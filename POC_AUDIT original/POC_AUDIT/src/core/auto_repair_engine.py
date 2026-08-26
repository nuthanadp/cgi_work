"""
Auto repair engine for applying repair rules to fix account validation errors
"""

import re
from typing import List, Optional, Tuple, Dict, Any
from models import (
    Account, ValidationError, RepairRule, RuleCondition, RuleAction,
    ClearingType, MessageType, AccountType
)


class AutoRepairEngine:
    """Engine for applying automated repair rules to fix account validation errors"""
    
    def __init__(self):
        self.rules: List[RepairRule] = []
        self.lookup_tables: Dict[str, Dict[str, str]] = self._initialize_lookup_tables()
    
    def _initialize_lookup_tables(self) -> Dict[str, Dict[str, str]]:
        """Initialize lookup tables for common replacements"""
        return {
            'bank_code_mapping': {
                'BARC': 'BARCGB22',
                'HSBC': 'HBUKGB4B',
                'LLOY': 'LOYDGB21',
                'ABNA': 'ABNANL2A',
                'INGB': 'INGBNL2A',
                'RABO': 'RABONL2U'
            },
            'country_bank_codes': {
                'DE_12345678': '12345678',
                'DE_87654321': '87654321', 
                'FR_30004': '30004',
                'GB_BARC': 'BARC',
                'NL_ABNA': 'ABNA'
            },
            'iban_corrections': {
                'DE89 3704 0044 0532 0130 00': 'DE89370400440532013000',
                'FR14 2004 1010 0505 0001 3M02 606': 'FR1420041010050500013M02606'
            }
        }
    
    def add_rule(self, rule: RepairRule) -> None:
        """Add a new repair rule"""
        self.rules.append(rule)
        # Sort rules by priority (lower number = higher priority)
        self.rules.sort(key=lambda r: r.priority)
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove a repair rule"""
        original_count = len(self.rules)
        self.rules = [rule for rule in self.rules if rule.rule_id != rule_id]
        return len(self.rules) < original_count
    
    def apply_repairs(self, account: Account, errors: List[ValidationError],
                     clearing_type: ClearingType, message_type: MessageType) -> Tuple[Account, bool, List[str]]:
        """
        Apply repair rules to fix account validation errors
        
        Args:
            account: Account to repair
            errors: List of validation errors
            clearing_type: Clearing type context
            message_type: Message type context
            
        Returns:
            Tuple of (repaired_account, success, applied_rules)
        """
        repaired_account = account.copy(deep=True)
        applied_rules = []
        repair_success = False
        
        for rule in self.rules:
            if not rule.is_active:
                continue
                
            # Check if rule applies to this context
            if not self._rule_applies(rule, clearing_type, message_type, account.account_type):
                continue
            
            # Check if rule conditions are met
            if self._evaluate_conditions(rule.conditions, repaired_account, errors):
                # Apply rule actions
                if self._apply_rule_actions(rule.actions, repaired_account):
                    applied_rules.append(rule.rule_id)
                    rule.success_count += 1
                    repair_success = True
                else:
                    rule.failure_count += 1
        
        return repaired_account, repair_success, applied_rules
    
    def _rule_applies(self, rule: RepairRule, clearing_type: ClearingType,
                     message_type: MessageType, account_type: AccountType) -> bool:
        """Check if rule applies to the given context"""
        # Check clearing type match
        if rule.clearing_types and clearing_type not in rule.clearing_types:
            return False
        
        # Check message type match  
        if rule.message_types and message_type not in rule.message_types:
            return False
            
        # Check account type match
        if rule.account_types and account_type not in rule.account_types:
            return False
        
        return True
    
    def _evaluate_conditions(self, conditions: List[RuleCondition], account: Account,
                           errors: List[ValidationError]) -> bool:
        """Evaluate if all rule conditions are met"""
        for condition in conditions:
            if not self._evaluate_single_condition(condition, account, errors):
                return False
        return True
    
    def _evaluate_single_condition(self, condition: RuleCondition, account: Account,
                                 errors: List[ValidationError]) -> bool:
        """Evaluate a single condition"""
        # Get field value from account
        field_value = getattr(account, condition.field_name, None)
        
        # Handle error-based conditions
        if condition.field_name == "error_codes":
            error_codes = [error.error_code for error in errors]
            if condition.operator == "contains":
                return condition.value in error_codes
            elif condition.operator == "eq":
                return error_codes == condition.value
        
        # Handle regular field conditions
        if condition.operator == "eq":
            return field_value == condition.value
        elif condition.operator == "ne":
            return field_value != condition.value
        elif condition.operator == "contains":
            return condition.value in str(field_value) if field_value else False
        elif condition.operator == "regex":
            return bool(re.match(condition.value, str(field_value))) if field_value else False
        elif condition.operator == "empty":
            return not field_value or str(field_value).strip() == ""
        
        return False
    
    def _apply_rule_actions(self, actions: List[RuleAction], account: Account) -> bool:
        """Apply rule actions to modify the account"""
        try:
            for action in actions:
                if action.action_type == "replace":
                    setattr(account, action.target_field, action.action_value)
                elif action.action_type == "transform":
                    current_value = getattr(account, action.target_field, "")
                    new_value = self._apply_transformation(action.transformation, current_value)
                    setattr(account, action.target_field, new_value)
                elif action.action_type == "lookup":
                    current_value = getattr(account, action.target_field, "")
                    new_value = self._lookup_value(action.lookup_table, current_value)
                    if new_value:
                        setattr(account, action.target_field, new_value)
            return True
        except Exception:
            return False
    
    def _apply_transformation(self, transformation: str, value: str) -> str:
        """Apply transformation function to value"""
        if transformation == "remove_spaces":
            return value.replace(" ", "")
        elif transformation == "uppercase":
            return value.upper()
        elif transformation == "lowercase":
            return value.lower()  
        elif transformation == "add_country_prefix":
            # Add country prefix based on IBAN
            return value  # Simplified for POC
        elif transformation == "format_iban":
            # Remove spaces and format properly
            return value.replace(" ", "").upper()
        return value
    
    def _lookup_value(self, lookup_table_name: str, current_value: str) -> Optional[str]:
        """Look up replacement value in lookup table"""
        if lookup_table_name in self.lookup_tables:
            lookup_table = self.lookup_tables[lookup_table_name]
            return lookup_table.get(current_value)
        return None
    
    def get_applicable_rules(self, clearing_type: ClearingType, message_type: MessageType,
                           account_type: AccountType) -> List[RepairRule]:
        """Get list of rules that could apply to given context"""
        applicable_rules = []
        for rule in self.rules:
            if rule.is_active and self._rule_applies(rule, clearing_type, message_type, account_type):
                applicable_rules.append(rule)
        return applicable_rules
    
    def get_rule_statistics(self) -> Dict[str, Any]:
        """Get statistics about rule usage and effectiveness"""
        stats = {
            "total_rules": len(self.rules),
            "active_rules": len([r for r in self.rules if r.is_active]),
            "total_successes": sum(r.success_count for r in self.rules),
            "total_failures": sum(r.failure_count for r in self.rules),
            "rule_details": []
        }
        
        for rule in self.rules:
            total_attempts = rule.success_count + rule.failure_count
            success_rate = (rule.success_count / total_attempts * 100) if total_attempts > 0 else 0
            
            stats["rule_details"].append({
                "rule_id": rule.rule_id,
                "rule_name": rule.rule_name,
                "successes": rule.success_count,
                "failures": rule.failure_count,
                "success_rate": round(success_rate, 2),
                "is_active": rule.is_active
            })
        
        return stats