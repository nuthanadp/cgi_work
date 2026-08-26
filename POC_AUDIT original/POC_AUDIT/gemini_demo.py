"""
Gemini-Enhanced APS Demo
Demonstrates the POC with Google Gemini LLM integration for advanced pattern analysis and rule suggestions.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import json

# Setup environment
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from src.models.account import Account
from src.models.audit_log import AuditLog
from src.core.payment_processor import PaymentProcessor
from src.core.account_validator import AccountValidator
from src.core.auto_repair_engine import AutoRepairEngine
from src.auditing.audit_logger import AuditLogger
from src.ai.pattern_analyzer import PatternAnalyzer
from src.ai.rule_suggester import RuleSuggester
from src.ai.gemini_analyzer import GeminiPatternAnalyzer
from src.storage.database import Database
from config.settings import APSConfig


class GeminiEnhancedAPSDemo:
    """
    Demonstrates APS functionality enhanced with Google Gemini AI capabilities
    """
    
    def __init__(self):
        self.config = APSConfig()
        self.setup_components()
        logger.info("Gemini-Enhanced APS Demo initialized")
        
        if self.config.USE_GEMINI:
            logger.info(f"✅ Gemini AI enabled with model: {self.config.GEMINI_MODEL}")
        else:
            logger.warning("⚠️  Gemini API key not configured - using traditional ML only")
    
    def setup_components(self):
        """Initialize all APS components"""
        self.db = Database(self.config.DATABASE_PATH)
        self.audit_logger = AuditLogger(self.config.AUDIT_LOG_PATH)
        self.account_validator = AccountValidator()
        self.auto_repair_engine = AutoRepairEngine()
        self.payment_processor = PaymentProcessor(
            self.account_validator, 
            self.auto_repair_engine, 
            self.audit_logger
        )
        
        # AI components with Gemini enhancement
        self.pattern_analyzer = PatternAnalyzer(self.audit_logger)
        self.rule_suggester = RuleSuggester()
        self.gemini_analyzer = GeminiPatternAnalyzer()
    
    def run_complete_demo(self):
        """Run a complete demonstration of Gemini-enhanced APS capabilities"""
        print("\n" + "="*80)
        print("🚀 GEMINI-ENHANCED APS DEMONSTRATION")
        print("="*80)
        
        # Step 1: Process payments and generate manual repair logs
        print("\n📊 Step 1: Processing Payments and Generating Manual Repair Data...")
        self.simulate_payment_processing()
        
        # Step 2: Traditional ML Pattern Analysis
        print("\n🔍 Step 2: Traditional ML Pattern Analysis...")
        traditional_analysis = self.demonstrate_traditional_analysis()
        
        # Step 3: Gemini-Enhanced Analysis
        print("\n🤖 Step 3: Gemini LLM Enhanced Analysis...")
        gemini_analysis = self.demonstrate_gemini_analysis()
        
        # Step 4: Combined Insights and Rule Generation
        print("\n⚡ Step 4: Combined Insights and Intelligent Rule Suggestions...")
        self.demonstrate_combined_analysis(traditional_analysis, gemini_analysis)
        
        # Step 5: AI-Generated Rule Validation
        print("\n✅ Step 5: AI-Generated Rule Validation...")
        self.demonstrate_rule_validation()
        
        print("\n🎉 Demo completed successfully!")
        print("="*80)
    
    def simulate_payment_processing(self):
        """Simulate payment processing with manual repair scenarios"""
        # Create test accounts with various issues
        test_accounts = self.create_test_accounts_with_issues()
        
        processed_count = 0
        manual_repairs = 0
        
        for account_data in test_accounts:
            try:
                # Process payment
                account = Account(**account_data)
                result = self.payment_processor.process_payment(account, amount=1000.0)
                processed_count += 1
                
                # Simulate manual repair if automatic repair failed
                if not result["success"] and not result.get("auto_repaired", False):
                    self.simulate_manual_repair(account_data, result)
                    manual_repairs += 1
                    
            except Exception as e:
                logger.error(f"Error processing payment: {e}")
        
        print(f"📈 Processed {processed_count} payments")
        print(f"🔧 Generated {manual_repairs} manual repair cases")
    
    def create_test_accounts_with_issues(self) -> list:
        """Create test accounts that will trigger various repair scenarios"""
        return [
            # IBAN spacing issues
            {"account_id": "ACC001", "iban": "DE89 3704 0044 0532 0130 00", "account_type": "CHECKING"},
            {"account_id": "ACC002", "iban": "FR14 2004 1010 0505 0001 3M02 606", "account_type": "SAVINGS"},
            {"account_id": "ACC003", "iban": "GB29 NWBK 6016 1331 9268 19", "account_type": "CHECKING"},
            
            # IBAN length issues  
            {"account_id": "ACC004", "iban": "DE8937040044053201300", "account_type": "CHECKING"},
            {"account_id": "ACC005", "iban": "FR142004101005050001", "account_type": "SAVINGS"},
            
            # IBAN content issues
            {"account_id": "ACC006", "iban": "DE99370400440532013000", "account_type": "CHECKING"},
            {"account_id": "ACC007", "iban": "FR142004101005050001ZZ0606", "account_type": "SAVINGS"},
            
            # Country code issues
            {"account_id": "ACC008", "iban": "XX89370400440532013000", "account_type": "CHECKING"},
            {"account_id": "ACC009", "iban": "YY142004101005050001M02606", "account_type": "SAVINGS"},
            
            # Account ID issues
            {"account_id": "", "iban": "DE89370400440532013000", "account_type": "CHECKING"},
            {"account_id": "ACC011", "iban": "FR1420041010050500013M02606", "account_type": "INVALID_TYPE"},
        ]
    
    def simulate_manual_repair(self, original_account: Dict, validation_result: Dict):
        """Simulate manual repair of failed account validation"""
        repair_scenarios = {
            "iban_spacing": lambda iban: iban.replace(" ", ""),
            "iban_length": lambda iban: iban[:22] if len(iban) > 22 else iban,
            "iban_content": lambda iban: iban.replace("99", "89").replace("ZZ", "M0"),
            "country_code": lambda iban: "DE" + iban[2:] if iban.startswith("XX") else "FR" + iban[2:],
            "account_id": lambda aid: "AUTO_GENERATED_ID" if not aid else aid
        }
        
        # Determine repair type based on validation errors
        errors = validation_result.get("validation_errors", [])
        
        old_iban = original_account["iban"]
        old_account_id = original_account["account_id"]
        
        # Apply appropriate repair
        new_iban = old_iban
        new_account_id = old_account_id
        
        if "IBAN_CONTAINS_SPACES" in errors:
            new_iban = repair_scenarios["iban_spacing"](old_iban)
        elif "IBAN_INVALID_LENGTH" in errors:
            new_iban = repair_scenarios["iban_length"](old_iban)
        elif "IBAN_INVALID_FORMAT" in errors:
            new_iban = repair_scenarios["iban_content"](old_iban)
        elif "IBAN_UNSUPPORTED_COUNTRY" in errors:
            new_iban = repair_scenarios["country_code"](old_iban)
        elif "ACCOUNT_ID_MISSING" in errors:
            new_account_id = repair_scenarios["account_id"](old_account_id)
        
        # Log manual repair
        log_type = "DR_ACCOUNT_MANUAL_REPAIR" if "account" in str(errors).lower() else "CR_ACCOUNT_MANUAL_REPAIR"
        
        self.audit_logger.log_manual_repair(
            log_type=log_type,
            clearing_type="SEPA",
            message_type="PAIN001",
            old_account_id=old_account_id,
            old_iban=old_iban,
            new_account_id=new_account_id,
            new_iban=new_iban,
            repaired_by="demo_user",
            validation_errors=errors
        )
    
    def demonstrate_traditional_analysis(self) -> Dict[str, Any]:
        """Demonstrate traditional ML pattern analysis"""
        print("🔬 Running Traditional ML Analysis...")
        
        try:
            # Get audit logs from the last 30 days
            analysis_result = self.pattern_analyzer.analyze_patterns(days_back=30)
            
            if analysis_result["status"] == "success":
                traditional_patterns = analysis_result.get("traditional_patterns", [])
                
                print(f"📊 Found {len(traditional_patterns)} patterns using traditional ML")
                
                for i, pattern in enumerate(traditional_patterns[:3]):  # Show top 3
                    print(f"  Pattern {i+1}: {pattern.pattern_type}")
                    print(f"    Frequency: {pattern.occurrence_count}")
                    print(f"    Automation Score: {pattern.automation_feasibility:.2f}")
                    print(f"    Risk Level: {getattr(pattern, 'risk_level', 'UNKNOWN')}")
            else:
                print(f"⚠️  Analysis status: {analysis_result['status']}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Traditional analysis failed: {e}")
            return {"status": "error", "traditional_patterns": []}
    
    def demonstrate_gemini_analysis(self) -> Dict[str, Any]:
        """Demonstrate Gemini LLM enhanced analysis"""
        print("🧠 Running Gemini LLM Analysis...")
        
        if not self.config.USE_GEMINI:
            print("⚠️  Gemini not configured - skipping LLM analysis")
            return {"status": "gemini_unavailable"}
        
        try:
            # Get recent repair logs
            recent_logs = self.audit_logger.get_recent_logs(days=30)
            
            if not recent_logs:
                print("📭 No recent logs available for Gemini analysis")
                return {"status": "no_data"}
            
            # Convert to Gemini format
            log_dicts = [self._log_to_dict(log) for log in recent_logs]
            
            # Run Gemini analysis
            gemini_result = self.gemini_analyzer.analyze_manual_repairs(log_dicts)
            
            print(f"🤖 Gemini Analysis Results:")
            print(f"   Identified Patterns: {len(gemini_result.patterns)}")
            print(f"   Suggested Rules: {len(gemini_result.suggested_rules)}")
            print(f"   Confidence Score: {gemini_result.confidence_score:.2f}")
            print(f"   Automation Opportunities: {len(gemini_result.automation_opportunities)}")
            
            # Show key insights
            for i, pattern in enumerate(gemini_result.patterns[:2]):
                print(f"   🔍 Pattern {i+1}: {pattern.get('pattern_type', 'Unknown')}")
                print(f"      Description: {pattern.get('description', 'N/A')}")
                print(f"      Feasibility: {pattern.get('automation_feasibility', 'Unknown')}")
            
            return {"status": "success", "gemini_result": gemini_result}
            
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def demonstrate_combined_analysis(self, traditional_result: Dict, gemini_result: Dict):
        """Demonstrate combined traditional + Gemini analysis"""
        print("🔀 Combining Traditional ML + Gemini Insights...")
        
        try:
            # Get patterns from both analyses
            traditional_patterns = traditional_result.get("traditional_patterns", [])
            gemini_data = gemini_result.get("gemini_result")
            
            if traditional_patterns and gemini_data:
                # Generate combined rule suggestions
                rule_suggestions = self.rule_suggester.suggest_rules_from_patterns(traditional_patterns)
                
                print(f"⚡ Combined Analysis Results:")
                print(f"   Traditional Rules: {len(rule_suggestions.get('traditional_rules', []))}")
                print(f"   Gemini-Enhanced Rules: {len(rule_suggestions.get('gemini_rules', []))}")
                print(f"   Total Recommendations: {len(rule_suggestions.get('combined_recommendations', []))}")
                
                # Show top recommendations
                top_recommendations = rule_suggestions.get('combined_recommendations', [])[:3]
                for i, rec in enumerate(top_recommendations):
                    print(f"   🏆 Recommendation {i+1}:")
                    print(f"      Rule: {rec['rule_name']}")
                    print(f"      Source: {rec['source']}")
                    print(f"      Confidence: {rec.get('confidence_score', 0):.2f}")
                    print(f"      Overall Score: {rec.get('overall_score', 0):.1f}")
            
            else:
                print("⚠️  Insufficient data for combined analysis")
                
        except Exception as e:
            logger.error(f"Combined analysis failed: {e}")
    
    def demonstrate_rule_validation(self):
        """Demonstrate validation of AI-generated rules"""
        print("🧪 Validating AI-Generated Rules...")
        
        try:
            # Get recent patterns
            analysis_result = self.pattern_analyzer.analyze_patterns(days_back=30)
            
            if analysis_result["status"] == "success":
                traditional_patterns = analysis_result.get("traditional_patterns", [])
                
                if traditional_patterns:
                    # Generate rule suggestions
                    rule_suggestions = self.rule_suggester.suggest_rules_from_patterns(traditional_patterns)
                    combined_rules = rule_suggestions.get('combined_recommendations', [])
                    
                    validated_rules = []
                    for rule_data in combined_rules[:3]:  # Validate top 3 rules
                        validation_result = self._validate_rule_safety(rule_data)
                        validated_rules.append(validation_result)
                    
                    # Summary
                    safe_rules = [r for r in validated_rules if r["is_safe"]]
                    print(f"✅ Validated {len(validated_rules)} rules")
                    print(f"   Safe for automation: {len(safe_rules)}")
                    print(f"   Require review: {len(validated_rules) - len(safe_rules)}")
                    
                    for rule in safe_rules:
                        print(f"   ✅ SAFE: {rule['rule_name']} (Risk: {rule['risk_level']})")
                
        except Exception as e:
            logger.error(f"Rule validation failed: {e}")
    
    def _log_to_dict(self, log) -> Dict[str, Any]:
        """Convert audit log to dictionary for Gemini"""
        if hasattr(log, '__dict__'):
            return {
                "log_type": getattr(log, 'log_type', ''),
                "clearing_type": getattr(log, 'clearing_type', ''),
                "message_type": getattr(log, 'message_type', ''),
                "old_account_id": getattr(log, 'old_account_id', ''),
                "old_iban": getattr(log, 'old_iban', ''),
                "new_account_id": getattr(log, 'new_account_id', ''),
                "new_iban": getattr(log, 'new_iban', ''),
                "repaired_by": getattr(log, 'repaired_by', ''),
                "validation_errors": getattr(log, 'validation_errors', [])
            }
        else:
            return log if isinstance(log, dict) else {}
    
    def _validate_rule_safety(self, rule_data: Dict) -> Dict[str, Any]:
        """Validate if a generated rule is safe for automation"""
        rule_name = rule_data.get("rule_name", "Unknown")
        source = rule_data.get("source", "unknown")
        confidence = rule_data.get("confidence_score", 0)
        
        # Risk assessment criteria
        is_safe = True
        risk_level = "LOW"
        concerns = []
        
        # Check for high-risk operations
        if "country" in rule_name.lower() or "account_id" in rule_name.lower():
            risk_level = "HIGH"
            is_safe = False
            concerns.append("Modifies critical account data")
        
        # Check confidence level
        if confidence < 0.7:
            risk_level = "MEDIUM"
            concerns.append("Low confidence score")
        
        # Source-based assessment
        if source == "gemini" and risk_level == "LOW":
            # Gemini rules need additional validation
            concerns.append("LLM-generated rule requires human review")
        
        # Final safety determination
        if concerns:
            is_safe = len(concerns) <= 1 and risk_level != "HIGH"
        
        return {
            "rule_name": rule_name,
            "source": source,
            "confidence": confidence,
            "is_safe": is_safe,
            "risk_level": risk_level,
            "concerns": concerns
        }


def main():
    """Main demonstration function"""
    print("🤖 Starting Gemini-Enhanced APS Demo...")
    
    try:
        demo = GeminiEnhancedAPSDemo()
        demo.run_complete_demo()
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")


if __name__ == "__main__":
    main()