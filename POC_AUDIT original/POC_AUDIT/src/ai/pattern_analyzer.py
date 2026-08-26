"""
AI pattern analyzer for identifying automation opportunities in manual repair logs
Enhanced with Gemini LLM capabilities
"""

import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
import json

from ..models import (
    ManualRepairAuditLog, RepairPattern, SuggestedRule, RepairRule,
    RuleCondition, RuleAction, ClearingType, MessageType, AccountType
)
from ..logging.audit_logger import AuditLogger
from .gemini_analyzer import GeminiPatternAnalyzer, GeminiAnalysisResult


class PatternAnalyzer:
    """AI-powered analyzer for identifying patterns in manual repair logs
    Enhanced with Gemini LLM capabilities"""
    
    def __init__(self, audit_logger: AuditLogger):
        self.audit_logger = audit_logger
        self.vectorizer = TfidfVectorizer(max_features=100)
        self.scaler = StandardScaler()
        
        # Initialize Gemini analyzer
        self.gemini_analyzer = GeminiPatternAnalyzer()
        
        # Pattern recognition thresholds
        self.min_pattern_frequency = 3
        self.min_automation_score = 0.6
        self.clustering_eps = 0.3
        self.min_samples = 2
    
    def analyze_patterns(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Analyze manual repair logs to identify automation patterns
        Enhanced with Gemini LLM analysis
        
        Args:
            days_back: Number of days to look back for analysis
            
        Returns:
            Dict containing traditional ML patterns, Gemini insights, and combined analysis
        """
        # Get recent logs
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        logs = self.audit_logger.get_logs_by_date_range(start_date, end_date)
        
        if len(logs) < self.min_pattern_frequency:
            return {
                "traditional_patterns": [],
                "gemini_analysis": None,
                "combined_insights": [],
                "status": "insufficient_data"
            }
        
        # Traditional ML analysis
        traditional_patterns = self._traditional_ml_analysis(logs)
        
        # Gemini LLM analysis
        gemini_analysis = self._gemini_enhanced_analysis(logs)
        
        # Combine insights from both approaches
        combined_insights = self._combine_analysis_results(traditional_patterns, gemini_analysis)
        
        return {
            "traditional_patterns": traditional_patterns,
            "gemini_analysis": gemini_analysis,
            "combined_insights": combined_insights,
            "status": "success",
            "logs_analyzed": len(logs)
        }
    
    def _traditional_ml_analysis(self, logs: List[ManualRepairAuditLog]) -> List[RepairPattern]:
        """Perform traditional ML-based pattern analysis"""
        # Convert logs to dataframe for analysis
        df = self._logs_to_dataframe(logs)
        
        # Feature engineering
        features = self._extract_features(df)
        
        # Clustering to identify similar patterns
        clusters = self._cluster_repairs(features)
        
        # Analyze each cluster for automation potential
        patterns = self._analyze_clusters(df, clusters, logs)
        
        return patterns
    
    def _gemini_enhanced_analysis(self, logs: List[ManualRepairAuditLog]) -> Optional[GeminiAnalysisResult]:
        """Perform Gemini LLM enhanced analysis"""
        try:
            # Convert logs to dictionary format for Gemini
            log_dicts = [self._log_to_dict(log) for log in logs]
            
            # Run Gemini analysis
            gemini_result = self.gemini_analyzer.analyze_manual_repairs(log_dicts)
            
            return gemini_result
            
        except Exception as e:
            print(f"Gemini analysis failed: {e}")
            return None
    
    def _log_to_dict(self, log: ManualRepairAuditLog) -> Dict[str, Any]:
        """Convert ManualRepairAuditLog to dictionary for Gemini analysis"""
        return {
            "log_type": log.log_type,
            "clearing_type": log.clearing_type,
            "message_type": log.message_type,
            "old_account_id": log.old_account_id,
            "old_iban": log.old_iban,
            "new_account_id": log.new_account_id,
            "new_iban": log.new_iban,
            "repaired_by": log.repaired_by,
            "repair_timestamp": log.repair_timestamp.isoformat(),
            "validation_errors": log.validation_errors or []
        }
    
    def _combine_analysis_results(self, traditional_patterns: List[RepairPattern], 
                                gemini_analysis: Optional[GeminiAnalysisResult]) -> List[Dict[str, Any]]:
        """Combine traditional ML and Gemini analysis results"""
        combined_insights = []
        
        # Add traditional patterns with enhancement from Gemini
        for pattern in traditional_patterns:
            insight = {
                "pattern_id": pattern.pattern_id,
                "pattern_type": pattern.pattern_type,
                "occurrence_count": pattern.occurrence_count,
                "automation_feasibility": pattern.automation_feasibility,
                "source": "traditional_ml",
                "enhanced_by_gemini": False
            }
            
            # Try to enhance with Gemini insights
            if gemini_analysis:
                for gemini_pattern in gemini_analysis.patterns:
                    if self._patterns_match(pattern.pattern_type, gemini_pattern.get("pattern_type", "")):
                        insight.update({
                            "gemini_description": gemini_pattern.get("description", ""),
                            "gemini_feasibility": gemini_pattern.get("automation_feasibility", ""),
                            "enhanced_by_gemini": True,
                            "gemini_confidence": gemini_analysis.confidence_score
                        })
                        break
            
            combined_insights.append(insight)
        
        # Add Gemini-only insights
        if gemini_analysis:
            for gemini_pattern in gemini_analysis.patterns:
                if not any(self._patterns_match(p.pattern_type, gemini_pattern.get("pattern_type", "")) 
                          for p in traditional_patterns):
                    combined_insights.append({
                        "pattern_type": gemini_pattern.get("pattern_type", ""),
                        "description": gemini_pattern.get("description", ""),
                        "frequency": gemini_pattern.get("frequency", 0),
                        "automation_feasibility": gemini_pattern.get("automation_feasibility", ""),
                        "source": "gemini_only",
                        "gemini_confidence": gemini_analysis.confidence_score
                    })
        
        return combined_insights
    
    def _patterns_match(self, pattern1: str, pattern2: str) -> bool:
        """Check if two pattern types are similar"""
        pattern1_lower = pattern1.lower()
        pattern2_lower = pattern2.lower()
        
        # Simple keyword matching
        keywords1 = set(pattern1_lower.split('_'))
        keywords2 = set(pattern2_lower.split())
        
        return len(keywords1.intersection(keywords2)) > 0
    
    def _logs_to_dataframe(self, logs: List[ManualRepairAuditLog]) -> pd.DataFrame:
        """Convert audit logs to pandas DataFrame for analysis"""
        data = []
        
        for log in logs:
            # Extract change characteristics
            iban_changed = log.old_iban != log.new_iban
            account_id_changed = log.old_account_id != log.new_account_id
            
            # Analyze change type
            change_type = self._classify_change_type(log)
            
            # Calculate change magnitude
            change_magnitude = self._calculate_change_magnitude(log)
            
            # Time features
            hour_of_day = log.repair_timestamp.hour
            day_of_week = log.repair_timestamp.weekday()
            
            data.append({
                'log_id': log.log_id,
                'clearing_type': log.clearing_type,
                'message_type': log.message_type,
                'log_type': log.log_type,
                'iban_changed': iban_changed,
                'account_id_changed': account_id_changed,
                'change_type': change_type,
                'change_magnitude': change_magnitude,
                'hour_of_day': hour_of_day,
                'day_of_week': day_of_week,
                'repaired_by': log.repaired_by,
                'auto_repair_attempts': log.auto_repair_attempts,
                'validation_errors': ','.join(log.validation_errors or []),
                'old_iban_length': len(log.old_iban),
                'new_iban_length': len(log.new_iban),
                'iban_country': log.old_iban[:2] if len(log.old_iban) >= 2 else '',
            })
        
        return pd.DataFrame(data)
    
    def _classify_change_type(self, log: ManualRepairAuditLog) -> str:
        """Classify the type of change made in the repair"""
        old_iban = log.old_iban.replace(' ', '')
        new_iban = log.new_iban.replace(' ', '')
        
        if old_iban == new_iban and log.old_iban != log.new_iban:
            return "SPACE_FORMATTING"
        elif len(old_iban) != len(new_iban):
            return "LENGTH_CHANGE"
        elif old_iban[:2] != new_iban[:2]:
            return "COUNTRY_CHANGE"
        elif old_iban != new_iban:
            return "CONTENT_CHANGE"
        elif log.old_account_id != log.new_account_id:
            return "ACCOUNT_ID_CHANGE"
        else:
            return "UNKNOWN"
    
    def _calculate_change_magnitude(self, log: ManualRepairAuditLog) -> float:
        """Calculate magnitude of change (0-1 scale)"""
        # Simple character-based similarity score
        old_text = f"{log.old_iban}{log.old_account_id}"
        new_text = f"{log.new_iban}{log.new_account_id}"
        
        if not old_text or not new_text:
            return 1.0
        
        # Calculate character-level differences
        max_len = max(len(old_text), len(new_text))
        differences = sum(c1 != c2 for c1, c2 in zip(old_text, new_text))
        differences += abs(len(old_text) - len(new_text))
        
        return differences / max_len if max_len > 0 else 0.0
    
    def _extract_features(self, df: pd.DataFrame) -> np.ndarray:
        """Extract numerical features for clustering"""
        # Categorical encodings
        categorical_features = pd.get_dummies(df[['clearing_type', 'message_type', 'change_type', 'iban_country']])
        
        # Numerical features
        numerical_features = df[['change_magnitude', 'hour_of_day', 'day_of_week', 
                               'auto_repair_attempts', 'old_iban_length', 'new_iban_length']].fillna(0)
        
        # Binary features
        binary_features = df[['iban_changed', 'account_id_changed']].astype(int)
        
        # Combine all features
        all_features = pd.concat([numerical_features, binary_features, categorical_features], axis=1)
        
        # Scale features
        return self.scaler.fit_transform(all_features.fillna(0))
    
    def _cluster_repairs(self, features: np.ndarray) -> np.ndarray:
        """Cluster similar repair patterns using DBSCAN"""
        clusterer = DBSCAN(eps=self.clustering_eps, min_samples=self.min_samples)
        clusters = clusterer.fit_predict(features)
        return clusters
    
    def _analyze_clusters(self, df: pd.DataFrame, clusters: np.ndarray, 
                         logs: List[ManualRepairAuditLog]) -> List[RepairPattern]:
        """Analyze each cluster for automation potential"""
        patterns = []
        
        # Add cluster labels to dataframe
        df_clustered = df.copy()
        df_clustered['cluster'] = clusters
        
        # Analyze each cluster
        for cluster_id in set(clusters):
            if cluster_id == -1:  # Skip noise points
                continue
                
            cluster_logs = df_clustered[df_clustered['cluster'] == cluster_id]
            
            if len(cluster_logs) >= self.min_pattern_frequency:
                pattern = self._analyze_single_cluster(cluster_logs, logs)
                if pattern and pattern.automation_feasibility >= self.min_automation_score:
                    patterns.append(pattern)
        
        # Sort by automation potential
        patterns.sort(key=lambda p: (p.automation_feasibility * p.occurrence_count), reverse=True)
        return patterns
    
    def _analyze_single_cluster(self, cluster_data: pd.DataFrame, 
                              all_logs: List[ManualRepairAuditLog]) -> Optional[RepairPattern]:
        """Analyze a single cluster for automation opportunity"""
        # Get cluster characteristics
        dominant_clearing_type = cluster_data['clearing_type'].mode().iloc[0]
        dominant_message_type = cluster_data['message_type'].mode().iloc[0]
        dominant_change_type = cluster_data['change_type'].mode().iloc[0]
        
        # Calculate automation metrics
        occurrence_count = len(cluster_data)
        unique_users = cluster_data['repaired_by'].nunique()
        
        # Feasibility scoring
        consistency_score = self._calculate_consistency_score(cluster_data)
        complexity_score = self._calculate_complexity_score(cluster_data)
        risk_score = self._calculate_risk_score(cluster_data)
        
        automation_feasibility = (consistency_score + (1 - complexity_score) + (1 - risk_score)) / 3
        
        # Confidence scoring
        frequency_score = min(occurrence_count / 10, 1.0)
        user_diversity_score = min(unique_users / 3, 1.0)
        automation_confidence = (frequency_score + user_diversity_score + consistency_score) / 3
        
        # Get example log IDs
        example_log_ids = cluster_data['log_id'].head(5).tolist()
        
        # Generate pattern description and rule suggestion
        pattern_description = self._generate_cluster_description(cluster_data, dominant_change_type)
        rule_suggestion = self._suggest_automation_rule(cluster_data)
        
        return RepairPattern(
            pattern_id=f"CLUSTER_{hash(dominant_change_type + dominant_clearing_type) % 10000:04d}",
            pattern_type=dominant_change_type,
            pattern_description=pattern_description,
            clearing_type=ClearingType(dominant_clearing_type),
            message_type=MessageType(dominant_message_type),
            occurrence_count=occurrence_count,
            unique_users=unique_users,
            example_logs=example_log_ids,
            automation_feasibility=automation_feasibility,
            automation_confidence=automation_confidence,
            potential_rule=rule_suggestion
        )
    
    def _calculate_consistency_score(self, cluster_data: pd.DataFrame) -> float:
        """Calculate how consistent the repair pattern is"""
        # Check consistency across multiple dimensions
        change_type_consistency = 1.0 / cluster_data['change_type'].nunique()
        clearing_type_consistency = 1.0 / cluster_data['clearing_type'].nunique()
        message_type_consistency = 1.0 / cluster_data['message_type'].nunique()
        
        # Average magnitude variation
        magnitude_std = cluster_data['change_magnitude'].std()
        magnitude_consistency = 1.0 / (1.0 + magnitude_std)
        
        return np.mean([change_type_consistency, clearing_type_consistency, 
                       message_type_consistency, magnitude_consistency])
    
    def _calculate_complexity_score(self, cluster_data: pd.DataFrame) -> float:
        """Calculate complexity of the repair pattern (higher = more complex)"""
        # Simple repairs (like space removal) are less complex
        avg_magnitude = cluster_data['change_magnitude'].mean()
        
        # Multiple field changes increase complexity
        iban_change_rate = cluster_data['iban_changed'].mean()
        account_id_change_rate = cluster_data['account_id_changed'].mean()
        multi_field_complexity = iban_change_rate * account_id_change_rate
        
        # Auto repair attempts indicate complexity
        avg_auto_attempts = cluster_data['auto_repair_attempts'].mean()
        auto_attempt_complexity = min(avg_auto_attempts / 3, 1.0)
        
        return np.mean([avg_magnitude, multi_field_complexity, auto_attempt_complexity])
    
    def _calculate_risk_score(self, cluster_data: pd.DataFrame) -> float:
        """Calculate risk of automation (higher = riskier)"""
        # Large changes are riskier
        magnitude_risk = cluster_data['change_magnitude'].mean()
        
        # Country changes are risky
        country_changes = (cluster_data['change_type'] == 'COUNTRY_CHANGE').sum()
        country_risk = country_changes / len(cluster_data)
        
        # High-value transactions are riskier
        high_value_risk = (cluster_data['clearing_type'] == 'HIGH_VALUE').sum() / len(cluster_data)
        
        return np.mean([magnitude_risk, country_risk, high_value_risk])
    
    def _generate_cluster_description(self, cluster_data: pd.DataFrame, change_type: str) -> str:
        """Generate human-readable description of the cluster pattern"""
        count = len(cluster_data)
        dominant_clearing = cluster_data['clearing_type'].mode().iloc[0]
        dominant_message = cluster_data['message_type'].mode().iloc[0]
        
        descriptions = {
            'SPACE_FORMATTING': f'IBAN space formatting corrections in {dominant_clearing} {dominant_message} transactions',
            'LENGTH_CHANGE': f'IBAN length corrections in {dominant_clearing} {dominant_message} transactions',
            'CONTENT_CHANGE': f'IBAN content corrections in {dominant_clearing} {dominant_message} transactions',
            'ACCOUNT_ID_CHANGE': f'Account ID corrections in {dominant_clearing} {dominant_message} transactions',
            'COUNTRY_CHANGE': f'IBAN country code corrections in {dominant_clearing} {dominant_message} transactions'
        }
        
        base_desc = descriptions.get(change_type, f'{change_type} repairs in {dominant_clearing} {dominant_message}')
        return f'{base_desc} ({count} occurrences)'
    
    def _suggest_automation_rule(self, cluster_data: pd.DataFrame) -> str:
        """Suggest an automation rule for the cluster pattern"""
        change_type = cluster_data['change_type'].mode().iloc[0]
        
        suggestions = {
            'SPACE_FORMATTING': 'Create rule to automatically remove spaces from IBAN input',
            'LENGTH_CHANGE': 'Create validation rule to check IBAN length and suggest corrections',
            'CONTENT_CHANGE': 'Create lookup table for common IBAN corrections',
            'ACCOUNT_ID_CHANGE': 'Requires manual review - account changes may need verification',
            'COUNTRY_CHANGE': 'High risk - requires careful validation before automation'
        }
        
        return suggestions.get(change_type, 'Pattern requires further analysis')
    
    def generate_automation_insights(self, patterns: List[RepairPattern]) -> Dict[str, Any]:
        """Generate high-level insights about automation opportunities"""
        total_patterns = len(patterns)
        high_feasibility_patterns = len([p for p in patterns if p.automation_feasibility > 0.8])
        total_occurrences = sum(p.occurrence_count for p in patterns)
        
        # Calculate potential savings
        automatable_repairs = sum(p.occurrence_count for p in patterns if p.automation_feasibility > 0.7)
        automation_potential = automatable_repairs / total_occurrences if total_occurrences > 0 else 0
        
        # Risk analysis
        high_risk_patterns = len([p for p in patterns if p.automation_feasibility < 0.5])
        
        return {
            'total_patterns_identified': total_patterns,
            'high_feasibility_patterns': high_feasibility_patterns,
            'total_repair_occurrences': total_occurrences,
            'automatable_repairs': automatable_repairs,
            'automation_potential_percentage': round(automation_potential * 100, 2),
            'high_risk_patterns': high_risk_patterns,
            'top_patterns': [
                {
                    'pattern_id': p.pattern_id,
                    'description': p.pattern_description,
                    'feasibility': round(p.automation_feasibility, 3),
                    'occurrences': p.occurrence_count
                }
                for p in patterns[:5]
            ],
            'recommendations': self._generate_recommendations(patterns)
        }
    
    def _generate_recommendations(self, patterns: List[RepairPattern]) -> List[str]:
        """Generate actionable recommendations based on pattern analysis"""
        recommendations = []
        
        high_feasibility = [p for p in patterns if p.automation_feasibility > 0.8]
        if high_feasibility:
            recommendations.append(
                f"Immediately implement rules for {len(high_feasibility)} high-feasibility patterns "
                f"to automate {sum(p.occurrence_count for p in high_feasibility)} repairs"
            )
        
        medium_feasibility = [p for p in patterns if 0.5 < p.automation_feasibility <= 0.8]
        if medium_feasibility:
            recommendations.append(
                f"Review {len(medium_feasibility)} medium-feasibility patterns for selective automation"
            )
        
        high_frequency = [p for p in patterns if p.occurrence_count >= 10]
        if high_frequency:
            recommendations.append(
                f"Priority focus on {len(high_frequency)} high-frequency patterns for maximum impact"
            )
        
        space_formatting = [p for p in patterns if 'space' in p.pattern_description.lower()]
        if space_formatting:
            recommendations.append("IBAN space formatting is highly automatable - implement immediately")
        
        return recommendations