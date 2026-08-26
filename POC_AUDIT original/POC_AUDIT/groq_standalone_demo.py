"""
Standalone Groq AI Demo for APS Pattern Analysis
Pure Groq implementation without pandas/numpy dependencies
"""

import json
import logging
from typing import List, Dict, Any
from groq import Groq
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class GroqAnalysisResult:
    """Result of Groq AI analysis"""
    patterns: List[Dict[str, Any]]
    suggested_rules: List[Dict[str, Any]] 
    automation_opportunities: List[Dict[str, Any]]
    confidence_score: float
    reasoning: str


class GroqAPS:
    """
    Standalone APS POC using pure Groq AI for pattern identification
    No pandas, no numpy - just intelligent LLM analysis!
    """
    
    def __init__(self, api_key: str = ""):
        self.logger = logging.getLogger(__name__)
        import os
        api_key = api_key or os.getenv("GROQ_API_KEY", "")
        
        # Initialize Groq client
        try:
            self.client = Groq(api_key=api_key)
            self.model = "llama3-8b-8192"  # Fast inference model
            self.logger.info("🤖 Groq AI initialized successfully!")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Groq: {e}")
            self.client = None
    
    def analyze_repair_patterns(self, repair_logs: List[Dict]) -> GroqAnalysisResult:
        """
        Use Groq AI to intelligently identify patterns in manual repairs
        This is where AI does the heavy lifting instead of traditional ML!
        """
        if not self.client:
            return self._create_fallback_result()
        
        try:
            prompt = self._build_analysis_prompt(repair_logs)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an AI banking expert specializing in payment system automation. 
                        Analyze manual repair patterns and suggest intelligent automation rules.
                        Focus on IBAN formatting, account validation, and safe automation opportunities."""
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Very consistent analysis
                max_tokens=3000,
                top_p=0.95
            )
            
            return self._parse_response(response.choices[0].message.content)
            
        except Exception as e:
            self.logger.error(f"❌ Groq analysis failed: {e}")
            return self._create_fallback_result()
    
    def _build_analysis_prompt(self, repair_logs: List[Dict]) -> str:
        """Build intelligent prompt for Groq analysis"""
        
        # Prepare clean log data for analysis
        clean_logs = []
        for i, log in enumerate(repair_logs):
            clean_log = {
                "repair_id": i + 1,
                "type": log.get("log_type", "UNKNOWN"),
                "clearing_type": log.get("clearing_type"),
                "old_iban": log.get("old_iban", ""),
                "new_iban": log.get("new_iban", ""),
                "old_account": log.get("old_account_id", ""),
                "new_account": log.get("new_account_id", ""),
                "change_type": self._identify_change_type(log)
            }
            clean_logs.append(clean_log)
        
        return f"""
🏦 BANKING SYSTEM ANALYSIS: Manual Account Repairs

I need you to analyze these {len(repair_logs)} manual repair logs and identify automation opportunities:

REPAIR DATA:
{json.dumps(clean_logs, indent=2)}

🎯 YOUR MISSION:
1. 🔍 Find recurring patterns in these manual fixes
2. 🤖 Suggest automation rules that could prevent these manual interventions  
3. 📊 Assess which repairs are safe to automate vs require human review
4. ⚡ Focus on high-impact, low-risk automation opportunities

🔒 SAFETY REQUIREMENTS:
- Only suggest automation for low-risk formatting issues
- Flag high-risk changes that need human verification
- Ensure regulatory compliance for banking operations

📋 RESPONSE FORMAT (JSON):
{{
    "patterns": [
        {{
            "type": "pattern_name",
            "frequency": number_of_occurrences, 
            "description": "what pattern was found",
            "examples": ["example1", "example2"],
            "automation_risk": "LOW/MEDIUM/HIGH"
        }}
    ],
    "suggested_rules": [
        {{
            "rule_name": "descriptive_name",
            "trigger_condition": "when to apply rule",
            "action": "what to do automatically", 
            "confidence": 0.95,
            "risk_level": "LOW/MEDIUM/HIGH",
            "regulatory_notes": "compliance considerations"
        }}
    ],
    "automation_opportunities": [
        {{
            "opportunity": "description",
            "estimated_automation_rate": 85,
            "implementation_complexity": "LOW/MEDIUM/HIGH",
            "business_impact": "HIGH/MEDIUM/LOW"
        }}
    ],
    "confidence_score": 0.92,
    "reasoning": "explanation of analysis approach"
}}

🚀 Make this analysis sharp, actionable, and banking-regulation compliant!
"""
    
    def _identify_change_type(self, log: Dict) -> str:
        """Intelligently identify what type of change was made"""
        old_iban = log.get("old_iban", "")
        new_iban = log.get("new_iban", "")
        
        if old_iban and new_iban:
            # Remove spaces and compare
            old_clean = old_iban.replace(" ", "").replace("-", "")
            new_clean = new_iban.replace(" ", "").replace("-", "")
            
            if old_clean == new_clean:
                return "FORMATTING_ONLY" 
            elif len(old_clean) != len(new_clean):
                return "LENGTH_CHANGE"
            else:
                return "CONTENT_CHANGE"
        
        old_account = log.get("old_account_id", "")
        new_account = log.get("new_account_id", "")
        if old_account != new_account:
            return "ACCOUNT_ID_CHANGE"
            
        return "UNKNOWN_CHANGE"
    
    def _parse_response(self, response_text: str) -> GroqAnalysisResult:
        """Parse Groq's JSON response into structured result"""
        try:
            # Clean up response if wrapped in markdown
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_text = response_text[start:end].strip()
            else:
                json_text = response_text.strip()
            
            data = json.loads(json_text)
            
            return GroqAnalysisResult(
                patterns=data.get("patterns", []),
                suggested_rules=data.get("suggested_rules", []),
                automation_opportunities=data.get("automation_opportunities", []),
                confidence_score=data.get("confidence_score", 0.0),
                reasoning=data.get("reasoning", "Groq AI analysis completed")
            )
            
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Failed to parse Groq JSON: {e}")
            self.logger.debug(f"Raw response: {response_text}")
            return self._create_fallback_result()
    
    def _create_fallback_result(self) -> GroqAnalysisResult:
        """Fallback result when Groq is unavailable"""
        return GroqAnalysisResult(
            patterns=[{"type": "fallback", "description": "Groq AI unavailable"}],
            suggested_rules=[{"rule_name": "MANUAL_REVIEW", "confidence": 0.5}],
            automation_opportunities=[{"opportunity": "Limited without AI analysis"}],
            confidence_score=0.1,
            reasoning="Groq AI service unavailable - manual analysis needed"
        )
    
    def run_demo(self):
        """Run the full APS POC demonstration"""
        print("🚀 Groq AI-Powered APS Demo")
        print("=" * 60)
        print("🤖 Using PURE Groq AI for intelligent pattern analysis")
        print("❌ NO pandas, NO numpy - just smart LLM reasoning!")
        print("=" * 60)
        
        # Generate sample manual repair logs
        print("\n📋 Step 1: Sample Manual Repair Logs")
        sample_logs = self._generate_sample_logs()
        
        for i, log in enumerate(sample_logs, 1):
            change_type = self._identify_change_type(log)
            print(f"  {i}. {log['log_type']}: {log['old_iban']} → {log['new_iban']}")
            print(f"     Change: {change_type}")
        
        # Analyze with Groq AI
        print(f"\n🤖 Step 2: Groq AI Analysis ({self.model})")
        print("   Analyzing patterns for automation opportunities...")
        
        analysis = self.analyze_repair_patterns(sample_logs)
        
        # Display results
        print(f"\n📊 Step 3: AI Analysis Results")
        print(f"   • Overall Confidence: {analysis.confidence_score:.1%}")
        print(f"   • Patterns Identified: {len(analysis.patterns)}")
        print(f"   • Automation Rules Suggested: {len(analysis.suggested_rules)}")
        print(f"   • Opportunities Found: {len(analysis.automation_opportunities)}")
        
        print(f"\n🔍 Identified Patterns:")
        for pattern in analysis.patterns:
            risk = pattern.get('automation_risk', 'UNKNOWN')
            emoji = "🟢" if risk == "LOW" else "🟡" if risk == "MEDIUM" else "🔴"
            print(f"   {emoji} {pattern.get('type', 'Unknown')}: {pattern.get('description', 'No description')}")
            
        print(f"\n💡 Suggested Automation Rules:")
        for rule in analysis.suggested_rules:
            confidence = rule.get('confidence', 0) * 100
            risk = rule.get('risk_level', 'UNKNOWN')
            emoji = "✅" if risk == "LOW" else "⚠️" if risk == "MEDIUM" else "❌"
            print(f"   {emoji} {rule.get('rule_name', 'Unknown Rule')} ({confidence:.0f}% confidence)")
            print(f"      Action: {rule.get('action', 'Not specified')}")
            
        print(f"\n🎯 Automation Opportunities:")
        for opp in analysis.automation_opportunities:
            rate = opp.get('estimated_automation_rate', 0)
            impact = opp.get('business_impact', 'UNKNOWN')
            print(f"   📈 {opp.get('opportunity', 'Unknown')}")
            print(f"      Potential Rate: {rate}% | Impact: {impact}")
        
        print(f"\n🧠 AI Reasoning:")
        print(f"   {analysis.reasoning}")
        
        print("\n✅ Demo completed successfully!")
        print("🎉 Groq AI successfully identified automation patterns!")
        
    def _generate_sample_logs(self):
        """Generate realistic sample manual repair logs"""
        return [
            {
                "log_type": "DR_ACCOUNT_MANUAL_REPAIR",
                "clearing_type": "SEPA", 
                "message_type": "103",
                "old_account_id": "ACC001",
                "old_iban": "DE89 3704 0044 0532 0130 00",  # Has spaces
                "new_account_id": "ACC001",
                "new_iban": "DE89370400440532013000",        # No spaces
                "timestamp": datetime.now().isoformat()
            },
            {
                "log_type": "CR_ACCOUNT_MANUAL_REPAIR", 
                "clearing_type": "SEPA",
                "message_type": "103", 
                "old_account_id": "ACC 002",                 # Space in account ID
                "old_iban": "GB29 NWBK 6016 1331 1400 00",  # Spaces in IBAN
                "new_account_id": "ACC002",                   # No space
                "new_iban": "GB29NWBK60161331140000",         # No spaces
                "timestamp": datetime.now().isoformat()
            },
            {
                "log_type": "DR_ACCOUNT_MANUAL_REPAIR",
                "clearing_type": "SWIFT",
                "message_type": "202",
                "old_account_id": "ACC003", 
                "old_iban": "FR14 2004 1010 0505 0001 3M02 606",  # French IBAN with spaces
                "new_account_id": "ACC003",
                "new_iban": "FR1420041010050500013M02606",          # No spaces
                "timestamp": datetime.now().isoformat()
            },
            {
                "log_type": "CR_ACCOUNT_MANUAL_REPAIR",
                "clearing_type": "SEPA", 
                "message_type": "103",
                "old_account_id": "ACC004",
                "old_iban": "IT60 X054 2811 1010 0000 0123 456",   # Italian with spaces
                "new_account_id": "ACC004", 
                "new_iban": "IT60X0542811101000000123456",           # No spaces  
                "timestamp": datetime.now().isoformat()
            }
        ]


if __name__ == "__main__":
    print("🎯 Starting Groq AI-Powered APS Analysis...")
    
    # Initialize and run demo
    aps = GroqAPS()
    aps.run_demo()
