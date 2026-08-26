"""
Audit logger for tracking manual account repairs
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import uuid

from ..models import (
    ManualRepairAuditLog, AuditLogType, Account, AccountType,
    ClearingType, MessageType, AuditLogSummary, RepairPattern
)


class AuditLogger:
    """Logger for manual repair audit events"""
    
    def __init__(self, log_file_path: Optional[str] = None):
        self.log_file_path = log_file_path or "data/audit_logs.json"
        self.logs: List[ManualRepairAuditLog] = []
        self._load_existing_logs()
    
    def _load_existing_logs(self):
        """Load existing audit logs from file"""
        try:
            log_path = Path(self.log_file_path)
            if log_path.exists():
                with open(log_path, 'r') as f:
                    log_data = json.load(f)
                    self.logs = [ManualRepairAuditLog(**log) for log in log_data]
        except Exception as e:
            print(f"Warning: Could not load existing logs: {e}")
    
    def _save_logs(self):
        """Save logs to file"""
        try:
            log_path = Path(self.log_file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert logs to dict format for JSON serialization
            log_data = [log.dict() for log in self.logs]
            
            with open(log_path, 'w') as f:
                json.dump(log_data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving logs: {e}")
    
    def log_manual_repair(self, transaction_id: str, old_account: Account, new_account: Account,
                         clearing_type: ClearingType, message_type: MessageType,
                         repaired_by: str, repair_reason: Optional[str] = None,
                         validation_errors: Optional[List[str]] = None,
                         auto_repair_attempts: int = 0) -> str:
        """
        Log a manual account repair event
        
        Args:
            transaction_id: ID of the transaction being repaired
            old_account: Original account details
            new_account: Repaired account details
            clearing_type: Clearing type
            message_type: Message type
            repaired_by: User who performed the repair
            repair_reason: Reason for manual repair
            validation_errors: List of original validation errors
            auto_repair_attempts: Number of failed auto repair attempts
            
        Returns:
            Log ID of the created audit log
        """
        log_id = str(uuid.uuid4())
        
        # Determine log type based on account type
        if old_account.account_type == AccountType.DEBITOR:
            log_type = AuditLogType.DR_ACCOUNT_MANUAL_REPAIR
        else:
            log_type = AuditLogType.CR_ACCOUNT_MANUAL_REPAIR
        
        audit_log = ManualRepairAuditLog(
            log_id=log_id,
            log_type=log_type,
            transaction_id=transaction_id,
            clearing_type=clearing_type,
            message_type=message_type,
            old_account_id=old_account.account_id,
            old_iban=old_account.iban,
            new_account_id=new_account.account_id,
            new_iban=new_account.iban,
            repaired_by=repaired_by,
            repair_reason=repair_reason,
            validation_errors=validation_errors,
            auto_repair_attempts=auto_repair_attempts,
            additional_data={
                "old_bank_code": old_account.bank_code,
                "new_bank_code": new_account.bank_code,
                "old_account_name": old_account.account_name,
                "new_account_name": new_account.account_name
            }
        )
        
        self.logs.append(audit_log)
        self._save_logs()
        
        # Print formatted audit message (as would appear in system logs)
        print(f"AUDIT: {audit_log.format_audit_message()}")
        
        return log_id
    
    def get_logs_by_date_range(self, start_date: datetime, end_date: datetime) -> List[ManualRepairAuditLog]:
        """Get audit logs within a date range"""
        return [
            log for log in self.logs
            if start_date <= log.repair_timestamp <= end_date
        ]
    
    def get_logs_by_user(self, user: str) -> List[ManualRepairAuditLog]:
        """Get audit logs for a specific user"""
        return [log for log in self.logs if log.repaired_by == user]
    
    def get_logs_by_clearing_type(self, clearing_type: ClearingType) -> List[ManualRepairAuditLog]:
        """Get audit logs for a specific clearing type"""
        return [log for log in self.logs if log.clearing_type == clearing_type]
    
    def get_logs_by_message_type(self, message_type: MessageType) -> List[ManualRepairAuditLog]:
        """Get audit logs for a specific message type"""
        return [log for log in self.logs if log.message_type == message_type]
    
    def generate_summary(self, days_back: int = 30) -> AuditLogSummary:
        """Generate summary statistics for audit logs"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        relevant_logs = self.get_logs_by_date_range(start_date, end_date)
        
        summary = AuditLogSummary(
            total_logs=len(relevant_logs),
            dr_repairs=len([log for log in relevant_logs if log.log_type == AuditLogType.DR_ACCOUNT_MANUAL_REPAIR]),
            cr_repairs=len([log for log in relevant_logs if log.log_type == AuditLogType.CR_ACCOUNT_MANUAL_REPAIR]),
            analysis_start_date=start_date,
            analysis_end_date=end_date
        )
        
        # Generate breakdowns
        summary.logs_by_day = self._get_logs_by_day(relevant_logs)
        summary.logs_by_hour = self._get_logs_by_hour(relevant_logs)
        summary.top_clearing_types = self._get_top_clearing_types(relevant_logs)
        summary.top_message_types = self._get_top_message_types(relevant_logs)
        summary.top_repair_reasons = self._get_top_repair_reasons(relevant_logs)
        summary.repairs_by_user = self._get_repairs_by_user(relevant_logs)
        
        return summary
    
    def _get_logs_by_day(self, logs: List[ManualRepairAuditLog]) -> Dict[str, int]:
        """Group logs by day"""
        day_counts = {}
        for log in logs:
            day_str = log.repair_timestamp.strftime('%Y-%m-%d')
            day_counts[day_str] = day_counts.get(day_str, 0) + 1
        return day_counts
    
    def _get_logs_by_hour(self, logs: List[ManualRepairAuditLog]) -> Dict[str, int]:
        """Group logs by hour of day"""
        hour_counts = {}
        for log in logs:
            hour_str = str(log.repair_timestamp.hour)
            hour_counts[hour_str] = hour_counts.get(hour_str, 0) + 1
        return hour_counts
    
    def _get_top_clearing_types(self, logs: List[ManualRepairAuditLog]) -> Dict[str, int]:
        """Get most common clearing types"""
        clearing_counts = {}
        for log in logs:
            clearing_type = log.clearing_type
            clearing_counts[clearing_type] = clearing_counts.get(clearing_type, 0) + 1
        
        # Sort by count and return top 10
        sorted_items = sorted(clearing_counts.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_items[:10])
    
    def _get_top_message_types(self, logs: List[ManualRepairAuditLog]) -> Dict[str, int]:
        """Get most common message types"""
        message_counts = {}
        for log in logs:
            message_type = log.message_type
            message_counts[message_type] = message_counts.get(message_type, 0) + 1
        
        sorted_items = sorted(message_counts.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_items[:10])
    
    def _get_top_repair_reasons(self, logs: List[ManualRepairAuditLog]) -> Dict[str, int]:
        """Get most common repair reasons"""
        reason_counts = {}
        for log in logs:
            if log.repair_reason:
                reason_counts[log.repair_reason] = reason_counts.get(log.repair_reason, 0) + 1
        
        sorted_items = sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_items[:10])
    
    def _get_repairs_by_user(self, logs: List[ManualRepairAuditLog]) -> Dict[str, int]:
        """Get repair counts by user"""
        user_counts = {}
        for log in logs:
            user = log.repaired_by
            user_counts[user] = user_counts.get(user, 0) + 1
        
        sorted_items = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_items)
    
    def identify_patterns(self, min_occurrences: int = 3) -> List[RepairPattern]:
        """Identify patterns in manual repairs that could be automated"""
        patterns = []
        
        # Group logs by similar characteristics
        grouped_logs = self._group_logs_for_pattern_analysis()
        
        for pattern_key, pattern_logs in grouped_logs.items():
            if len(pattern_logs) >= min_occurrences:
                # Extract pattern characteristics
                clearing_type, message_type, pattern_type = pattern_key
                
                # Calculate automation potential
                feasibility = self._calculate_automation_feasibility(pattern_logs)
                confidence = self._calculate_automation_confidence(pattern_logs)
                
                pattern = RepairPattern(
                    pattern_id=f"PATTERN_{hash(pattern_key) % 10000:04d}",
                    pattern_type=pattern_type,
                    pattern_description=self._generate_pattern_description(pattern_logs),
                    clearing_type=clearing_type,
                    message_type=message_type,
                    occurrence_count=len(pattern_logs),
                    unique_users=len(set(log.repaired_by for log in pattern_logs)),
                    example_logs=[log.log_id for log in pattern_logs[:5]],
                    automation_feasibility=feasibility,
                    automation_confidence=confidence,
                    potential_rule=self._suggest_rule_description(pattern_logs)
                )
                
                patterns.append(pattern)
        
        # Sort by occurrence count
        patterns.sort(key=lambda p: p.occurrence_count, reverse=True)
        return patterns
    
    def _group_logs_for_pattern_analysis(self) -> Dict[tuple, List[ManualRepairAuditLog]]:
        """Group logs by similar repair patterns"""
        grouped = {}
        
        for log in self.logs:
            # Analyze the type of change made
            pattern_type = self._classify_repair_type(log)
            
            # Group by clearing type, message type, and pattern type
            key = (log.clearing_type, log.message_type, pattern_type)
            
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(log)
        
        return grouped
    
    def _classify_repair_type(self, log: ManualRepairAuditLog) -> str:
        """Classify the type of repair performed"""
        # Simple pattern classification based on changes
        if log.old_iban != log.new_iban:
            if " " in log.old_iban and " " not in log.new_iban:
                return "IBAN_SPACE_REMOVAL"
            elif len(log.old_iban) != len(log.new_iban):
                return "IBAN_FORMAT_CHANGE"
            else:
                return "IBAN_CORRECTION"
        
        if log.old_account_id != log.new_account_id:
            return "ACCOUNT_ID_CHANGE"
        
        # Check additional data for bank code changes
        old_bank_code = log.additional_data.get("old_bank_code", "") if log.additional_data else ""
        new_bank_code = log.additional_data.get("new_bank_code", "") if log.additional_data else ""
        
        if old_bank_code != new_bank_code:
            return "BANK_CODE_CORRECTION"
        
        return "OTHER"
    
    def _calculate_automation_feasibility(self, logs: List[ManualRepairAuditLog]) -> float:
        """Calculate how feasible it would be to automate this repair pattern"""
        # Factors that increase feasibility:
        # - Consistent pattern across users
        # - Simple transformation rules
        # - Low risk operations
        
        unique_users = len(set(log.repaired_by for log in logs))
        total_occurrences = len(logs)
        
        # If multiple users are making the same repair, it's more likely automatable
        user_consistency_score = min(unique_users / max(total_occurrences, 1) * 2, 1.0)
        
        # Pattern-specific feasibility
        pattern_type = self._classify_repair_type(logs[0])
        pattern_feasibility = {
            "IBAN_SPACE_REMOVAL": 0.9,
            "BANK_CODE_CORRECTION": 0.7,
            "IBAN_FORMAT_CHANGE": 0.5,
            "ACCOUNT_ID_CHANGE": 0.3,
            "OTHER": 0.2
        }.get(pattern_type, 0.2)
        
        return (user_consistency_score + pattern_feasibility) / 2
    
    def _calculate_automation_confidence(self, logs: List[ManualRepairAuditLog]) -> float:
        """Calculate confidence in the automation suggestion"""
        frequency_score = min(len(logs) / 10, 1.0)  # More occurrences = higher confidence
        consistency_score = self._measure_pattern_consistency(logs)
        
        return (frequency_score + consistency_score) / 2
    
    def _measure_pattern_consistency(self, logs: List[ManualRepairAuditLog]) -> float:
        """Measure how consistent the repair pattern is"""
        if len(logs) < 2:
            return 0.5
        
        # Check consistency of repair types
        repair_types = [self._classify_repair_type(log) for log in logs]
        unique_types = len(set(repair_types))
        
        # More consistent = fewer unique repair types
        return 1.0 / unique_types if unique_types > 0 else 0.0
    
    def _generate_pattern_description(self, logs: List[ManualRepairAuditLog]) -> str:
        """Generate human-readable description of the pattern"""
        pattern_type = self._classify_repair_type(logs[0])
        count = len(logs)
        clearing_type = logs[0].clearing_type
        message_type = logs[0].message_type
        
        descriptions = {
            "IBAN_SPACE_REMOVAL": f"Remove spaces from IBAN format ({count} occurrences)",
            "BANK_CODE_CORRECTION": f"Correct bank codes for {clearing_type} {message_type} ({count} occurrences)",
            "IBAN_FORMAT_CHANGE": f"Fix IBAN format issues ({count} occurrences)",
            "ACCOUNT_ID_CHANGE": f"Account ID corrections ({count} occurrences)",
            "OTHER": f"Other repair pattern ({count} occurrences)"
        }
        
        return descriptions.get(pattern_type, f"Unclassified pattern ({count} occurrences)")
    
    def _suggest_rule_description(self, logs: List[ManualRepairAuditLog]) -> str:
        """Suggest a repair rule description for this pattern"""
        pattern_type = self._classify_repair_type(logs[0])
        
        suggestions = {
            "IBAN_SPACE_REMOVAL": "Create rule to automatically remove spaces from IBAN input",
            "BANK_CODE_CORRECTION": "Create lookup table rule for bank code standardization",
            "IBAN_FORMAT_CHANGE": "Create rule to validate and correct IBAN format",
            "ACCOUNT_ID_CHANGE": "Review account validation rules - may require manual intervention",
            "OTHER": "Pattern requires further analysis before automation"
        }
        
        return suggestions.get(pattern_type, "Manual review recommended")
    
    def export_logs_for_ai_analysis(self, format_type: str = "json") -> str:
        """Export logs in format suitable for AI analysis"""
        analysis_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_logs": len(self.logs),
            "logs": []
        }
        
        for log in self.logs:
            log_data = {
                "log_id": log.log_id,
                "log_type": log.log_type,
                "clearing_type": log.clearing_type,
                "message_type": log.message_type,
                "repair_timestamp": log.repair_timestamp.isoformat(),
                "repair_pattern": self._classify_repair_type(log),
                "old_iban": log.old_iban,
                "new_iban": log.new_iban,
                "old_account_id": log.old_account_id,
                "new_account_id": log.new_account_id,
                "validation_errors": log.validation_errors,
                "auto_repair_attempts": log.auto_repair_attempts
            }
            analysis_data["logs"].append(log_data)
        
        if format_type == "json":
            return json.dumps(analysis_data, indent=2)
        else:
            # Could add CSV, XML formats etc.
            return json.dumps(analysis_data, indent=2)