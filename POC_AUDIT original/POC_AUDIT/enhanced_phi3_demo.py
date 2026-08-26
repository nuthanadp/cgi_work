#!/usr/bin/env python3
"""
Enhanced Phi-3 Demo for APS System
Demonstrates data-driven repair rule generation from repeated manual fix patterns
"""

import json
import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ai.phi3_analyzer import Phi3Analyzer

def load_enhanced_audit_logs():
    """Load enhanced audit logs with repeated patterns for testing"""
    try:
        with open("data/enhanced_audit_logs.json", "r") as f:
            data = json.load(f)
        return data["enhanced_manual_repair_logs"]
    except FileNotFoundError:
        print("⚠️  Enhanced audit logs not found, using sample data...")
        return [
            {
                "log_type": "DR_ACCOUNT_MANUAL_REPAIR",
                "clearing_type": "SEPA",
                "message_type": "103",
                "old_account_id": "ACC001",
                "old_iban": "DE89 3704 0044 0532 0130 00",
                "new_account_id": "ACC001",
                "new_iban": "DE89370400440532013000",
                "timestamp": "2026-03-31T10:15:30.123Z",
                "repair_reason": "IBAN space formatting"
            },
            {
                "log_type": "DR_ACCOUNT_MANUAL_REPAIR", 
                "clearing_type": "SEPA",
                "message_type": "103",
                "old_account_id": "ACC005",
                "old_iban": "DE89 3704 0044 0532 0130 00",
                "new_account_id": "ACC005",
                "new_iban": "DE89370400440532013000",
                "timestamp": "2026-03-31T14:22:15.456Z",
                "repair_reason": "IBAN space formatting"
            },
            {
                "log_type": "DR_ACCOUNT_MANUAL_REPAIR",
                "clearing_type": "SWIFT",
                "message_type": "202", 
                "old_account_id": "ACC012",
                "old_iban": "GB29NWBK601613314000",
                "new_account_id": "ACC012",
                "new_iban": "GB29NWBK60161331400000", 
                "timestamp": "2026-03-31T18:30:45.012Z",
                "repair_reason": "IBAN length correction"
            },
            {
                "log_type": "DR_ACCOUNT_MANUAL_REPAIR",
                "clearing_type": "SWIFT", 
                "message_type": "202",
                "old_account_id": "ACC015",
                "old_iban": "GB29NWBK601613314000",
                "new_account_id": "ACC015",
                "new_iban": "GB29NWBK60161331400000",
                "timestamp": "2026-03-31T20:12:33.345Z",
                "repair_reason": "IBAN length correction"
            }
        ]

def save_analysis_results(analysis_result, filename_prefix="enhanced_phi3_analysis"):
    """Save analysis results to JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.json"
    
    result_dict = analysis_result.__dict__
    result_dict["model"] = "microsoft/Phi-3-mini-4k-instruct"
    result_dict["timestamp"] = datetime.now().isoformat()
    result_dict["analysis_type"] = "data_driven_repair_rules"
    
    with open(filename, "w") as f:
        json.dump(result_dict, f, indent=2)
    
    return filename

def display_analysis_summary(analysis_result):
    """Display enhanced analysis summary focusing on data-driven rules"""
    print("\n" + "="*80)
    print("🧠 ENHANCED PHI-3 DATA-DRIVEN ANALYSIS RESULTS")
    print("="*80)
    
    print(f"\n📊 Analysis Summary:")
    print(f"  • Model: microsoft/Phi-3-mini-4k-instruct")
    print(f"  • Confidence: {analysis_result.confidence}%")
    print(f"  • Patterns Found: {len(analysis_result.patterns)}")
    print(f"  • Data-Driven Rules: {len(analysis_result.suggested_rules)}")
    print(f"  • Automation Opportunities: {len(analysis_result.automation_opportunities)}")
    
    # Display repeated patterns found
    if analysis_result.patterns:
        print(f"\n🔍 Repeated Patterns Detected:")
        for i, pattern in enumerate(analysis_result.patterns, 1):
            print(f"  {i}. {pattern['type']} (Frequency: {pattern['frequency']})")
            print(f"     Pattern: {pattern.get('pattern', pattern['description'])}")
    
    # Display data-driven rules
    if analysis_result.suggested_rules:
        print(f"\n💡 Data-Driven Auto-Repair Rules:")
        for i, rule in enumerate(analysis_result.suggested_rules, 1):
            print(f"\n  Rule {i}: {rule['rule_type']}")
            print(f"    Condition: clearingType={rule['condition']['clearingType']}, msgType={rule['condition']['msgType']}")
            print(f"               oldIBAN=\"{rule['condition']['oldIBAN']}\"")
            print(f"    Action: replace_IBAN=\"{rule['action']['replace_IBAN']}\"")
            print(f"    Confidence: {rule['confidence']}%")
            print(f"    Risk Level: {rule['risk_level']}")
            print(f"    Reason: {rule['reason']}")
    
    # Display automation opportunities
    print(f"\n🎯 Automation Opportunities:")
    for i, opportunity in enumerate(analysis_result.automation_opportunities, 1):
        print(f"  {i}. {opportunity['opportunity']}")
        print(f"     Automation Rate: {opportunity['automation_rate']}")
        print(f"     Complexity: {opportunity['complexity']}")
        if 'automatable_cases' in opportunity:
            print(f"     Coverage: {opportunity['automatable_cases']}/{opportunity['total_cases']} cases")
        if 'reason' in opportunity:
            print(f"     Reason: {opportunity['reason']}")

def demonstrate_rule_matching():
    """Demonstrate how the generated rules would work in practice"""
    print(f"\n🔧 Rule Matching Demonstration:")
    print("="*50)
    
    # Simulate a new transaction that matches one of our generated rules
    print("Scenario: New transaction with IBAN 'DE89 3704 0044 0532 0130 00' (SEPA/MT103)")
    print("✅ Rule Match Found!")
    print("   • Rule: AUTO_REPAIR_RULE for SEPA/MT103")
    print("   • Action: Replace with 'DE89370400440532013000'")
    print("   • Confidence: 90%")
    print("   • Result: ✅ AUTOMATED REPAIR SUCCESSFUL")
    
    print("\nScenario: New transaction with unknown IBAN")
    print("⚠️  No rule match found")
    print("   • Action: Route to MANUAL_REPAIR")
    print("   • Result: 📋 Manual review required")

def main():
    """Main demo function"""
    print("🚀 Enhanced Phi-3 Data-Driven APS Demo")
    print("Focus: Repeated oldIBAN → newIBAN pattern analysis")
    print("-" * 60)
    
    # Load enhanced audit logs with repeated patterns
    print("📋 Loading Enhanced Audit Logs...")
    audit_logs = load_enhanced_audit_logs()
    print(f"   Loaded {len(audit_logs)} manual repair logs")
    
    # Display sample patterns
    print("\n📊 Sample Log Patterns:")
    iban_patterns = {}
    for log in audit_logs:
        key = f"{log['old_iban']} → {log['new_iban']}"
        iban_patterns[key] = iban_patterns.get(key, 0) + 1
    
    for pattern, count in iban_patterns.items():
        print(f"   {pattern} (×{count})")
    
    # Initialize Phi-3 analyzer
    print("\n🧠 Initializing Phi-3 Analyzer...")
    analyzer = Phi3Analyzer()
    
    # Perform analysis
    print("⚡ Analyzing Manual Repair Patterns...")
    analysis_result = analyzer.analyze_manual_repairs(audit_logs)
    
    # Display results
    display_analysis_summary(analysis_result)
    
    # Demonstrate practical rule matching
    demonstrate_rule_matching()
    
    # Save results
    print(f"\n💾 Saving Analysis Results...")
    filename = save_analysis_results(analysis_result)
    print(f"   Results saved to: {filename}")
    
    print(f"\n🎉 Enhanced Data-Driven Analysis Complete!")
    print("="*80)

if __name__ == "__main__":
    main()