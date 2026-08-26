"""
AI rule suggester for generating automated repair rules from identified patterns
Enhanced with Gemini LLM capabilities for sophisticated rule generation
"""

import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

from ..models import (
    RepairPattern, SuggestedRule, RepairRule, RuleCondition, RuleAction,
    ClearingType, MessageType, AccountType
)
from .gemini_analyzer import GeminiPatternAnalyzer


class RuleSuggester:
    """AI-powered rule generator for creating automation rules from patterns
    Enhanced with Gemini LLM for sophisticated rule generation"""
    
    def __init__(self):
        self.rule_templates = self._initialize_rule_templates()
        self.gemini_analyzer = GeminiPatternAnalyzer()
    
    def _initialize_rule_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize rule templates for common repair patterns"""
        return {
            "SPACE_FORMATTING": {
                "name_template": "Remove IBAN Spaces - {clearing_type} {message_type}",
                "description_template": "Automatically remove spaces from IBAN formatting for {clearing_type} {message_type} transactions",
                "conditions": [
                    {"field_name": "iban", "operator": "contains", "value": " "},
                    {"field_name": "error_codes", "operator": "contains", "value": "IBAN_INVALID_FORMAT"}
                ],
                "actions": [
                    {"action_type": "transform", "target_field": "iban", "transformation": "remove_spaces"}
                ],
                "risk_level": "LOW",
                "priority": 10
            },
            "CONTENT_CHANGE": {
                "name_template": "IBAN Correction - {clearing_type} {message_type}",
                "description_template": "Common IBAN corrections for {clearing_type} {message_type} transactions",
                "conditions": [
                    {"field_name": "error_codes", "operator": "contains", "value": "IBAN_INVALID_FORMAT"}
                ],
                "actions": [
                    {"action_type": "lookup", "target_field": "iban", "lookup_table": "iban_corrections"}
                ],
                "risk_level": "MEDIUM",
                "priority": 30
            },
            "LENGTH_CHANGE": {
                "name_template": "IBAN Length Fix - {clearing_type} {message_type}",
                "description_template": "Fix IBAN length issues for {clearing_type} {message_type} transactions",
                "conditions": [
                    {"field_name": "error_codes", "operator": "contains", "value": "IBAN_INVALID_LENGTH"}
                ],
                "actions": [
                    {"action_type": "transform", "target_field": "iban", "transformation": "format_iban"}
                ],
                "risk_level": "MEDIUM",
                "priority": 40
            },
            "ACCOUNT_ID_CHANGE": {
                "name_template": "Account ID Validation - {clearing_type} {message_type}",
                "description_template": "Account ID corrections for {clearing_type} {message_type} transactions - REQUIRES REVIEW",
                "conditions": [
                    {"field_name": "error_codes", "operator": "contains", "value": "ACCOUNT_VALIDATION_FAILED"}
                ],
                "actions": [
                    {"action_type": "lookup", "target_field": "account_id", "lookup_table": "account_id_corrections"}
                ],
                "risk_level": "HIGH",
                "priority": 90
            },
            "COUNTRY_CHANGE": {
                "name_template": "Country Code Correction - {clearing_type} {message_type}",
                "description_template": "IBAN country code corrections for {clearing_type} {message_type} - HIGH RISK",
                "conditions": [
                    {"field_name": "error_codes", "operator": "contains", "value": "IBAN_UNSUPPORTED_COUNTRY"}
                ],
                "actions": [
                    {"action_type": "lookup", "target_field": "iban", "lookup_table": "country_corrections"}
                ],
                "risk_level": "HIGH",
                "priority": 95
            }
        }
    
    def suggest_rules_from_patterns(self, patterns: List[RepairPattern]) -> Dict[str, Any]:
        """Generate rule suggestions from identified patterns
        Enhanced with Gemini LLM analysis
        
        Returns:
            Dict containing traditional rules, Gemini-generated rules, and combined recommendations
        """
        # Traditional rule generation
        traditional_rules = self._suggest_traditional_rules(patterns)
        
        # Gemini-enhanced rule generation
        gemini_rules = self._suggest_gemini_rules(patterns)
        
        # Combine and rank all suggestions
        combined_rules = self._combine_rule_suggestions(traditional_rules, gemini_rules)
        
        return {
            "traditional_rules": traditional_rules,
            "gemini_rules": gemini_rules,
            "combined_recommendations": combined_rules,
            "total_suggestions": len(combined_rules)
        }
    
    def _suggest_traditional_rules(self, patterns: List[RepairPattern]) -> List[SuggestedRule]:
        """Generate traditional template-based rule suggestions"""
        suggested_rules = []
        
        for pattern in patterns:
            # Only suggest rules for patterns with sufficient confidence
            if pattern.automation_feasibility >= 0.5:
                rule_suggestion = self._create_rule_suggestion(pattern)
                if rule_suggestion:
                    suggested_rules.append(rule_suggestion)
        
        # Sort by priority (feasibility * frequency)
        suggested_rules.sort(
            key=lambda r: r.confidence_score * r.manual_repair_count, 
            reverse=True
        )
        
        return suggested_rules
    
    def _suggest_gemini_rules(self, patterns: List[RepairPattern]) -> List[Dict[str, Any]]:
        """Generate Gemini LLM-enhanced rule suggestions"""
        try:
            # Convert patterns to Gemini-compatible format
            pattern_data = [self._pattern_to_dict(pattern) for pattern in patterns]
            
            # Use Gemini to generate sophisticated rules
            gemini_rules = self.gemini_analyzer.generate_repair_rule_suggestions(pattern_data)
            
            # Enhance each Gemini rule with traditional analysis
            enhanced_rules = []
            for rule_data in gemini_rules:
                enhanced_rule = self._enhance_gemini_rule(rule_data, patterns)
                if enhanced_rule:
                    enhanced_rules.append(enhanced_rule)
            
            return enhanced_rules
            
        except Exception as e:
            print(f"Gemini rule generation failed: {e}")
            return []
    
    def _pattern_to_dict(self, pattern: RepairPattern) -> Dict[str, Any]:
        """Convert RepairPattern to dictionary for Gemini analysis"""
        return {
            "pattern_type": pattern.pattern_type,
            "occurrence_count": pattern.occurrence_count,
            "automation_feasibility": pattern.automation_feasibility,
            "clearing_type": pattern.clearing_type,
            "message_type": pattern.message_type,
            "example_changes": [
                {
                    "old_iban": log.get("old_iban", ""),
                    "new_iban": log.get("new_iban", ""),
                    "old_account": log.get("old_account_id", ""),
                    "new_account": log.get("new_account_id", "")
                }
                for log in pattern.example_logs[:3]  # Limit examples
            ]
        }
    
    def _enhance_gemini_rule(self, gemini_rule: Dict[str, Any], patterns: List[RepairPattern]) -> Optional[Dict[str, Any]]:
        """Enhance Gemini-generated rule with traditional analysis"""
        try:
            # Find matching pattern for validation
            matching_pattern = None
            for pattern in patterns:
                if self._rule_matches_pattern(gemini_rule, pattern):
                    matching_pattern = pattern
                    break
            
            enhanced_rule = {
                "rule_id": gemini_rule.get("rule_id", f"GEMINI_{uuid.uuid4()}"),
                "rule_name": gemini_rule.get("rule_name", "Gemini Generated Rule"),
                "description": gemini_rule.get("description", ""),
                "priority": gemini_rule.get("priority", 50),
                "conditions": gemini_rule.get("conditions", []),
                "actions": gemini_rule.get("actions", []),
                "risk_assessment": gemini_rule.get("risk_assessment", "medium"),
                "validation_required": gemini_rule.get("validation_required", True),
                "source": "gemini_llm",
                "confidence_score": 0.7,  # Default Gemini confidence
                "supporting_pattern": matching_pattern.pattern_id if matching_pattern else None
            }
            
            # Validate rule structure
            if self._validate_gemini_rule_structure(enhanced_rule):
                return enhanced_rule
            else:
                print(f"Invalid Gemini rule structure: {gemini_rule.get('rule_id', 'unknown')}")
                return None
                
        except Exception as e:
            print(f"Error enhancing Gemini rule: {e}")
            return None
    
    def _rule_matches_pattern(self, rule: Dict[str, Any], pattern: RepairPattern) -> bool:
        """Check if a Gemini rule matches a traditional pattern"""
        rule_name = rule.get("rule_name", "").lower()
        pattern_type = pattern.pattern_type.lower()
        
        # Simple keyword matching
        pattern_keywords = pattern_type.replace('_', ' ').split()
        return any(keyword in rule_name for keyword in pattern_keywords)
    
    def _validate_gemini_rule_structure(self, rule: Dict[str, Any]) -> bool:
        """Validate that a Gemini-generated rule has proper structure"""
        required_fields = ["rule_id", "rule_name", "conditions", "actions"]
        
        for field in required_fields:
            if field not in rule:
                return False
        
        # Validate conditions and actions are lists
        if not isinstance(rule["conditions"], list) or not isinstance(rule["actions"], list):
            return False
        
        return True
    
    def _combine_rule_suggestions(self, traditional_rules: List[SuggestedRule], 
                                gemini_rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Combine traditional and Gemini rule suggestions with ranking"""
        combined_suggestions = []
        
        # Add traditional rules
        for rule in traditional_rules:
            combined_suggestions.append({
                "rule_id": rule.suggested_rule.rule_id,
                "rule_name": rule.suggested_rule.rule_name,
                "source": "traditional",
                "confidence_score": rule.confidence_score,
                "feasibility_score": rule.feasibility_score,
                "risk_level": rule.risk_level,
                "manual_repair_count": rule.manual_repair_count,
                "overall_score": rule.confidence_score * rule.feasibility_score * rule.manual_repair_count,
                "rule_data": rule
            })
        
        # Add Gemini rules
        for rule in gemini_rules:
            combined_suggestions.append({
                "rule_id": rule.get("rule_id"),
                "rule_name": rule.get("rule_name"),
                "source": "gemini",
                "confidence_score": rule.get("confidence_score", 0.7),
                "risk_assessment": rule.get("risk_assessment", "medium"),
                "overall_score": rule.get("confidence_score", 0.7) * 10,  # Boost Gemini rules
                "rule_data": rule
            })
        
        # Sort by overall score
        combined_suggestions.sort(key=lambda x: x["overall_score"], reverse=True)
        
        return combined_suggestions
    
    def _create_rule_suggestion(self, pattern: RepairPattern) -> Optional[SuggestedRule]:
        """Create a rule suggestion from a single pattern"""
        try:
            # Get rule template for this pattern type
            template = self.rule_templates.get(pattern.pattern_type)
            if not template:
                template = self._create_generic_template(pattern)
            
            # Generate rule from template
            repair_rule = self._generate_rule_from_template(pattern, template)
            
            # Calculate confidence and risk scores
            confidence_score = self._calculate_confidence_score(pattern)
            feasibility_score = pattern.automation_feasibility
            risk_level = self._determine_risk_level(pattern, template)
            
            suggestion = SuggestedRule(
                suggestion_id=str(uuid.uuid4()),
                suggested_rule=repair_rule,
                confidence_score=confidence_score,
                pattern_frequency=pattern.occurrence_count,
                manual_repair_count=pattern.occurrence_count,
                supporting_cases=pattern.example_logs,
                feasibility_score=feasibility_score,
                risk_level=risk_level
            )
            
            return suggestion
            
        except Exception as e:
            print(f"Error creating rule suggestion for pattern {pattern.pattern_id}: {e}")
            return None
    
    def _generate_rule_from_template(self, pattern: RepairPattern, template: Dict[str, Any]) -> RepairRule:
        """Generate a RepairRule from a template and pattern"""
        # Format template strings with pattern data
        rule_name = template["name_template"].format(
            clearing_type=pattern.clearing_type,
            message_type=pattern.message_type
        )
        
        description = template["description_template"].format(
            clearing_type=pattern.clearing_type,
            message_type=pattern.message_type
        )
        
        # Create conditions
        conditions = []
        for condition_template in template.get("conditions", []):
            condition = RuleCondition(**condition_template)
            conditions.append(condition)
        
        # Add pattern-specific conditions
        if pattern.clearing_type:
            conditions.append(RuleCondition(
                field_name="clearing_type",
                operator="eq",
                value=pattern.clearing_type
            ))
        
        if pattern.message_type:
            conditions.append(RuleCondition(
                field_name="message_type",
                operator="eq",
                value=pattern.message_type
            ))
        
        # Create actions
        actions = []
        for action_template in template.get("actions", []):
            action = RuleAction(**action_template)
            actions.append(action)
        
        # Determine account types
        account_types = self._determine_account_types(pattern)
        
        repair_rule = RepairRule(
            rule_id=f"RULE_{pattern.pattern_id}",
            rule_name=rule_name,
            description=description,
            clearing_types=[pattern.clearing_type] if pattern.clearing_type else [],
            message_types=[pattern.message_type] if pattern.message_type else [],
            account_types=account_types,
            conditions=conditions,
            actions=actions,
            priority=template.get("priority", 50),
            created_by="AI_RULE_SUGGESTER"
        )
        
        return repair_rule
    
    def _create_generic_template(self, pattern: RepairPattern) -> Dict[str, Any]:
        """Create a generic template for unknown pattern types"""
        return {
            "name_template": f"Generic Rule - {pattern.pattern_type}",
            "description_template": f"Automated rule for {pattern.pattern_type} pattern",
            "conditions": [
                {"field_name": "error_codes", "operator": "contains", "value": "VALIDATION_FAILED"}
            ],
            "actions": [
                {"action_type": "transform", "target_field": "iban", "transformation": "format_iban"}
            ],
            "risk_level": "HIGH",
            "priority": 80
        }
    
    def _calculate_confidence_score(self, pattern: RepairPattern) -> float:
        """Calculate confidence score for the rule suggestion"""
        # Base confidence on pattern characteristics
        frequency_factor = min(pattern.occurrence_count / 10, 1.0)
        user_diversity_factor = min(pattern.unique_users / 3, 1.0)
        automation_factor = pattern.automation_feasibility
        
        confidence = (frequency_factor + user_diversity_factor + automation_factor) / 3
        
        # Boost confidence for well-known safe patterns
        if pattern.pattern_type == "SPACE_FORMATTING":
            confidence = min(confidence * 1.2, 1.0)
        
        # Reduce confidence for risky patterns
        if pattern.pattern_type in ["COUNTRY_CHANGE", "ACCOUNT_ID_CHANGE"]:
            confidence *= 0.8
        
        return confidence
    
    def _determine_risk_level(self, pattern: RepairPattern, template: Dict[str, Any]) -> str:
        """Determine risk level for the automation rule"""
        base_risk = template.get("risk_level", "MEDIUM")
        
        # Increase risk for high-value transactions
        if pattern.clearing_type == ClearingType.HIGH_VALUE:
            if base_risk == "LOW":
                return "MEDIUM"
            elif base_risk == "MEDIUM":
                return "HIGH"
        
        # Increase risk for international transactions
        if pattern.clearing_type == ClearingType.INTERNATIONAL:
            if base_risk == "LOW":
                return "MEDIUM"
        
        # Reduce risk for very common, simple patterns
        if (pattern.pattern_type == "SPACE_FORMATTING" and 
            pattern.occurrence_count > 20 and 
            pattern.automation_feasibility > 0.9):
            return "LOW"
        
        return base_risk
    
    def _determine_account_types(self, pattern: RepairPattern) -> List[AccountType]:
        """Determine which account types the rule should apply to"""
        # In a real system, this would analyze the pattern data
        # For POC, return both types unless specific patterns suggest otherwise
        
        if "debitor" in pattern.pattern_description.lower():
            return [AccountType.DEBITOR]
        elif "creditor" in pattern.pattern_description.lower():
            return [AccountType.CREDITOR]
        else:
            return [AccountType.DEBITOR, AccountType.CREDITOR]
    
    def prioritize_suggestions(self, suggestions: List[SuggestedRule]) -> List[SuggestedRule]:
        """Prioritize rule suggestions based on impact and risk"""
        def priority_score(suggestion: SuggestedRule) -> Tuple[int, float]:
            # Primary sort: risk level (lower risk first)
            risk_priority = {
                "LOW": 1,
                "MEDIUM": 2, 
                "HIGH": 3
            }.get(suggestion.risk_level, 3)
            
            # Secondary sort: impact (confidence * frequency)
            impact_score = suggestion.confidence_score * suggestion.manual_repair_count
            
            return (risk_priority, -impact_score)  # Negative for descending order
        
        return sorted(suggestions, key=priority_score)
    
    def generate_implementation_plan(self, suggestions: List[SuggestedRule]) -> Dict[str, Any]:
        """Generate an implementation plan for rule suggestions"""
        low_risk = [s for s in suggestions if s.risk_level == "LOW"]
        medium_risk = [s for s in suggestions if s.risk_level == "MEDIUM"]
        high_risk = [s for s in suggestions if s.risk_level == "HIGH"]
        
        total_automatable = sum(s.manual_repair_count for s in suggestions)
        immediate_automatable = sum(s.manual_repair_count for s in low_risk)
        
        plan = {
            "summary": {
                "total_suggestions": len(suggestions),
                "low_risk_suggestions": len(low_risk),
                "medium_risk_suggestions": len(medium_risk),
                "high_risk_suggestions": len(high_risk),
                "total_automatable_repairs": total_automatable,
                "immediate_automation_potential": immediate_automatable
            },
            "implementation_phases": {
                "phase_1_immediate": {
                    "description": "Implement low-risk, high-confidence rules immediately",
                    "rules": [
                        {
                            "rule_id": s.suggested_rule.rule_id,
                            "rule_name": s.suggested_rule.rule_name,
                            "confidence": s.confidence_score,
                            "automation_count": s.manual_repair_count,
                            "risk": s.risk_level
                        } for s in low_risk[:5]
                    ],
                    "estimated_automation_percentage": round(
                        (immediate_automatable / total_automatable * 100) if total_automatable > 0 else 0, 2
                    )
                },
                "phase_2_review": {
                    "description": "Review and test medium-risk rules in staging environment",
                    "rules": [
                        {
                            "rule_id": s.suggested_rule.rule_id,
                            "rule_name": s.suggested_rule.rule_name,
                            "confidence": s.confidence_score,
                            "automation_count": s.manual_repair_count,
                            "risk": s.risk_level,
                            "review_requirements": "Staging environment testing, manual verification"
                        } for s in medium_risk
                    ]
                },
                "phase_3_careful": {
                    "description": "Carefully evaluate high-risk rules with extensive testing",
                    "rules": [
                        {
                            "rule_id": s.suggested_rule.rule_id,
                            "rule_name": s.suggested_rule.rule_name,
                            "confidence": s.confidence_score,
                            "automation_count": s.manual_repair_count,
                            "risk": s.risk_level,
                            "review_requirements": "Extensive testing, business approval, gradual rollout"
                        } for s in high_risk
                    ]
                }
            },
            "recommendations": self._generate_implementation_recommendations(suggestions),
            "success_metrics": [
                "Reduction in manual repair volume",
                "Improvement in transaction processing time",
                "Decrease in validation failure rates",
                "User satisfaction with automated repairs"
            ]
        }
        
        return plan
    
    def _generate_implementation_recommendations(self, suggestions: List[SuggestedRule]) -> List[str]:
        """Generate specific implementation recommendations"""
        recommendations = []
        
        low_risk_count = len([s for s in suggestions if s.risk_level == "LOW"])
        if low_risk_count > 0:
            recommendations.append(
                f"Start with {low_risk_count} low-risk rules for immediate impact"
            )
        
        space_formatting_rules = [
            s for s in suggestions 
            if "space" in s.suggested_rule.rule_name.lower()
        ]
        if space_formatting_rules:
            recommendations.append("IBAN space formatting rules have highest success probability")
        
        high_frequency_rules = [s for s in suggestions if s.manual_repair_count >= 10]
        if high_frequency_rules:
            recommendations.append(
                f"Focus on {len(high_frequency_rules)} high-frequency patterns for maximum efficiency gains"
            )
        
        international_rules = [
            s for s in suggestions 
            if ClearingType.INTERNATIONAL in s.suggested_rule.clearing_types
        ]
        if international_rules:
            recommendations.append(
                "International transaction rules require extra validation due to regulatory compliance"
            )
        
        recommendations.extend([
            "Implement A/B testing for new rules to measure effectiveness",
            "Set up monitoring for rule performance and false positive rates", 
            "Create fallback mechanisms for rule failures",
            "Establish regular review cycles for rule optimization"
        ])
        
        return recommendations
    
    def export_rules_for_implementation(self, suggestions: List[SuggestedRule]) -> str:
        """Export rule suggestions in format ready for implementation"""
        implementation_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_suggestions": len(suggestions),
            "rules": []
        }
        
        for suggestion in suggestions:
            rule_data = {
                "suggestion_id": suggestion.suggestion_id,
                "rule": suggestion.suggested_rule.dict(),
                "metadata": {
                    "confidence_score": suggestion.confidence_score,
                    "feasibility_score": suggestion.feasibility_score,
                    "risk_level": suggestion.risk_level,
                    "manual_repair_count": suggestion.manual_repair_count,
                    "supporting_cases": suggestion.supporting_cases
                },
                "implementation_priority": self._calculate_implementation_priority(suggestion)
            }
            implementation_data["rules"].append(rule_data)
        
        import json
        return json.dumps(implementation_data, indent=2, default=str)
    
    def _calculate_implementation_priority(self, suggestion: SuggestedRule) -> int:
        """Calculate implementation priority (1 = highest priority)"""
        risk_weight = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}[suggestion.risk_level]
        impact_score = suggestion.confidence_score * suggestion.manual_repair_count
        
        # Lower risk and higher impact = higher priority (lower number)
        priority = risk_weight * (1 / max(impact_score, 0.1))
        
        return min(int(priority * 10), 100)  # Scale to 1-100