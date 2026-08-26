"""
Data-Driven Analyzer for APS Manual Repair Logs
Provides accurate analysis based on actual data patterns instead of AI hallucination
"""

import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from collections import Counter, defaultdict
import re


@dataclass
class DataDrivenAnalysisResult:
    """Result of data-driven analysis"""
    patterns: List[Dict[str, Any]]
    suggested_rules: List[Dict[str, Any]]
    automation_opportunities: List[Dict[str, Any]]
    confidence: float
    summary_stats: Dict[str, Any]


class DataDrivenAnalyzer:
    """
    Analyzer that performs real pattern analysis on actual data
    No AI hallucination - only data-based conclusions
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Data-driven analyzer initialized - no AI hallucination")
    
    def analyze_manual_repairs(self, repair_logs: List[Dict]) -> DataDrivenAnalysisResult:
        """
        Analyze manual repair logs using pure data analysis
        
        Args:
            repair_logs: List of manual repair log dictionaries
            
        Returns:
            DataDrivenAnalysisResult with patterns based on actual data
        """
        if not repair_logs:
            return self._empty_result()
        
        # Extract actual data statistics
        stats = self._calculate_statistics(repair_logs)
        
        # Detect real patterns in the data
        patterns = self._detect_real_patterns(repair_logs, stats)
        
        # Generate data-based automation rules
        rules = self._generate_data_based_rules(repair_logs, patterns)
        
        # Calculate real automation opportunities
        opportunities = self._calculate_automation_opportunities(repair_logs, patterns)
        
        # Calculate confidence based on data consistency
        confidence = self._calculate_data_confidence(patterns, len(repair_logs))
        
        return DataDrivenAnalysisResult(
            patterns=patterns,
            suggested_rules=rules,
            automation_opportunities=opportunities,
            confidence=confidence,
            summary_stats=stats
        )
    
    def _calculate_statistics(self, repair_logs: List[Dict]) -> Dict[str, Any]:
        """Calculate real statistics from the data"""
        
        # Count actual clearing types
        clearing_types = Counter(log.get("clearing_type", "UNKNOWN") for log in repair_logs)
        
        # Count actual message types  
        message_types = Counter(log.get("message_type", "UNKNOWN") for log in repair_logs)
        
        # Count actual log types
        log_types = Counter(log.get("log_type", "UNKNOWN") for log in repair_logs)
        
        # Analyze actual account ID changes
        account_changes = []
        iban_changes = []
        
        for log in repair_logs:
            # Handle both field name formats
            old_acc = str(log.get("oldAccount", log.get("old_account_id", "")))
            new_acc = str(log.get("newAccount", log.get("new_account_id", "")))
            old_iban = log.get("old_iban", "")
            new_iban = log.get("new_iban", "")
            
            if old_acc != new_acc:
                account_changes.append({
                    "old": old_acc,
                    "new": new_acc,
                    "change_type": self._detect_account_change_type(old_acc, new_acc)
                })
            
            if old_iban != new_iban:
                iban_changes.append({
                    "old": old_iban,
                    "new": new_iban,
                    "change_type": self._detect_iban_change_type(old_iban, new_iban)
                })
        
        return {
            "total_logs": len(repair_logs),
            "clearing_types": dict(clearing_types),
            "message_types": dict(message_types),
            "log_types": dict(log_types),
            "account_changes": account_changes,
            "iban_changes": iban_changes,
            "most_common_clearing": clearing_types.most_common(1)[0] if clearing_types else ("UNKNOWN", 0),
            "most_common_message": message_types.most_common(1)[0] if message_types else ("UNKNOWN", 0)
        }
    
    def _detect_account_change_type(self, old_acc: str, new_acc: str) -> str:
        """Detect the type of account change"""
        # Skip empty accounts
        old_acc = old_acc.strip()
        new_acc = new_acc.strip()
        
        if not old_acc or not new_acc:
            return "empty_field"
        
        # Check if new account is old account with prefix
        if new_acc.endswith(old_acc) and len(new_acc) > len(old_acc):
            prefix = new_acc[:-len(old_acc)]
            return f"prefix_addition_{prefix}"
        
        # Check if old account is new account with prefix  
        if old_acc.endswith(new_acc) and len(old_acc) > len(new_acc):
            prefix = old_acc[:-len(new_acc)]
            return f"prefix_removal_{prefix}"
        
        # Check for character replacement
        if len(old_acc) == len(new_acc):
            return "character_replacement"
        
        return "complete_replacement"
    
    def _detect_iban_change_type(self, old_iban: str, new_iban: str) -> str:
        """Detect the type of IBAN change"""
        if not old_iban and not new_iban:
            return "both_empty"
        
        if not old_iban or not new_iban:
            return "one_empty"
        
        # Remove spaces and compare
        old_clean = old_iban.replace(" ", "")
        new_clean = new_iban.replace(" ", "")
        
        if old_clean == new_clean:
            return "space_formatting"
        
        # Check for hyphen removal
        old_no_hyphen = old_iban.replace("-", "")
        new_no_hyphen = new_iban.replace("-", "")
        
        if old_no_hyphen == new_no_hyphen and "-" in old_iban and "-" not in new_iban:
            return "hyphen_removal"
        
        return "content_change"
    
    def _detect_real_patterns(self, repair_logs: List[Dict], stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect actual patterns in the data"""
        patterns = []
        
        # Analyze account ID patterns
        account_change_types = Counter(change["change_type"] for change in stats["account_changes"])
        for change_type, frequency in account_change_types.items():
            if frequency >= 2:  # Pattern if occurs 2+ times
                patterns.append({
                    "type": f"ACCOUNT_{change_type.upper()}",
                    "frequency": frequency,
                    "description": f"Account ID {change_type.replace('_', ' ')}: {frequency} occurrences",
                    "category": "account_modification",
                    "automation_potential": "HIGH" if frequency > len(repair_logs) * 0.5 else "MEDIUM"
                })
        
        # Analyze IBAN patterns
        iban_change_types = Counter(change["change_type"] for change in stats["iban_changes"])
        for change_type, frequency in iban_change_types.items():
            if frequency >= 2:  # Pattern if occurs 2+ times
                patterns.append({
                    "type": f"IBAN_{change_type.upper()}",
                    "frequency": frequency,  
                    "description": f"IBAN {change_type.replace('_', ' ')}: {frequency} occurrences",
                    "category": "iban_modification",
                    "automation_potential": "HIGH" if frequency > len(repair_logs) * 0.5 else "MEDIUM"
                })
        
        # Banking context pattern (based on actual data)
        clearing_type = stats["most_common_clearing"][0]
        message_type = stats["most_common_message"][0]
        
        if clearing_type != "UNKNOWN" and message_type != "UNKNOWN":
            patterns.append({
                "type": "BANKING_CONTEXT",
                "frequency": stats["most_common_clearing"][1],
                "description": f"{clearing_type} {message_type} transactions show consistent patterns",
                "category": "banking_system",
                "automation_potential": "HIGH"
            })
        
        return patterns
    
    def _generate_data_based_rules(self, repair_logs: List[Dict], patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate automation rules based on actual data patterns"""
        rules = []
        
        for pattern in patterns:
            if pattern["automation_potential"] == "HIGH":
                
                if pattern["category"] == "account_modification":
                    # Extract the specific change pattern
                    pattern_type = pattern["type"].replace("ACCOUNT_", "").lower()
                    
                    if "prefix_addition" in pattern_type:
                        prefix = pattern_type.split("_")[-1]
                        rules.append({
                            "rule_type": "ACCOUNT_PREFIX_ADDITION",
                            "condition": {
                                "clearing_type": repair_logs[0].get("clearing_type"),
                                "message_type": repair_logs[0].get("message_type"),
                                "account_pattern": f"missing_prefix_{prefix}"
                            },
                            "action": {
                                "type": "add_prefix", 
                                "prefix": prefix
                            },
                            "confidence": 90,
                            "risk_level": "LOW",
                            "reason": f"Detected {pattern['frequency']} cases of {prefix} prefix addition"
                        })
                
                elif pattern["category"] == "iban_modification":
                    pattern_type = pattern["type"].replace("IBAN_", "").lower()
                    
                    if "hyphen_removal" in pattern_type:
                        rules.append({
                            "rule_type": "IBAN_HYPHEN_REMOVAL",
                            "condition": {
                                "clearing_type": repair_logs[0].get("clearing_type"),
                                "iban_pattern": "contains_hyphen"
                            },
                            "action": {
                                "type": "remove_character",
                                "character": "-"
                            },
                            "confidence": 95,
                            "risk_level": "LOW",
                            "reason": f"Detected {pattern['frequency']} cases of hyphen removal"
                        })
        
        return rules
    
    def _calculate_automation_opportunities(self, repair_logs: List[Dict], patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate real automation opportunities based on data"""
        
        # Count only valid logs (exclude empty entries)
        valid_logs = [log for log in repair_logs if 
                     str(log.get('oldAccount', log.get('old_account_id', ''))).strip() and 
                     str(log.get('newAccount', log.get('new_account_id', ''))).strip()]
        
        if not valid_logs:
            return []
        
        # Count automatable vs manual patterns
        high_automation_patterns = [p for p in patterns if p["automation_potential"] == "HIGH"]
        automatable_logs = sum(p["frequency"] for p in high_automation_patterns)
        
        # Use valid logs count instead of all repair logs
        automation_rate = (automatable_logs / len(valid_logs)) * 100 if valid_logs else 0
        
        opportunities = []
        
        if automation_rate > 80:
            opportunities.append({
                "opportunity": "High-frequency pattern automation",
                "automation_rate": f"{automation_rate:.0f}%",
                "complexity": "LOW",
                "implementation": "Rule-based automation for detected patterns"
            })
        
        # Specific opportunities based on actual patterns
        for pattern in high_automation_patterns:
            if pattern["category"] == "account_modification":
                opportunities.append({
                    "opportunity": f"Automate {pattern['type'].lower().replace('_', ' ')}",
                    "automation_rate": f"{(pattern['frequency'] / len(valid_logs) * 100):.0f}%",
                    "complexity": "LOW", 
                    "implementation": f"Pattern occurs {pattern['frequency']} times - safe to automate"
                })
        
        return opportunities
    
    def _calculate_data_confidence(self, patterns: List[Dict[str, Any]], total_logs: int) -> float:
        """Calculate confidence based on data consistency"""
        if not patterns or total_logs == 0:
            return 0.0
        
        # Count only valid logs for confidence calculation
        valid_logs = [log for log in self.logs if 
                     str(log.get('oldAccount', log.get('old_account_id', ''))).strip() and 
                     str(log.get('newAccount', log.get('new_account_id', ''))).strip()]
        valid_count = len(valid_logs)
        
        if valid_count == 0:
            return 0.0
        
        # High confidence if patterns cover most of the valid data
        pattern_coverage = sum(p["frequency"] for p in patterns) / valid_count
        
        # Boost confidence for consistent patterns
        high_freq_patterns = len([p for p in patterns if p["frequency"] > valid_count * 0.1])
        consistency_boost = min(high_freq_patterns / len(patterns), 1.0) if patterns else 0.0
        
        return min((pattern_coverage * 0.7 + consistency_boost * 0.3) * 100, 95.0)
    
    def _empty_result(self) -> DataDrivenAnalysisResult:
        """Return empty result when no data available"""
        return DataDrivenAnalysisResult(
            patterns=[],
            suggested_rules=[],
            automation_opportunities=[],
            confidence=0.0,
            summary_stats={"total_logs": 0}
        )


# Compatibility wrapper for existing interfaces
class GroqAnalyzer:
    """Drop-in replacement for GroqAnalyzer that uses data-driven analysis"""
    
    def __init__(self):
        self.analyzer = DataDrivenAnalyzer()
        self.logger = logging.getLogger(__name__)
        self.logger.info("Using data-driven analysis instead of Groq AI")
    
    def analyze_manual_repairs(self, repair_logs: List[Dict]) -> Any:
        """Analyze using data-driven approach"""
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