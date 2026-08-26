"""
Payment processor that orchestrates the complete payment validation and repair flow
"""

from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import uuid

from models import (
    PaymentTransaction, Account, ValidationError, AccountType,
    ClearingType, MessageType
)
from core.account_validator import AccountValidator
from core.auto_repair_engine import AutoRepairEngine


class PaymentProcessingResult:
    """Result of payment processing"""
    def __init__(self, transaction: PaymentTransaction):
        self.transaction = transaction
        self.validation_passed = False
        self.auto_repair_successful = False
        self.requires_manual_repair = False
        self.debitor_errors = []
        self.creditor_errors = []
        self.applied_auto_rules = []
        self.processing_time = datetime.now()
    

class PaymentProcessor:
    """Main payment processor that coordinates validation and repair"""
    
    def __init__(self):
        self.validator = AccountValidator()
        self.repair_engine = AutoRepairEngine()
        self.processing_stats = {
            "total_processed": 0,
            "validation_passed": 0,
            "auto_repair_successful": 0,
            "manual_repair_required": 0,
            "processing_failed": 0
        }
        
        # Initialize with some default repair rules
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize some basic repair rules for demonstration"""
        from ..models import RepairRule, RuleCondition, RuleAction
        
        # Rule 1: Fix IBAN spacing issues
        iban_spacing_rule = RepairRule(
            rule_id="IBAN_REMOVE_SPACES",
            rule_name="Remove IBAN Spaces",
            description="Remove spaces from IBAN formatting",
            conditions=[
                RuleCondition(field_name="iban", operator="contains", value=" "),
                RuleCondition(field_name="error_codes", operator="contains", value="IBAN_INVALID_FORMAT")
            ],
            actions=[
                RuleAction(action_type="transform", target_field="iban", transformation="remove_spaces")
            ],
            priority=10,
            created_by="SYSTEM"
        )
        
        # Rule 2: Fix bank code mapping for UK
        uk_bank_code_rule = RepairRule(
            rule_id="UK_BANK_CODE_MAPPING",
            rule_name="UK Bank Code Mapping",
            description="Map short UK bank codes to full codes",
            clearing_types=[ClearingType.INTERNATIONAL],
            conditions=[
                RuleCondition(field_name="iban", operator="regex", value="^GB.*"),
                RuleCondition(field_name="error_codes", operator="contains", value="BANK_CODE_INVALID")
            ],
            actions=[
                RuleAction(action_type="lookup", target_field="bank_code", lookup_table="bank_code_mapping")
            ],
            priority=20,
            created_by="SYSTEM"
        )
        
        # Rule 3: Fix German bank code format
        de_bank_code_rule = RepairRule(
            rule_id="DE_BANK_CODE_FORMAT",
            rule_name="German Bank Code Format",
            description="Ensure German bank codes are numeric",
            conditions=[
                RuleCondition(field_name="iban", operator="regex", value="^DE.*"),
                RuleCondition(field_name="error_codes", operator="contains", value="CROSS_FIELD_COUNTRY_MISMATCH")
            ],
            actions=[
                RuleAction(action_type="lookup", target_field="bank_code", lookup_table="country_bank_codes")
            ],
            priority=30,
            created_by="SYSTEM"
        )
        
        self.repair_engine.add_rule(iban_spacing_rule)
        self.repair_engine.add_rule(uk_bank_code_rule)
        self.repair_engine.add_rule(de_bank_code_rule)
    
    def process_payment(self, transaction: PaymentTransaction) -> PaymentProcessingResult:
        """
        Process a payment transaction with validation and repair
        
        Args:
            transaction: Payment transaction to process
            
        Returns:
            PaymentProcessingResult with processing outcome
        """
        result = PaymentProcessingResult(transaction)
        
        try:
            # Step 1: Validate both accounts
            dr_valid, dr_errors = self.validator.validate_account(
                transaction.debitor_account,
                transaction.clearing_type,
                transaction.message_type
            )
            
            cr_valid, cr_errors = self.validator.validate_account(
                transaction.creditor_account,
                transaction.clearing_type,
                transaction.message_type
            )
            
            result.debitor_errors = dr_errors
            result.creditor_errors = cr_errors
            
            # If both accounts are valid, we're done
            if dr_valid and cr_valid:
                result.validation_passed = True
                transaction.validation_status = "PASSED"
                self.processing_stats["validation_passed"] += 1
                return result
            
            # Step 2: Attempt auto-repair
            auto_repair_successful = True
            
            if not dr_valid:
                repaired_dr, dr_success, dr_rules = self.repair_engine.apply_repairs(
                    transaction.debitor_account,
                    dr_errors,
                    transaction.clearing_type,
                    transaction.message_type
                )
                if dr_success:
                    # Re-validate repaired account
                    dr_valid_after_repair, _ = self.validator.validate_account(
                        repaired_dr,
                        transaction.clearing_type,
                        transaction.message_type
                    )
                    if dr_valid_after_repair:
                        transaction.debitor_account = repaired_dr
                        result.applied_auto_rules.extend(dr_rules)
                    else:
                        auto_repair_successful = False
                else:
                    auto_repair_successful = False
            
            if not cr_valid:
                repaired_cr, cr_success, cr_rules = self.repair_engine.apply_repairs(
                    transaction.creditor_account,
                    cr_errors,
                    transaction.clearing_type,
                    transaction.message_type
                )
                if cr_success:
                    # Re-validate repaired account
                    cr_valid_after_repair, _ = self.validator.validate_account(
                        repaired_cr,
                        transaction.clearing_type,
                        transaction.message_type
                    )
                    if cr_valid_after_repair:
                        transaction.creditor_account = repaired_cr
                        result.applied_auto_rules.extend(cr_rules)
                    else:
                        auto_repair_successful = False
                else:
                    auto_repair_successful = False
            
            transaction.repair_attempts += 1
            
            # Step 3: Determine final status
            if auto_repair_successful:
                result.auto_repair_successful = True
                transaction.validation_status = "AUTO_REPAIRED"
                self.processing_stats["auto_repair_successful"] += 1
            else:
                result.requires_manual_repair = True
                transaction.validation_status = "MANUAL_REPAIR_REQUIRED"
                self.processing_stats["manual_repair_required"] += 1
            
        except Exception as e:
            result.transaction.validation_status = "PROCESSING_FAILED"
            self.processing_stats["processing_failed"] += 1
            
        finally:
            self.processing_stats["total_processed"] += 1
        
        return result
    
    def batch_process_payments(self, transactions: List[PaymentTransaction]) -> List[PaymentProcessingResult]:
        """Process multiple payment transactions"""
        results = []
        for transaction in transactions:
            result = self.process_payment(transaction)
            results.append(result)
        return results
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        stats = self.processing_stats.copy()
        
        # Calculate percentages
        total = stats["total_processed"]
        if total > 0:
            stats["validation_pass_rate"] = round(stats["validation_passed"] / total * 100, 2)
            stats["auto_repair_rate"] = round(stats["auto_repair_successful"] / total * 100, 2)
            stats["manual_repair_rate"] = round(stats["manual_repair_required"] / total * 100, 2)
            stats["failure_rate"] = round(stats["processing_failed"] / total * 100, 2)
        
        # Add repair engine stats
        stats["repair_engine_stats"] = self.repair_engine.get_rule_statistics()
        
        return stats
    
    def get_transactions_requiring_manual_repair(self) -> List[Dict[str, Any]]:
        """Get summary of transactions that require manual repair"""
        # In a real system, this would query a database
        # For POC, returning sample data structure
        return [
            {
                "transaction_id": "TXN_001",
                "clearing_type": "INTERNATIONAL",
                "message_type": "MT103",
                "debitor_errors": ["IBAN_INVALID_FORMAT"],
                "creditor_errors": ["BANK_CODE_INVALID"],
                "failed_auto_rules": ["UK_BANK_CODE_MAPPING"],
                "processing_time": datetime.now()
            }
        ]
    
    def add_repair_rule(self, rule_dict: Dict[str, Any]) -> str:
        """Add a new repair rule from dictionary"""
        from ..models import RepairRule
        
        rule = RepairRule(**rule_dict)
        self.repair_engine.add_rule(rule)
        return rule.rule_id
    
    def get_suggested_fixes(self, transaction: PaymentTransaction) -> Dict[str, List[str]]:
        """Get suggested manual fixes for a transaction"""
        suggestions = {
            "debitor": [],
            "creditor": []
        }
        
        # Get validation errors for both accounts
        dr_valid, dr_errors = self.validator.validate_account(
            transaction.debitor_account,
            transaction.clearing_type,
            transaction.message_type
        )
        
        cr_valid, cr_errors = self.validator.validate_account(
            transaction.creditor_account,
            transaction.clearing_type,
            transaction.message_type
        )
        
        # Get suggestions for fixes
        if not dr_valid:
            suggestions["debitor"] = self.validator.get_suggested_fixes(
                dr_errors, transaction.debitor_account
            )
        
        if not cr_valid:
            suggestions["creditor"] = self.validator.get_suggested_fixes(
                cr_errors, transaction.creditor_account
            )
        
        return suggestions