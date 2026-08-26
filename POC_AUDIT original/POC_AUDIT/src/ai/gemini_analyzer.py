"""
Gemini-powered AI analyzer for APS manual repair pattern analysis.
Uses Google's Gemini LLM for sophisticated pattern recognition and rule suggestion.
"""

import json
import logging
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from dataclasses import dataclass
from config.settings import APSConfig


@dataclass
class GeminiAnalysisResult:
    """Result of Gemini analysis"""
    patterns: List[Dict[str, Any]]
    suggested_rules: List[Dict[str, Any]]
    automation_opportunities: List[Dict[str, Any]]
    confidence_score: float
    reasoning: str


class GeminiPatternAnalyzer:
    """
    Advanced pattern analyzer using Google Gemini LLM
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = APSConfig()
        
        # Initialize Gemini if API key is available
        if self.config.USE_GEMINI:
            try:
                genai.configure(api_key=self.config.GEMINI_API_KEY)
                self.model = genai.GenerativeModel(self.config.GEMINI_MODEL)
                self.logger.info("Gemini AI initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Gemini: {e}")
                self.model = None
        else:
            self.logger.warning("Gemini API key not configured, using fallback analysis")
            self.model = None
    
    def analyze_manual_repairs(self, repair_logs: List[Dict]) -> GeminiAnalysisResult:
        """
        Analyze manual repair logs using Gemini for pattern recognition
        
        Args:
            repair_logs: List of manual repair log entries
            
        Returns:
            GeminiAnalysisResult with patterns and suggestions
        """
        if not self.model:
            return self._fallback_analysis(repair_logs)
        
        try:
            # Prepare data for Gemini analysis
            analysis_prompt = self._create_analysis_prompt(repair_logs)
            
            # Generate analysis using Gemini
            response = self.model.generate_content(
                analysis_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.config.GEMINI_TEMPERATURE,
                    max_output_tokens=2048,
                )
            )
            
            # Parse Gemini response
            result = self._parse_gemini_response(response.text)
            
            self.logger.info(f"Gemini analysis completed with confidence: {result.confidence_score}")
            return result
            
        except Exception as e:
            self.logger.error(f"Gemini analysis failed: {e}")
            return self._fallback_analysis(repair_logs)
    
    def _create_analysis_prompt(self, repair_logs: List[Dict]) -> str:
        """Create a detailed prompt for Gemini analysis"""
        
        # Prepare repair data summary
        repair_summary = self._summarize_repairs(repair_logs)
        
        prompt = f"""
You are an expert AI system analyzing banking payment system manual repair patterns. 
Your task is to identify automation opportunities and suggest repair rules.

CONTEXT:
This is an Automatic Payment System (APS) where manual repairs are performed when automatic validation fails.
Each manual repair represents a potential pattern that could be automated.

REPAIR LOG DATA:
{repair_summary}

ANALYSIS TASKS:
1. Identify common patterns in the manual repairs
2. Determine which patterns can be safely automated
3. Suggest specific repair rules for automation
4. Assess automation feasibility and risk

RESPONSE FORMAT (JSON):
{{
  "patterns": [
    {{
      "pattern_type": "string",
      "description": "string", 
      "frequency": "number",
      "examples": ["string"],
      "automation_feasibility": "high|medium|low"
    }}
  ],
  "suggested_rules": [
    {{
      "rule_name": "string",
      "rule_type": "string",
      "condition": "string",
      "action": "string",
      "confidence": "number",
      "risk_level": "low|medium|high"
    }}
  ],
  "automation_opportunities": [
    {{
      "opportunity": "string",
      "impact": "string",
      "implementation_complexity": "string"
    }}
  ],
  "confidence_score": "number (0-1)",
  "reasoning": "string"
}}

Focus on banking compliance, data validation patterns, and safe automation practices.
"""
        return prompt
    
    def _summarize_repairs(self, repair_logs: List[Dict]) -> str:
        """Create a concise summary of repair logs for Gemini"""
        summary = []
        
        for i, log in enumerate(repair_logs[:50]):  # Limit to avoid token limits
            summary.append(f"""
Repair #{i+1}:
- Type: {log.get('log_type', 'Unknown')}
- Clearing: {log.get('clearing_type', 'N/A')}
- Message: {log.get('message_type', 'N/A')}
- Old Account: {log.get('old_account_id', 'N/A')} 
- Old IBAN: {log.get('old_iban', 'N/A')}
- New Account: {log.get('new_account_id', 'N/A')}
- New IBAN: {log.get('new_iban', 'N/A')}
- Change Pattern: {self._analyze_change_pattern(log)}
""")
        
        return "\n".join(summary)
    
    def _analyze_change_pattern(self, log: Dict) -> str:
        """Analyze the type of change made in a repair"""
        old_iban = log.get('old_iban', '')
        new_iban = log.get('new_iban', '')
        
        if not old_iban or not new_iban:
            return "Incomplete data"
        
        if len(old_iban) != len(new_iban):
            return f"Length change ({len(old_iban)} -> {len(new_iban)})"
        
        if old_iban.replace(' ', '') == new_iban.replace(' ', ''):
            return "Spacing correction"
        
        if old_iban[:2] != new_iban[:2]:
            return "Country code change"
        
        return "Content modification"
    
    def _parse_gemini_response(self, response_text: str) -> GeminiAnalysisResult:
        """Parse Gemini's JSON response into structured result"""
        try:
            # Clean response text (remove markdown formatting if present)
            clean_text = response_text.strip()
            if clean_text.startswith('```json'):
                clean_text = clean_text[7:]
            if clean_text.endswith('```'):
                clean_text = clean_text[:-3]
            
            data = json.loads(clean_text)
            
            return GeminiAnalysisResult(
                patterns=data.get('patterns', []),
                suggested_rules=data.get('suggested_rules', []),
                automation_opportunities=data.get('automation_opportunities', []),
                confidence_score=float(data.get('confidence_score', 0.5)),
                reasoning=data.get('reasoning', 'Analysis completed')
            )
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Gemini response: {e}")
            # Fallback to basic analysis
            return self._create_fallback_result()
    
    def _fallback_analysis(self, repair_logs: List[Dict]) -> GeminiAnalysisResult:
        """Fallback analysis when Gemini is not available"""
        self.logger.info("Using fallback analysis (Gemini unavailable)")
        
        # Basic pattern analysis
        patterns = self._basic_pattern_analysis(repair_logs)
        
        return GeminiAnalysisResult(
            patterns=patterns,
            suggested_rules=self._create_basic_rules(patterns),
            automation_opportunities=[
                {
                    "opportunity": "IBAN formatting standardization",
                    "impact": "Reduce manual spacing corrections",
                    "implementation_complexity": "Low"
                }
            ],
            confidence_score=0.6,
            reasoning="Basic pattern analysis (Gemini unavailable)"
        )
    
    def _basic_pattern_analysis(self, repair_logs: List[Dict]) -> List[Dict]:
        """Basic pattern analysis without LLM"""
        pattern_counts = {}
        
        for log in repair_logs:
            pattern = self._analyze_change_pattern(log)
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        patterns = []
        for pattern_type, count in pattern_counts.items():
            if count >= 2:  # Minimum frequency
                patterns.append({
                    "pattern_type": pattern_type,
                    "description": f"Manual repairs involving {pattern_type.lower()}",
                    "frequency": count,
                    "automation_feasibility": "medium" if count > 5 else "low"
                })
        
        return patterns
    
    def _create_basic_rules(self, patterns: List[Dict]) -> List[Dict]:
        """Create basic automation rules from patterns"""
        rules = []
        
        for pattern in patterns:
            if pattern["pattern_type"] == "Spacing correction" and pattern["frequency"] > 3:
                rules.append({
                    "rule_name": "IBAN_SPACING_NORMALIZATION",
                    "rule_type": "formatting",
                    "condition": "IBAN contains spaces",
                    "action": "Remove all spaces from IBAN",
                    "confidence": 0.8,
                    "risk_level": "low"
                })
        
        return rules
    
    def _create_fallback_result(self) -> GeminiAnalysisResult:
        """Create a fallback result when parsing fails"""
        return GeminiAnalysisResult(
            patterns=[],
            suggested_rules=[],
            automation_opportunities=[],
            confidence_score=0.1,
            reasoning="Analysis failed, using empty result"
        )

    def generate_repair_rule_suggestions(self, patterns: List[Dict]) -> List[Dict]:
        """
        Generate specific repair rule suggestions based on identified patterns
        """
        if not self.model:
            return self._create_basic_rules(patterns)
        
        try:
            prompt = f"""
Based on the following payment system repair patterns, generate specific automation rules:

PATTERNS:
{json.dumps(patterns, indent=2)}

Generate detailed repair rules in this JSON format:
{{
  "rules": [
    {{
      "rule_id": "unique_identifier",
      "rule_name": "descriptive_name",
      "priority": "number (1-10)",
      "conditions": [
        {{
          "field": "field_name",
          "operator": "equals|contains|matches|length_is",
          "value": "expected_value"
        }}
      ],
      "actions": [
        {{
          "type": "replace|format|validate|normalize",
          "field": "target_field", 
          "operation": "specific_operation"
        }}
      ],
      "risk_assessment": "low|medium|high",
      "validation_required": "boolean"
    }}
  ]
}}

Focus on safe, reversible operations that maintain data integrity.
"""
            
            response = self.model.generate_content(prompt)
            rules_data = json.loads(response.text.strip())
            return rules_data.get('rules', [])
            
        except Exception as e:
            self.logger.error(f"Rule generation failed: {e}")
            return self._create_basic_rules(patterns)