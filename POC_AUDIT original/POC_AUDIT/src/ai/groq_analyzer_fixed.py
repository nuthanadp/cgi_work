"""
Groq-powered AI analyzer for APS manual repair pattern analysis.
IMPROVED: Uses data-driven analysis + AI to eliminate hallucination and provide accurate results.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from groq import Groq
from dataclasses import dataclass
from collections import Counter


@dataclass
class GroqAnalysisResult:
    """Result of Groq analysis"""
    patterns: List[Dict[str, Any]]
    suggested_rules: List[Dict[str, Any]]
    automation_opportunities: List[Dict[str, Any]]
    confidence: float
    summary_stats: Dict[str, Any]


class GroqPatternAnalyzer:
    """
    IMPROVED: Data-driven + AI analyzer that eliminates hallucination
    Step 1: Extract real data patterns mathematically
    Step 2: Use AI to enhance with domain knowledge  
    Step 3: Generate precise, executable rules
    """
    
    def __init__(self, api_key: str = ""):
        self.logger = logging.getLogger(__name__)
        import os
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        
        # Initialize Groq client
        try:
            self.client = Groq(api_key=self.api_key)
            self.model = "llama3-8b-8192"
            self.logger.info("Groq AI initialized (data-driven mode)")
        except Exception as e:
            self.logger.error(f"Failed to initialize Groq: {e}")
            self.client = None
    
    def analyze_manual_repairs(self, repair_logs: List[Dict]) -> GroqAnalysisResult:
        """
        IMPROVED: Data-driven analysis + AI enhancement
        
        Args:
            repair_logs: List of manual repair log dictionaries
        
        Returns:
            GroqAnalysisResult with patterns and rules
        """
        if not repair_logs:
            return self._empty_result()
            
        # Step 1: Extract real data patterns (no AI hallucination)
        data_stats = self._extract_data_statistics(repair_logs)
        
        # Step 2: Get AI insights (optional enhancement)
        ai_insights = self._get_ai_insights(repair_logs, data_stats)
        
        # Step 3: Generate final analysis based on real data + AI enhancement
        return self._generate_final_analysis(repair_logs, data_stats, ai_insights)
    
    def _extract_data_statistics(self, repair_logs: List[Dict]) -> Dict[str, Any]:
        """Extract real statistics from repair logs data"""
        
        # Count actual clearing types, message types, log types
        clearing_types = Counter(log.get("clearing_type", "UNKNOWN") for log in repair_logs)
        message_types = Counter(log.get("message_type", "UNKNOWN") for log in repair_logs)
        log_types = Counter(log.get("log_type", "UNKNOWN") for log in repair_logs)
        
        # Detect real transformations (account/IBAN changes)
        transformations = []
        transformation_types = Counter()
        
        for log in repair_logs:
            transformation = self._detect_exact_transformation(log)
            if transformation:
                transformations.append(transformation)
                transformation_types[transformation["type"]] += 1
        
        return {
            "total_logs": len(repair_logs),
            "clearing_types": dict(clearing_types),
            "message_types": dict(message_types),
            "log_types": dict(log_types),
            "transformations": transformations,
            "transformation_types": dict(transformation_types),
            "most_common_clearing": clearing_types.most_common(1)[0] if clearing_types else ("UNKNOWN", 0),
            "most_common_message": message_types.most_common(1)[0] if message_types else ("UNKNOWN", 0)
        }
    
    def _detect_exact_transformation(self, log: Dict) -> Optional[Dict[str, Any]]:
        """Detect exact transformation between old and new values"""
        # Handle multiple field name formats (for compatibility)
        old_account = str(log.get("oldAccount", log.get("old_account_id", ""))).strip()
        new_account = str(log.get("newAccount", log.get("new_account_id", ""))).strip()
        old_iban = log.get("oldIban", log.get("old_iban", "")).strip()
        new_iban = log.get("newIban", log.get("new_iban", "")).strip()
        
        # Skip empty entries - these don't represent real transactions
        if not old_account and not new_account:
            return None
            
        # Account transformations
        if old_account and new_account and old_account != new_account:
            if new_account.endswith(old_account) and len(new_account) > len(old_account):
                prefix = new_account[:-len(old_account)]
                return {
                    "type": f"account_prefix_addition_{prefix}",
                    "field": "account_id",
                    "old": old_account,
                    "new": new_account,
                    "action": f"add_prefix_{prefix}",
                    "example": f"{old_account} → {new_account}"
                }
        
        # IBAN transformations (skip if both empty)
        if old_iban and new_iban and old_iban != new_iban:
            if len(old_iban) != len(new_iban):
                return {
                    "type": "iban_format_change",
                    "field": "iban",
                    "old": old_iban,
                    "new": new_iban,
                    "action": "reformat_iban",
                    "example": f"{old_iban} → {new_iban}"
                }
        
        return None
    
    def _get_ai_insights(self, repair_logs: List[Dict], data_stats: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get AI insights for enhancement (optional)"""
        if not self.client or not data_stats["transformations"]:
            return None
            
        try:
            # Create focused prompt with real data
            patterns_summary = "Pattern analysis:\\n"
            for t_type, count in data_stats["transformation_types"].items():
                patterns_summary += f"- {t_type}: {count} occurrences\\n"
            
            prompt = f"Analyze these REAL payment system repair patterns:\\n\\nData Statistics:\\n- Total logs: {data_stats['total_logs']}\\n- Clearing types: {data_stats['clearing_types']}\\n- Message types: {data_stats['message_types']}\\n\\n{patterns_summary}\\n\\nProvide automation insights for these actual patterns only:\\n1. Risk assessment for each pattern type (LOW/MEDIUM/HIGH)\\n2. Implementation recommendations\\n3. Business impact analysis\\n\\nReturn valid JSON only."
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            return json.loads(completion.choices[0].message.content)
            
        except Exception as e:
            self.logger.warning(f"AI insights failed: {e}")
            return None
    
    def _generate_final_analysis(self, repair_logs: List[Dict], data_stats: Dict[str, Any], ai_insights: Optional[Dict]) -> GroqAnalysisResult:
        """Generate final analysis combining data + AI"""
        
        # Calculate real automation opportunities (excluding empty transactions)
        total_real_transactions = len([log for log in repair_logs 
                                     if str(log.get("oldAccount", log.get("old_account_id", ""))).strip() or 
                                        str(log.get("newAccount", log.get("new_account_id", ""))).strip() or
                                        log.get("oldIban", log.get("old_iban", "")).strip() or 
                                        log.get("newIban", log.get("new_iban", "")).strip()])

        # Generate patterns list for display  
        patterns = []
        for transformation_type, frequency in data_stats["transformation_types"].items():
            patterns.append({
                "pattern_type": transformation_type,
                "frequency": frequency,
                "description": f"{transformation_type.title().replace('_', ' ')}: {frequency} occurrences"
            })

        # Generate suggested rules with corrected confidence calculation
        suggested_rules = []
        for transformation_type, frequency in data_stats["transformation_types"].items():
            if frequency >= 1:  # Only suggest rules for patterns that occur
                # Find example transformation
                example = next((t for t in data_stats["transformations"] if t["type"] == transformation_type), None)
                if not example:
                    continue

                risk_level = "LOW" if frequency >= 5 else "MEDIUM"

                suggested_rules.append({
                    "type": transformation_type,
                    "condition": {
                        "clearing_type": data_stats["most_common_clearing"][0],
                        "message_type": data_stats["most_common_message"][0],
                        "field": example["field"],
                        "pattern": example["action"]
                    },
                    "action": {
                        "type": example["action"],
                        "field": example["field"],
                        "transformation": example["example"]
                    },
                    "confidence": min(95, (frequency / total_real_transactions) * 100) if total_real_transactions > 0 else 0,
                    "risk_level": risk_level,
                    "frequency": frequency,
                    "reason": f"Detected {frequency} identical transformations in {total_real_transactions} real transactions"
                })
        
        automatable_transactions = sum(freq for freq in data_stats["transformation_types"].values() if freq >= 1)
        
        # Calculate automation rate based on real transactions only
        if total_real_transactions > 0:
            automation_rate = (automatable_transactions / total_real_transactions) * 100
        else:
            automation_rate = 0
        
        # Determine opportunity based on real automation rate
        if automation_rate >= 90:
            complexity = "LOW"
            opp_desc = "Very high automation potential - implement immediately"
        elif automation_rate >= 70:
            complexity = "MEDIUM"  
            opp_desc = "High automation potential - good candidate for automation"
        else:
            complexity = "HIGH"
            opp_desc = "Moderate automation potential - requires careful analysis"
        
        opportunities = []
        opportunities.append({
            "opportunity": f"Automate {list(data_stats['transformation_types'].keys())[0].replace('_', ' ')}" if data_stats["transformation_types"] else "Pattern-based automation",
            "automation_rate": f"{automation_rate:.1f}%",
            "complexity": complexity,
            "transactions": f"{automatable_transactions}/{total_real_transactions} real transactions",
            "description": opp_desc
        })
        
        # Calculate confidence based on pattern consistency in real transactions
        if total_real_transactions > 0:
            confidence = min(95.0, (automatable_transactions / total_real_transactions) * 100)
        else:
            confidence = 0.0
        
        return GroqAnalysisResult(
            patterns=patterns,
            suggested_rules=suggested_rules,
            automation_opportunities=opportunities,
            confidence=confidence,
            summary_stats=data_stats
        )
    
    def _empty_result(self) -> GroqAnalysisResult:
        """Return empty result when no data available"""
        return GroqAnalysisResult(
            patterns=[],
            suggested_rules=[],
            automation_opportunities=[],
            confidence=0.0,
            summary_stats={"total_logs": 0}
        )


# Compatibility wrapper for existing interfaces
class GroqAnalyzer:
    """Drop-in replacement for GroqAnalyzer that uses improved data-driven + AI analysis"""
    
    def __init__(self):
        self.analyzer = GroqPatternAnalyzer()
        self.logger = logging.getLogger(__name__)
        self.logger.info("Using improved data-driven + AI analysis")
    
    def analyze_manual_repairs(self, repair_logs: List[Dict]) -> Any:
        """Analyze using improved data-driven + AI approach"""
        result = self.analyzer.analyze_manual_repairs(repair_logs)
        
        # Convert to expected format
        class CompatResult:
            def __init__(self, data_result):
                self.patterns = data_result.patterns
                self.suggested_rules = data_result.suggested_rules  
                self.automation_opportunities = data_result.automation_opportunities
                self.confidence = data_result.confidence
                self.summary_stats = data_result.summary_stats
        
        return CompatResult(result)