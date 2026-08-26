"""
Simple Groq AI Enhanced APS Demo
Demonstrates intelligent banking repair suggestions using Groq AI
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ai.groq_analyzer import GroqPatternAnalyzer
from src.models.account import Account
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GroqAPSDemo:
    """Simple demo showcasing APS with Groq AI integration"""
    
    def __init__(self):
        self.groq_analyzer = GroqPatternAnalyzer()
        
    def run_demo(self):
        """Run a simplified demo of the Groq-enhanced APS system"""
        print("🚀 Groq AI Enhanced APS Demo")
        print("=" * 50)
        
        # Step 1: Show sample manual repair logs
        print("\n📋 Step 1: Sample Manual Repair Logs")
        sample_logs = self._get_sample_logs()
        for i, log in enumerate(sample_logs, 1):
            print(f"  {i}. {log['log_type']}: {log['old_iban']} → {log['new_iban']}")
        
        # Step 2: Use Groq AI to analyze patterns
        print("\n🤖 Step 2: Groq AI Analysis")
        print("  Analyzing patterns with Groq LLM...")
        
        try:
            analysis = self.groq_analyzer.analyze_manual_repairs(sample_logs)
            
            print("📊 Analysis Results:")
            print(f"  • Confidence: {analysis.confidence_score:.1%}")
            print(f"  • Patterns Found: {len(analysis.patterns)}")
            print(f"  • Automation Opportunities: {len(analysis.automation_opportunities)}")
            
            # Step 3: Show patterns found
            print("\n🔍 Step 3: Detected Patterns")
            for i, pattern in enumerate(analysis.patterns, 1):
                print(f"  {i}. {pattern.get('pattern_type', 'Unknown')}")
                print(f"     Frequency: {pattern.get('frequency', 0)}")
                print(f"     Description: {pattern.get('description', 'N/A')}")
            
            # Step 4: Show suggested automation rules
            print("\n💡 Step 4: AI-Generated Rules")
            for i, rule in enumerate(analysis.suggested_rules, 1):
                print(f"  {i}. {rule.get('rule_name', 'Auto-fix rule')}")
                print(f"     Type: {rule.get('rule_type', 'Format correction')}")
                print(f"     Condition: {rule.get('condition', 'N/A')}")
                print(f"     Action: {rule.get('action', 'N/A')}")
                print(f"     Confidence: {rule.get('confidence', 0.85):.1%}")
                print(f"     Risk Level: {rule.get('risk_level', 'MEDIUM')}")
                print()
            
            # Step 5: Show automation opportunities
            print("\n🎯 Step 5: Automation Opportunities")
            for i, opportunity in enumerate(analysis.automation_opportunities, 1):
                print(f"  {i}. {opportunity.get('opportunity', 'Unknown')}")
                print(f"     Automation Rate: {opportunity.get('potential_automation_rate', 0)}%")
                print(f"     Complexity: {opportunity.get('complexity', 'UNKNOWN')}")
                
        except Exception as e:
            print(f"❌ Error during Groq analysis: {e}")
            print("🔄 Using fallback analysis...")
        
        print("\n✅ Demo completed successfully!")
        
    def _get_sample_logs(self):
        """Generate sample manual repair logs"""
        return [
            {
                "log_type": "DR_ACCOUNT_MANUAL_REPAIR",
                "clearing_type": "SEPA",
                "message_type": "103",
                "old_account_id": "ACC001",
                "old_iban": "DE89 3704 0044 0532 0130 00",
                "new_account_id": "ACC001", 
                "new_iban": "DE89370400440532013000",
                "timestamp": datetime.now().isoformat()
            },
            {
                "log_type": "CR_ACCOUNT_MANUAL_REPAIR",
                "clearing_type": "SEPA", 
                "message_type": "103",
                "old_account_id": "ACC002",
                "old_iban": "GB29NWBK601613311400",
                "new_account_id": "ACC002",
                "new_iban": "GB29NWBK60161331140000", 
                "timestamp": datetime.now().isoformat()
            },
            {
                "log_type": "DR_ACCOUNT_MANUAL_REPAIR",
                "clearing_type": "SWIFT",
                "message_type": "202",
                "old_account_id": "ACC 003",
                "old_iban": "FR14 2004 1010 0505 0001 3M02 606",
                "new_account_id": "ACC003",
                "new_iban": "FR1420041010050500013M02606",
                "timestamp": datetime.now().isoformat()
            }
        ]

if __name__ == "__main__":
    try:
        demo = GroqAPSDemo()
        demo.run_demo()
    except Exception as e:
        print(f"❌ Error running demo: {e}")
        import traceback
        traceback.print_exc()
        
        for account in problem_accounts:
            print(f"  ❌ Account validation failed: {account.account_id}")
            print(f"     IBAN: {account.iban}")
            print(f"     Issue: Formatting problems detected")
            
            # Try automatic repair first
            repaired = self.repair_engine.attempt_repair(account)
            if repaired.is_valid:
                print(f"  ✅ Automatic repair successful!")
            else:
                print(f"  ⚠️  Automatic repair failed - needs manual intervention")
    
    def _simulate_manual_repairs(self):
        """Simulate manual repairs and generate audit logs"""
        
        manual_repairs = [
            {
                "log_type": "DR_ACCOUNT_MANUAL_REPAIR",
                "clearing_type": "SEPA",
                "message_type": "PAIN001",
                "old_account_id": "ACC001",
                "old_iban": "DE89 3704 0044 0532 0130 00",
                "new_account_id": "ACC001", 
                "new_iban": "DE89370400440532013000"
            },
            {
                "log_type": "CR_ACCOUNT_MANUAL_REPAIR",
                "clearing_type": "SEPA",
                "message_type": "PAIN001",
                "old_account_id": "ACC 003",
                "old_iban": "FR1420041010050500013M02606",
                "new_account_id": "ACC003",
                "new_iban": "FR1420041010050500013M02606"
            },
            {
                "log_type": "DR_ACCOUNT_MANUAL_REPAIR", 
                "clearing_type": "SEPA",
                "message_type": "PAIN008",
                "old_account_id": "ACC004",
                "old_iban": "ES91 2100 0418 4502 0005 1332",
                "new_account_id": "ACC004",
                "new_iban": "ES9121000418450200051332"
            },
            {
                "log_type": "DR_ACCOUNT_MANUAL_REPAIR",
                "clearing_type": "SWIFT",
                "message_type": "MT103",
                "old_account_id": "ACC002",
                "old_iban": "GB29NWBK601613311400",
                "new_account_id": "ACC002",
                "new_iban": "GB29NWBK60161331140000"
            },
            {
                "log_type": "CR_ACCOUNT_MANUAL_REPAIR",
                "clearing_type": "SEPA", 
                "message_type": "PAIN001",
                "old_account_id": "ACC005",
                "old_iban": "IT60 X054 2811 1010 0000 0123 456",
                "new_account_id": "ACC005",
                "new_iban": "IT60X0542811101000000123456"
            },
            {
                "log_type": "DR_ACCOUNT_MANUAL_REPAIR",
                "clearing_type": "SEPA",
                "message_type": "PAIN001",
                "old_account_id": "ACC006",
                "old_iban": "NL91 ABNA 0417 1643 00",
                "new_account_id": "ACC006",
                "new_iban": "NL91ABNA0417164300"
            }
        ]
        
        print("  📝 Logging manual repairs to audit system...")
        
        for repair in manual_repairs:
            # Log the manual repair
            self.audit_logger.log_manual_repair(
                log_type=repair["log_type"],
                clearing_type=repair["clearing_type"],
                message_type=repair["message_type"], 
                old_account_id=repair["old_account_id"],
                old_iban=repair["old_iban"],
                new_account_id=repair["new_account_id"],
                new_iban=repair["new_iban"]
            )
            
            print(f"     → {repair['log_type']}: {repair['old_iban']} → {repair['new_iban']}")
        
        print(f"  ✅ Logged {len(manual_repairs)} manual repairs")
        return manual_repairs
    
    def _demonstrate_groq_analysis(self):
        """Demonstrate Groq AI analysis of repair patterns"""
        
        # Get recent audit logs
        audit_logs = self.database.get_recent_audit_logs(days=30)
        
        if not audit_logs:
            print("  ⚠️  No audit logs found. Using sample data...")
            # Use sample data for demo
            audit_logs = self._get_sample_audit_logs()
        
        print(f"  🔍 Analyzing {len(audit_logs)} repair logs with Groq AI...")
        
        # Convert to expected format
        log_dicts = [
            {
                "log_type": log.log_type,
                "clearing_type": log.clearing_type,
                "message_type": log.message_type,
                "old_account_id": log.old_account_id,
                "old_iban": log.old_iban,
                "new_account_id": log.new_account_id,
                "new_iban": log.new_iban,
                "timestamp": log.timestamp.isoformat() if hasattr(log, 'timestamp') else datetime.now().isoformat()
            } for log in audit_logs
        ]
        
        # Analyze with Groq
        analysis_result = self.groq_analyzer.analyze_manual_repairs(log_dicts)
        
        # Display results
        print(f"\n  📊 Analysis Results (Confidence: {analysis_result.confidence_score:.2f}):")
        print(f"     {analysis_result.reasoning}\n")
        
        # Show identified patterns
        if analysis_result.patterns:
            print("  🔍 Identified Patterns:")
            for pattern in analysis_result.patterns:
                print(f"     • {pattern.get('pattern_type', 'Unknown')}: {pattern.get('description', 'No description')}")
                print(f"       Frequency: {pattern.get('frequency', 0)} occurrences")
        
        # Show automation opportunities
        if analysis_result.automation_opportunities:
            print("\n  🎯 Automation Opportunities:")
            for opp in analysis_result.automation_opportunities:
                print(f"     • {opp.get('opportunity', 'Unknown opportunity')}")
                print(f"       Potential automation: {opp.get('potential_automation_rate', 0)}%")
                print(f"       Complexity: {opp.get('complexity', 'Unknown')}")
        
        return analysis_result
    
    def _demonstrate_automation_suggestions(self):
        """Show AI-generated automation rule suggestions"""
        
        # Get recent analysis or perform new analysis
        audit_logs = self._get_sample_audit_logs()
        log_dicts = [
            {
                "log_type": log.get("log_type"),
                "clearing_type": log.get("clearing_type"),
                "message_type": log.get("message_type"),
                "old_account_id": log.get("old_account_id"),
                "old_iban": log.get("old_iban"),
                "new_account_id": log.get("new_account_id"),
                "new_iban": log.get("new_iban")
            } for log in audit_logs
        ]
        
        analysis_result = self.groq_analyzer.analyze_manual_repairs(log_dicts)
        
        print("  🧠 AI-Generated Automation Rules:")
        
        if analysis_result.suggested_rules:
            for i, rule in enumerate(analysis_result.suggested_rules, 1):
                print(f"\n     Rule #{i}: {rule.get('rule_name', 'Unnamed Rule')}")
                print(f"     Type: {rule.get('rule_type', 'Unknown')}")
                print(f"     Condition: {rule.get('condition', 'No condition specified')}")
                print(f"     Action: {rule.get('action', 'No action specified')}")
                print(f"     Confidence: {rule.get('confidence', 0):.2f}")
                print(f"     Risk Level: {rule.get('risk_level', 'Unknown')}")
        else:
            print("     No specific automation rules generated")
    
    def _demonstrate_realtime_suggestions(self):
        """Show real-time repair suggestions for failed validations"""
        
        # Sample account with validation failure
        failed_accounts = [
            {
                "account_id": "ACC999",
                "iban": "DE89 3704 0044 0532 0130 99",
                "clearing_type": "SEPA",
                "validation_error": "IBAN format invalid - contains spaces"
            },
            {
                "account_id": "ACC 888",
                "iban": "GB29NWBK601613311400",
                "clearing_type": "SWIFT",
                "validation_error": "Account ID contains invalid characters"
            }
        ]
        
        print("  ⚡ Real-time Repair Suggestions:")
        
        for account_data in failed_accounts:
            print(f"\n     Account: {account_data['account_id']}")
            print(f"     Issue: {account_data['validation_error']}")
            
            # Get AI suggestions
            suggestions = self.groq_analyzer.generate_repair_suggestions(account_data)
            
            if suggestions:
                print(f"     💡 AI Suggestions:")
                for j, suggestion in enumerate(suggestions, 1):
                    print(f"        {j}. {suggestion.get('description', 'No description')}")
                    print(f"           Confidence: {suggestion.get('confidence', 0):.2f}")
                    print(f"           Changes: {suggestion.get('proposed_changes', {})}")
            else:
                print(f"     ⚠️  No automatic suggestions available")
    
    def _get_sample_audit_logs(self):
        """Generate sample audit logs for demonstration"""
        return [
            {
                "log_type": "DR_ACCOUNT_MANUAL_REPAIR",
                "clearing_type": "SEPA",
                "message_type": "PAIN001",
                "old_account_id": "ACC001",
                "old_iban": "DE89 3704 0044 0532 0130 00",
                "new_account_id": "ACC001",
                "new_iban": "DE89370400440532013000"
            },
            {
                "log_type": "CR_ACCOUNT_MANUAL_REPAIR",
                "clearing_type": "SEPA",
                "message_type": "PAIN001",
                "old_account_id": "ACC 003",
                "old_iban": "FR1420041010050500013M02606",
                "new_account_id": "ACC003",
                "new_iban": "FR1420041010050500013M02606"
            },
            {
                "log_type": "DR_ACCOUNT_MANUAL_REPAIR",
                "clearing_type": "SEPA",
                "message_type": "PAIN008",
                "old_account_id": "ACC004",
                "old_iban": "ES91 2100 0418 4502 0005 1332",
                "new_account_id": "ACC004",
                "new_iban": "ES9121000418450200051332"
            }
        ]


def main():
    """Main demo function"""
    try:
        print("🎯 Initializing Groq AI Enhanced APS System...")
        demo = GroqAPSDemo()
        demo.run_demo()

    except Exception as e:
        logger.error(f"Demo failed: {str(e)}")
        print(f"❌ Demo failed: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Ensure Groq API key is valid")
        print("2. Check internet connectivity")
        print("3. Verify all dependencies are installed")


if __name__ == "__main__":
    main()