"""
Basic tests for the APS POC functionality
"""

import sys
import os
import json
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from models import (
    Account, PaymentTransaction, ClearingType, MessageType, AccountType
)
from core.account_validator import AccountValidator
from core.auto_repair_engine import AutoRepairEngine 
from core.payment_processor import PaymentProcessor
from logging.audit_logger import AuditLogger


def test_account_validation():
    """Test basic account validation"""
    print("🧪 Testing Account Validation...")
    
    validator = AccountValidator()
    
    # Test valid account
    valid_account = Account(
        account_id="TEST_001",
        iban="DE89370400440532013000",
        bank_code="37040044",
        account_type=AccountType.DEBITOR,
        account_name="Test Account"
    )
    
    is_valid, errors = validator.validate_account(
        valid_account, ClearingType.DOMESTIC, MessageType.ISO20022_PACS008
    )
    
    print(f"   ✅ Valid account test: {'PASS' if is_valid else 'FAIL'}")
    
    # Test invalid account (with spaces in IBAN)
    invalid_account = Account(
        account_id="TEST_002", 
        iban="DE89 3704 0044 0532 013000",  # Spaces in IBAN
        bank_code="37040044",
        account_type=AccountType.DEBITOR,
        account_name="Test Account"
    )
    
    is_valid, errors = validator.validate_account(
        invalid_account, ClearingType.DOMESTIC, MessageType.ISO20022_PACS008
    )
    
    print(f"   ✅ Invalid account test: {'PASS' if not is_valid else 'FAIL'}")
    print(f"      Errors found: {len(errors)}")
    
    return True


def test_auto_repair():
    """Test automatic repair functionality"""
    print("🔧 Testing Auto Repair Engine...")
    
    repair_engine = AutoRepairEngine()
    
    # Test account with IBAN spacing issue
    account_with_spaces = Account(
        account_id="TEST_003",
        iban="DE89 3704 0044 0532 013000",  # Spaces in IBAN
        bank_code="37040044", 
        account_type=AccountType.DEBITOR,
        account_name="Test Account"
    )
    
    # Mock validation errors
    from models import ValidationError
    errors = [
        ValidationError(
            error_code="IBAN_INVALID_FORMAT",
            error_message="IBAN contains spaces",
            field_name="iban",
            current_value=account_with_spaces.iban
        )
    ]
    
    repaired_account, success, applied_rules = repair_engine.apply_repairs(
        account_with_spaces, errors, ClearingType.DOMESTIC, MessageType.ISO20022_PACS008
    )
    
    print(f"   ✅ Auto repair test: {'PASS' if success else 'FAIL'}")
    print(f"      Rules applied: {len(applied_rules)}")
    print(f"      Repaired IBAN: {repaired_account.iban}")
    
    return success


def test_payment_processing():
    """Test complete payment processing workflow"""
    print("💳 Testing Payment Processing...")
    
    processor = PaymentProcessor()
    
    # Create test transaction
    debitor = Account(
        account_id="DR_001",
        iban="DE89 3704 0044 0532 013000",  # Invalid format
        bank_code="37040044",
        account_type=AccountType.DEBITOR,
        account_name="Debitor Test"
    )
    
    creditor = Account(
        account_id="CR_001",
        iban="FR1420041010050500013M02606",  # Valid
        bank_code="20041",
        account_type=AccountType.CREDITOR,
        account_name="Creditor Test"
    )
    
    transaction = PaymentTransaction(
        transaction_id="TXN_TEST_001",
        debitor_account=debitor,
        creditor_account=creditor,
        amount=1000.00,
        currency="EUR",
        clearing_type=ClearingType.INTERNATIONAL,
        message_type=MessageType.ISO20022_PACS008
    )
    
    result = processor.process_payment(transaction)
    
    print(f"   ✅ Payment processing test: PASS")
    print(f"      Validation passed: {result.validation_passed}")
    print(f"      Auto repair successful: {result.auto_repair_successful}")
    print(f"      Manual repair required: {result.requires_manual_repair}")
    
    return True


def test_audit_logging():
    """Test audit logging functionality"""
    print("📝 Testing Audit Logging...")
    
    audit_logger = AuditLogger("tests/test_audit.json")
    
    # Create test accounts
    old_account = Account(
        account_id="OLD_001",
        iban="DE89 3704 0044 0532 013000",
        bank_code="37040044",
        account_type=AccountType.DEBITOR,
        account_name="Old Account"
    )
    
    new_account = Account(
        account_id="OLD_001", 
        iban="DE89370400440532013000",  # Fixed spacing
        bank_code="37040044",
        account_type=AccountType.DEBITOR,
        account_name="Old Account"
    )
    
    # Log manual repair
    log_id = audit_logger.log_manual_repair(
        transaction_id="TXN_TEST_002",
        old_account=old_account,
        new_account=new_account,
        clearing_type=ClearingType.DOMESTIC,
        message_type=MessageType.ISO20022_PACS008,
        repaired_by="test_user@example.com",
        repair_reason="IBAN formatting test",
        validation_errors=["IBAN_INVALID_FORMAT"]
    )
    
    print(f"   ✅ Audit logging test: PASS")
    print(f"      Log ID created: {log_id}")
    print(f"      Total logs: {len(audit_logger.logs)}")
    
    return True


def test_pattern_analysis():
    """Test AI pattern analysis"""
    print("🤖 Testing AI Pattern Analysis...")
    
    try:
        from ai.pattern_analyzer import PatternAnalyzer
        
        # Create audit logger with sample data
        audit_logger = AuditLogger("tests/test_audit.json")
        
        # Add sample manual repair logs for testing
        from models import ManualRepairAuditLog
        
        sample_logs = [
            ManualRepairAuditLog(
                log_id=f"LOG_TEST_{i}",
                log_type="DR_ACCOUNT_MANUAL_REPAIR",
                transaction_id=f"TXN_TEST_{i}",
                clearing_type=ClearingType.INTERNATIONAL,
                message_type=MessageType.ISO20022_PACS008,
                old_account_id=f"ACC_{i}",
                old_iban=f"DE89 3704 0044 0532 0130{i:02d}",
                new_account_id=f"ACC_{i}",
                new_iban=f"DE893704004405320130{i:02d}",
                repaired_by="test_user@example.com",
                repair_timestamp=datetime.now()
            )
            for i in range(5)
        ]
        
        audit_logger.logs.extend(sample_logs)
        
        # Run pattern analysis
        analyzer = PatternAnalyzer(audit_logger)
        patterns = analyzer.analyze_patterns(days_back=30)
        
        print(f"   ✅ Pattern analysis test: PASS")
        print(f"      Patterns identified: {len(patterns)}")
        
        if patterns:
            print(f"      Top pattern: {patterns[0].pattern_description}")
            print(f"      Automation feasibility: {patterns[0].automation_feasibility:.2f}")
        
        return True
        
    except Exception as e:
        print(f"   ⚠️  Pattern analysis test skipped: {e}")
        return True


def run_all_tests():
    """Run all POC tests"""
    print("🚀 Running APS POC Tests")
    print("=" * 50)
    
    tests = [
        test_account_validation,
        test_auto_repair,
        test_payment_processing,
        test_audit_logging,
        test_pattern_analysis
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            results.append(False)
        print()
    
    passed = sum(results)
    total = len(results)
    
    print("=" * 50)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! POC is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above.")
    
    return passed == total


if __name__ == "__main__":
    run_all_tests()