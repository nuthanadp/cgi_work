#!/usr/bin/env python3
"""
Microsoft Phi-3-mini-4k-instruct Demo for APS Manual Repair Analysis
Demonstrates local LLM inference without API dependencies
"""

import logging
import json
from datetime import datetime, timezone
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ai.phi3_analyzer import Phi3Analyzer
from config.settings import APSConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Phi3APSDemo:
    """Demonstration of Phi-3 enhanced APS system"""
    
    def __init__(self):
        self.phi3_analyzer = Phi3Analyzer()
        logger.info("Phi-3 APS Demo initialized")
    
    def get_enhanced_sample_logs(self):
        """Generate comprehensive sample audit logs for Phi-3 analysis"""
        return [
            {
                "log_type": "DR_ACCOUNT_MANUAL_REPAIR",
                "clearing_type": "SEPA",
                "message_type": "MT103", 
                "old_account_id": "ACC001",
                "old_iban": "DE89 3704 0044 0532 0130 00",  # Spaces
                "new_account_id": "ACC001",
                "new_iban": "DE89370400440532013000",         # Spaces removed
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "repair_reason": "IBAN formatting - spaces removed",
                "user_id": "user123",
                "session_id": "sess_001"
            },
            {
                "log_type": "CR_ACCOUNT_MANUAL_REPAIR",
                "clearing_type": "SEPA",
                "message_type": "MT103",
                "old_account_id": "ACC002", 
                "old_iban": "FR14 2004 1010 0505 0001 3M02 606",  # Spaces
                "new_account_id": "ACC002",
                "new_iban": "FR1420041010050500013M02606",          # Spaces removed
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "repair_reason": "IBAN formatting - spaces removed",
                "user_id": "user456",
                "session_id": "sess_002"
            },
            {
                "log_type": "DR_ACCOUNT_MANUAL_REPAIR",
                "clearing_type": "SWIFT",
                "message_type": "MT202",
                "old_account_id": "ACC003",
                "old_iban": "GB29NWBK601613311400",        # Short IBAN
                "new_account_id": "ACC004", 
                "new_iban": "GB29NWBK60161331140000",      # Corrected length
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "repair_reason": "IBAN length correction",
                "user_id": "user789",
                "session_id": "sess_003"
            },
            {
                "log_type": "CR_ACCOUNT_MANUAL_REPAIR",
                "clearing_type": "TARGET2",
                "message_type": "MT103",
                "old_account_id": "ACC005",
                "old_iban": "IT60 X054 2811 1010 0000 0123 456",   # Spaces and X
                "new_account_id": "ACC005",
                "new_iban": "IT6005428111010000000123456",          # Cleaned
                "timestamp": datetime.now(timezone.utc).isoformat(), 
                "repair_reason": "IBAN format and character correction",
                "user_id": "user101",
                "session_id": "sess_004"
            }
        ]
    
    def run_phi3_demo(self):
        """Run complete Phi-3 enhanced APS demo"""
        print("🚀 Microsoft Phi-3 APS Demo")
        print("=" * 60)
        
        # Step 1: Display sample logs
        sample_logs = self.get_enhanced_sample_logs()
        print(f"\n📋 Step 1: Enhanced Sample Manual Repair Logs ({len(sample_logs)} logs)")
        for i, log in enumerate(sample_logs, 1):
            print(f"  {i}. {log['log_type']}: {log['clearing_type']}/{log['message_type']}")
            print(f"     Old IBAN: {log['old_iban']}")
            print(f"     New IBAN: {log['new_iban']}")
            print(f"     Reason: {log['repair_reason']}")
        
        # Step 2: Phi-3 Analysis
        print(f"\n🤖 Step 2: Phi-3 Local LLM Analysis")
        print("  Analyzing patterns with Microsoft Phi-3-mini-4k-instruct...")
        
        try:
            # Run Phi-3 analysis
            analysis_result = self.phi3_analyzer.analyze_manual_repairs(sample_logs)
            
            # Display results
            print("📊 Analysis Results:")
            print(f"  • Confidence: {analysis_result.confidence}%")
            print(f"  • Patterns Found: {len(analysis_result.patterns)}")
            print(f"  • Suggested Rules: {len(analysis_result.suggested_rules)}")
            print(f"  • Automation Opportunities: {len(analysis_result.automation_opportunities)}")
            
            # Step 3: Display detected patterns
            print(f"\n🔍 Step 3: Detected Patterns")
            for i, pattern in enumerate(analysis_result.patterns, 1):
                print(f"  {i}. {pattern['type']}")
                print(f"     Frequency: {pattern['frequency']}")
                print(f"     Description: {pattern['description']}")
                if 'example_old' in pattern:
                    print(f"     Example: {pattern['example_old']} → {pattern['example_new']}")
            
            # Step 4: Display AI-generated rules
            print(f"\n💡 Step 4: Phi-3 Generated Automation Rules")
            for i, rule in enumerate(analysis_result.suggested_rules, 1):
                print(f"  {i}. {rule['rule_name']}")
                print(f"     Type: {rule['rule_type']}")
                print(f"     Condition: {rule['condition']}")
                print(f"     Action: {rule['action']}")
                print(f"     Confidence: {rule['confidence']}%")
                print(f"     Risk Level: {rule['risk_level']}")
                if 'estimated_success_rate' in rule:
                    print(f"     Success Rate: {rule['estimated_success_rate']}")
            
            # Step 5: Display automation opportunities
            print(f"\n🎯 Step 5: Automation Opportunities")
            for i, opp in enumerate(analysis_result.automation_opportunities, 1):
                print(f"  {i}. {opp['opportunity']}")
                print(f"     Automation Rate: {opp['automation_rate']}")
                print(f"     Complexity: {opp['complexity']}")
                if 'expected_benefit' in opp:
                    print(f"     Expected Benefit: {opp['expected_benefit']}")
                if 'implementation_effort' in opp:
                    print(f"     Implementation Effort: {opp['implementation_effort']}")
            
            # Step 6: Model info
            print(f"\n🧠 Step 6: Phi-3 Model Information")
            print(f"  Model: {self.phi3_analyzer.model_name}")
            print(f"  Device: {self.phi3_analyzer.device}")
            print(f"  Status: {'✅ Local inference active' if self.phi3_analyzer.model else '⚠️ Fallback mode'}")
            
            print("\n✅ Phi-3 Demo completed successfully!")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Phi-3 demo failed: {e}")
            print(f"❌ Demo failed: {e}")
            print("\nTroubleshooting tips:")
            print("1. Ensure transformers and torch are installed")
            print("2. Check available memory (Phi-3 requires ~4GB)")  
            print("3. Try CPU mode if CUDA errors occur")
            print("4. Verify internet connection for model download")
            return None
    
    def compare_models(self):
        """Compare Phi-3 vs Groq performance"""
        print("\n🔬 Model Comparison: Phi-3 vs Groq")
        print("=" * 50)
        
        comparison_table = [
            ["Feature", "Phi-3-mini-4k", "Groq Llama-3-8B"],
            ["Location", "Local", "Remote API"],
            ["Parameters", "3.8B", "8B"],
            ["Context", "4K tokens", "8K tokens"],
            ["Speed", "Medium (CPU)", "Very Fast"],
            ["Privacy", "100% Local", "API calls"],
            ["Cost", "Free", "Pay per token"],
            ["Availability", "Always", "Requires internet"],
            ["Memory", "~4GB RAM", "No local memory"],
            ["Latency", "Low", "Very Low"]
        ]
        
        for row in comparison_table:
            print(f"{row[0]:<15} | {row[1]:<15} | {row[2]:<15}")
        
        print("\n🎯 Use Cases:")
        print("  Phi-3: Privacy-critical, offline deployment, cost-sensitive")
        print("  Groq: High-speed, cloud-native, real-time applications")

def main():
    """Main demo function"""
    try:
        demo = Phi3APSDemo()
        
        # Run Phi-3 demo
        result = demo.run_phi3_demo()
        
        # Show model comparison
        demo.compare_models()
        
        # Save results if successful
        if result:
            output_file = f"phi3_analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w') as f:
                json.dump({
                    "model": "microsoft/Phi-3-mini-4k-instruct",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "confidence": result.confidence,
                    "patterns": result.patterns,
                    "suggested_rules": result.suggested_rules,
                    "automation_opportunities": result.automation_opportunities
                }, f, indent=2)
            print(f"\n💾 Results saved to: {output_file}")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"❌ Demo failed: {e}")

if __name__ == "__main__":
    main()