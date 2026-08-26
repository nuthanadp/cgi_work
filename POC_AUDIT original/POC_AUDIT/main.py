"""
Main application demonstrating the APS (Automatic Payment System) POC
with AI-driven repair rule suggestions
"""

import json
from datetime import datetime
from pathlib import Path

from src.core.payment_processor import PaymentProcessor
from src.logging.audit_logger import AuditLogger
from src.ai.pattern_analyzer import PatternAnalyzer
from src.ai.rule_suggester import RuleSuggester
from src.storage.database import DatabaseManager
from src.api.manual_repair_api import create_manual_repair_app
from src.models import (
    PaymentTransaction, Account, ManualRepairAuditLog,
    ClearingType, MessageType, AccountType
)


class APSDemo:
    """Main demonstration class for the APS POC"""
    
    def __init__(self):
        print("🚀 Initializing APS (Automatic Payment System) POC...")
        
        # Initialize core components
        self.payment_processor = PaymentProcessor()
        self.audit_logger = AuditLogger("data/audit_logs.json")
        self.database = DatabaseManager("data/aps_database.sqlite")
        self.pattern_analyzer = PatternAnalyzer(self.audit_logger)
        self.rule_suggester = RuleSuggester()
        
        print("✅ APS components initialized successfully")
    
    def run_complete_demo(self):
        """Run the complete APS demonstration"""
        print("\n" + "="*80)
        print("🏦 APS (AUTOMATIC PAYMENT SYSTEM) - AI-POWERED REPAIR POC")
        print("="*80)
        
        # Step 1: Load and process sample transactions
        print("\n📥 STEP 1: Processing Payment Transactions")
        self._load_sample_transactions()
        
        # Step 2: Simulate manual repairs
        print("\n🔧 STEP 2: Simulating Manual Repairs") 
        self._simulate_manual_repairs()
        
        # Step 3: Analyze patterns
        print("\n🤖 STEP 3: AI Pattern Analysis")
        patterns = self._analyze_repair_patterns()
        
        # Step 4: Generate rule suggestions
        print("\n💡 STEP 4: AI Rule Suggestions")
        suggestions = self._generate_rule_suggestions(patterns)
        
        # Step 5: Display results and insights
        print("\n📊 STEP 5: Results and Insights")
        self._display_insights(patterns, suggestions)
        
        # Step 6: Show implementation plan
        print("\n🗺️  STEP 6: Implementation Plan")
        self._show_implementation_plan(suggestions)
        
        print("\n" + "="*80)
        print("✅ APS POC Demonstration Complete!")
        print("="*80)
        
        return {
            "patterns": patterns,
            "suggestions": suggestions,
            "processor_stats": self.payment_processor.get_processing_statistics(),
            "audit_summary": self.audit_logger.generate_summary(30)
        }
    
    def _load_sample_transactions(self):
        """Load and process sample payment transactions"""
        try:
            with open("data/sample_data.json", "r") as f:
                data = json.load(f)
            
            transactions = []
            for tx_data in data["sample_transactions"]:
                # Convert dict to PaymentTransaction model
                debitor = Account(**tx_data["debitor_account"])
                creditor = Account(**tx_data["creditor_account"])
                
                transaction = PaymentTransaction(
                    transaction_id=tx_data["transaction_id"],
                    debitor_account=debitor,
                    creditor_account=creditor,
                    amount=tx_data["amount"],
                    currency=tx_data["currency"],
                    clearing_type=ClearingType(tx_data["clearing_type"]),
                    message_type=MessageType(tx_data["message_type"]),
                    validation_status=tx_data["validation_status"]
                )
                transactions.append(transaction)
            
            print(f"   📋 Loaded {len(transactions)} sample transactions")
            
            # Process transactions
            results = self.payment_processor.batch_process_payments(transactions)
            
            passed = len([r for r in results if r.validation_passed])
            auto_repaired = len([r for r in results if r.auto_repair_successful])
            manual_needed = len([r for r in results if r.requires_manual_repair])
            
            print(f"   ✅ Validation passed: {passed}")
            print(f"   🔧 Auto-repaired: {auto_repaired}")
            print(f"   👤 Manual repair needed: {manual_needed}")
            
            # Save to database
            for transaction in transactions:
                self.database.save_payment_transaction(transaction)
                
        except Exception as e:
            print(f"   ❌ Error loading transactions: {e}")
    
    def _simulate_manual_repairs(self):
        """Simulate manual repair operations"""
        try:
            with open("data/sample_data.json", "r") as f:
                data = json.load(f)
            
            repairs = data["sample_manual_repairs"]
            print(f"   🔧 Simulating {len(repairs)} manual repairs...")
            
            for repair_data in repairs:
                # Create audit log
                log = ManualRepairAuditLog(
                    log_id=repair_data["log_id"],
                    log_type=repair_data["log_type"],
                    transaction_id=repair_data["transaction_id"],
                    clearing_type=ClearingType(repair_data["clearing_type"]),
                    message_type=MessageType(repair_data["message_type"]),
                    old_account_id=repair_data["old_account_id"],
                    old_iban=repair_data["old_iban"],
                    new_account_id=repair_data["new_account_id"],
                    new_iban=repair_data["new_iban"],
                    repaired_by=repair_data["repaired_by"],
                    repair_timestamp=datetime.now(),
                    repair_reason=repair_data["repair_reason"],
                    validation_errors=repair_data["validation_errors"],
                    auto_repair_attempts=repair_data["auto_repair_attempts"]
                )
                
                self.audit_logger.logs.append(log)
                self.database.save_manual_repair_log(log)
            
            print(f"   ✅ Simulated {len(repairs)} manual repairs")
            print(f"   📝 Generated audit logs with standardized format:")
            print(f"       • DR_ACCOUNT_MANUAL_REPAIR: Debitor account repairs")
            print(f"       • CR_ACCOUNT_MANUAL_REPAIR: Creditor account repairs")
            
        except Exception as e:
            print(f"   ❌ Error simulating repairs: {e}")
    
    def _analyze_repair_patterns(self):
        """Analyze repair patterns using AI"""
        print("   🧠 Running AI pattern analysis...")
        
        patterns = self.pattern_analyzer.analyze_patterns(days_back=30)
        
        if patterns:
            print(f"   ✅ Identified {len(patterns)} repair patterns")
            
            for i, pattern in enumerate(patterns[:3], 1):
                print(f"   {i}. {pattern.pattern_description}")
                print(f"      • Feasibility: {pattern.automation_feasibility:.2f}")
                print(f"      • Occurrences: {pattern.occurrence_count}")
                print(f"      • Users: {pattern.unique_users}")
        else:
            print("   ⚠️  No significant patterns identified")
        
        return patterns
    
    def _generate_rule_suggestions(self, patterns):
        """Generate AI rule suggestions"""
        print("   🎯 Generating automation rule suggestions...")
        
        suggestions = self.rule_suggester.suggest_rules_from_patterns(patterns)
        
        if suggestions:
            print(f"   ✅ Generated {len(suggestions)} rule suggestions")
            
            for i, suggestion in enumerate(suggestions[:3], 1):
                risk_emoji = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}[suggestion.risk_level]
                print(f"   {i}. {suggestion.suggested_rule.rule_name}")
                print(f"      • Confidence: {suggestion.confidence_score:.2f}")
                print(f"      • Risk: {risk_emoji} {suggestion.risk_level}")
                print(f"      • Potential automation: {suggestion.manual_repair_count} repairs")
        else:
            print("   ⚠️  No rule suggestions generated")
        
        return suggestions
    
    def _display_insights(self, patterns, suggestions):
        """Display key insights and analytics"""
        # Processing statistics
        stats = self.payment_processor.get_processing_statistics()
        print("   📈 PROCESSING STATISTICS:")
        print(f"      • Total processed: {stats['total_processed']}")
        print(f"      • Auto-repair rate: {stats.get('auto_repair_rate', 0):.1f}%")
        print(f"      • Manual repair rate: {stats.get('manual_repair_rate', 0):.1f}%")
        
        # Audit summary
        summary = self.audit_logger.generate_summary(30)
        print(f"\n   📝 AUDIT SUMMARY (Last 30 days):")
        print(f"      • Total manual repairs: {summary.total_logs}")
        print(f"      • Debitor repairs: {summary.dr_repairs}")
        print(f"      • Creditor repairs: {summary.cr_repairs}")
        
        # Pattern insights
        if patterns:
            print(f"\n   🔍 PATTERN INSIGHTS:")
            high_feasibility = len([p for p in patterns if p.automation_feasibility > 0.8])
            print(f"      • High-feasibility patterns: {high_feasibility}")
            
            total_automatable = sum(p.occurrence_count for p in patterns if p.automation_feasibility > 0.7)
            total_repairs = sum(p.occurrence_count for p in patterns)
            automation_potential = (total_automatable / total_repairs * 100) if total_repairs > 0 else 0
            print(f"      • Automation potential: {automation_potential:.1f}%")
        
        # AI insights
        if patterns:
            ai_insights = self.pattern_analyzer.generate_automation_insights(patterns)
            print(f"\n   🤖 AI RECOMMENDATIONS:")
            for rec in ai_insights.get('recommendations', [])[:3]:
                print(f"      • {rec}")
    
    def _show_implementation_plan(self, suggestions):
        """Show implementation plan for rule suggestions"""
        if not suggestions:
            print("   ⚠️  No suggestions available for implementation planning")
            return
        
        plan = self.rule_suggester.generate_implementation_plan(suggestions)
        
        print("   🗺️  IMPLEMENTATION PLAN:")
        print(f"\n   📊 SUMMARY:")
        summary = plan['summary']
        print(f"      • Total suggestions: {summary['total_suggestions']}")
        print(f"      • Low risk: {summary['low_risk_suggestions']}")
        print(f"      • Medium risk: {summary['medium_risk_suggestions']}")
        print(f"      • High risk: {summary['high_risk_suggestions']}")
        
        print(f"\n   🚀 PHASE 1 - IMMEDIATE IMPLEMENTATION:")
        phase1 = plan['implementation_phases']['phase_1_immediate']
        print(f"      • {phase1['description']}")
        print(f"      • Automation potential: {phase1['estimated_automation_percentage']:.1f}%")
        
        for rule in phase1['rules'][:2]:
            print(f"      • {rule['rule_name']}")
            print(f"        - Confidence: {rule['confidence']:.2f}")
            print(f"        - Automates: {rule['automation_count']} repairs")
        
        print(f"\n   🔍 TOP RECOMMENDATIONS:")
        for i, rec in enumerate(plan['recommendations'][:3], 1):
            print(f"      {i}. {rec}")
    
    def run_api_demo(self):
        """Demonstrate the API interface"""
        print("\n🌐 API DEMONSTRATION")
        print("   Starting FastAPI server for manual repair interface...")
        
        # Create API app
        app = create_manual_repair_app(self.audit_logger, self.payment_processor)
        
        print("   ✅ API endpoints available:")
        print("      • POST /repair/manual - Perform manual repair")
        print("      • GET /repair/suggestions/{transaction_id} - Get repair suggestions")
        print("      • GET /repair/history - Get repair history") 
        print("      • GET /repair/stats - Get repair statistics")
        print("      • GET /repair/patterns - Get automation patterns")
        print("      • POST /repair/validate - Validate account repair")
        
        return app
    
    def export_results(self, output_dir: str = "output"):
        """Export demonstration results"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print(f"\n💾 EXPORTING RESULTS to {output_dir}/")
        
        # Export processing statistics
        stats = self.payment_processor.get_processing_statistics()
        with open(output_path / "processing_stats.json", "w") as f:
            json.dump(stats, f, indent=2, default=str)
        
        # Export audit summary
        summary = self.audit_logger.generate_summary(30)
        with open(output_path / "audit_summary.json", "w") as f:
            json.dump(summary.dict(), f, indent=2, default=str)
        
        # Export patterns
        patterns = self.pattern_analyzer.analyze_patterns(30)
        pattern_data = [p.dict() for p in patterns]
        with open(output_path / "repair_patterns.json", "w") as f:
            json.dump(pattern_data, f, indent=2, default=str)
        
        # Export rule suggestions
        suggestions = self.rule_suggester.suggest_rules_from_patterns(patterns)
        suggestion_data = [s.dict() for s in suggestions]
        with open(output_path / "rule_suggestions.json", "w") as f:
            json.dump(suggestion_data, f, indent=2, default=str)
        
        # Export implementation plan
        plan = self.rule_suggester.generate_implementation_plan(suggestions)
        with open(output_path / "implementation_plan.json", "w") as f:
            json.dump(plan, f, indent=2, default=str)
        
        print("   ✅ Results exported:")
        print("      • processing_stats.json - Payment processing statistics")
        print("      • audit_summary.json - Manual repair audit summary")
        print("      • repair_patterns.json - Identified automation patterns")
        print("      • rule_suggestions.json - AI-generated repair rules")
        print("      • implementation_plan.json - Rule implementation roadmap")


def main():
    """Main entry point for the APS POC demonstration"""
    try:
        # Initialize and run demo
        demo = APSDemo()
        results = demo.run_complete_demo()
        
        # Export results
        demo.export_results()
        
        # Optional: Start API server for interactive testing
        print("\n🌐 To start the API server for interactive testing:")
        print("   python -c \"from main import APSDemo; demo = APSDemo(); app = demo.run_api_demo(); import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000)\"")
        
        return results
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        raise


if __name__ == "__main__":
    main()