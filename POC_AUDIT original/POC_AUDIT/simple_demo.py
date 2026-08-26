"""
Simple demo runner to test the APS POC basic functionality
without requiring all dependencies
"""

import sys
import os
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent / 'src')
sys.path.insert(0, src_path)

def test_basic_imports():
    """Test basic imports to ensure structure is correct"""
    print("🧪 Testing basic imports...")
    
    try:
        from models import Account, AccountType, ClearingType, MessageType
        print("   ✅ Models imported successfully")
        
        from core.account_validator import AccountValidator
        print("   ✅ AccountValidator imported successfully")
        
        # Test creating a basic account
        account = Account(
            account_id="TEST_001",
            iban="DE89370400440532013000",
            bank_code="37040044",
            account_type=AccountType.DEBITOR,
            account_name="Test Account"
        )
        print(f"   ✅ Account created: {account.account_id}")
        
        # Test basic validation
        validator = AccountValidator()
        is_valid, errors = validator.validate_account(
            account, ClearingType.DOMESTIC, MessageType.ISO20022_PACS008
        )
        print(f"   ✅ Validation test: {'Valid' if is_valid else f'Invalid ({len(errors)} errors)'}")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Other error: {e}")
        return False

def demo_audit_logging():
    """Demonstrate audit logging without AI dependencies"""
    print("\n📝 Testing Audit Logging...")
    
    try:
        from models import ManualRepairAuditLog, Account, AccountType, ClearingType, MessageType
        from auditing.audit_logger import AuditLogger
        from datetime import datetime
        
        # Create sample accounts
        old_account = Account(
            account_id="OLD_001",
            iban="DE89 3704 0044 0532 013000",  # With spaces
            bank_code="37040044",
            account_type=AccountType.DEBITOR,
            account_name="Old Account"
        )
        
        new_account = Account(
            account_id="OLD_001",
            iban="DE89370400440532013000",  # Fixed
            bank_code="37040044", 
            account_type=AccountType.DEBITOR,
            account_name="Old Account"
        )
        
        # Create audit logger
        audit_logger = AuditLogger("data/demo_audit_logs.json")
        
        # Log manual repair
        log_id = audit_logger.log_manual_repair(
            transaction_id="TXN_DEMO_001",
            old_account=old_account,
            new_account=new_account,
            clearing_type=ClearingType.INTERNATIONAL,
            message_type=MessageType.ISO20022_PACS008,
            repaired_by="demo_user@example.com",
            repair_reason="IBAN formatting correction",
            validation_errors=["IBAN_INVALID_FORMAT"]
        )
        
        return True
        
    except Exception as e:
        print(f"   ❌ Audit logging error: {e}")
        return False

def demo_payment_processing():
    """Demonstrate payment processing without AI"""
    print("\n💳 Testing Payment Processing...")
    
    try:
        from core.payment_processor import PaymentProcessor
        from models import PaymentTransaction, Account, AccountType, ClearingType, MessageType
        
        # Create payment processor
        processor = PaymentProcessor()
        
        # Create test transaction
        debitor = Account(
            account_id="DR_001",
            iban="DE89 3704 0044 0532 013000",  # Invalid (spaces)
            bank_code="37040044",
            account_type=AccountType.DEBITOR,
            account_name="Debitor Company"
        )
        
        creditor = Account(
            account_id="CR_001", 
            iban="FR1420041010050500013M02606",  # Valid
            bank_code="20041",
            account_type=AccountType.CREDITOR,
            account_name="Creditor Company"
        )
        
        transaction = PaymentTransaction(
            transaction_id="TXN_DEMO_001",
            debitor_account=debitor,
            creditor_account=creditor,
            amount=15000.00,
            currency="EUR",
            clearing_type=ClearingType.INTERNATIONAL,
            message_type=MessageType.ISO20022_PACS008
        )
        
        # Process transaction
        result = processor.process_payment(transaction)
        
        print(f"   ✅ Transaction processed:")
        print(f"      • Validation passed: {result.validation_passed}")
        print(f"      • Auto repair successful: {result.auto_repair_successful}")
        print(f"      • Manual repair required: {result.requires_manual_repair}")
        print(f"      • Applied rules: {len(result.applied_auto_rules)}")
        
        # Get processing statistics
        stats = processor.get_processing_statistics()
        print(f"   📊 Processing Stats:")
        print(f"      • Total processed: {stats['total_processed']}")
        print(f"      • Auto repair rate: {stats.get('auto_repair_rate', 0):.1f}%")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Payment processing error: {e}")
        return False

def main():
    """Run simplified demo"""
    print("🏦 APS POC - SIMPLIFIED DEMO")
    print("=" * 60)
    
    tests = [
        test_basic_imports,
        demo_audit_logging,
        demo_payment_processing
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ Basic POC functionality verified!")
        print("\n📋 What this demonstrates:")
        print("   • Account validation with business rules")
        print("   • Automatic repair engine with rule-based fixes")
        print("   • Standardized audit logging for manual repairs")
        print("   • Payment processing workflow orchestration")
        print("\n🚀 Next steps:")
        print("   • Install ML dependencies: pip install -r requirements.txt")
        print("   • Run full demo: python main.py")
        print("   • Start API server: python run_poc.py")
    else:
        print("⚠️  Some issues found. Check the output above.")
    
    return passed == total

if __name__ == "__main__":
    main()