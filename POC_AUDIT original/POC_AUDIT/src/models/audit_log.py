from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from .account import ClearingType, MessageType, AccountType


class AuditLogType(str):
    DR_ACCOUNT_MANUAL_REPAIR = "DR_ACCOUNT_MANUAL_REPAIR"
    CR_ACCOUNT_MANUAL_REPAIR = "CR_ACCOUNT_MANUAL_REPAIR"


class ManualRepairAuditLog(BaseModel):
    """Audit log for manual account repairs"""
    log_id: str = Field(..., description="Unique log identifier")
    log_type: str = Field(..., description="Log type (DR_ACCOUNT_MANUAL_REPAIR or CR_ACCOUNT_MANUAL_REPAIR)")
    
    # Transaction context
    transaction_id: str = Field(..., description="Related transaction ID")
    clearing_type: ClearingType = Field(..., description="Clearing type")
    message_type: MessageType = Field(..., description="Message type")
    
    # Account changes
    old_account_id: str = Field(..., description="Original account ID")
    old_iban: str = Field(..., description="Original IBAN")
    new_account_id: str = Field(..., description="New account ID")
    new_iban: str = Field(..., description="New IBAN")
    
    # Metadata
    repaired_by: str = Field(..., description="User who performed the repair")
    repair_timestamp: datetime = Field(default_factory=datetime.now)
    repair_reason: Optional[str] = Field(None, description="Reason for manual repair")
    
    # Original validation errors
    validation_errors: Optional[List[str]] = Field(None, description="Original validation failures")
    
    # Additional context
    auto_repair_attempts: int = Field(default=0, description="Number of failed auto repair attempts")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="Additional contextual data")
    
    def format_audit_message(self) -> str:
        """Format the audit log message according to the specified format"""
        account_type = "Debitor" if self.log_type == AuditLogType.DR_ACCOUNT_MANUAL_REPAIR else "Creditor"
        
        message = (
            f"{account_type} account changed by manual repair for "
            f"clearing type {self.clearing_type} "
            f"message type {self.message_type} "
            f"old account Id {self.old_account_id} "
            f"old IBAN {self.old_iban} "
            f"new account Id {self.new_account_id} "
            f"new IBAN {self.new_iban}"
        )
        
        return message
    
    class Config:
        use_enum_values = True


class AuditLogSummary(BaseModel):
    """Summary statistics for audit logs"""
    total_logs: int = Field(..., description="Total number of audit logs")
    dr_repairs: int = Field(..., description="Debitor account repairs")
    cr_repairs: int = Field(..., description="Creditor account repairs")
    
    # Time-based breakdown
    logs_by_day: Dict[str, int] = Field(default={}, description="Logs grouped by day")
    logs_by_hour: Dict[str, int] = Field(default={}, description="Logs grouped by hour")
    
    # Pattern breakdown
    top_clearing_types: Dict[str, int] = Field(default={}, description="Most common clearing types")
    top_message_types: Dict[str, int] = Field(default={}, description="Most common message types")
    top_repair_reasons: Dict[str, int] = Field(default={}, description="Most common repair reasons")
    
    # User activity
    repairs_by_user: Dict[str, int] = Field(default={}, description="Repairs by user")
    
    # Analysis period
    analysis_start_date: datetime = Field(..., description="Analysis start date")
    analysis_end_date: datetime = Field(..., description="Analysis end date")


class RepairPattern(BaseModel):
    """Identified pattern in manual repairs"""
    pattern_id: str = Field(..., description="Pattern identifier")
    pattern_type: str = Field(..., description="Type of pattern identified")
    pattern_description: str = Field(..., description="Human readable description")
    
    # Pattern characteristics
    clearing_type: Optional[ClearingType] = Field(None, description="Associated clearing type")
    message_type: Optional[MessageType] = Field(None, description="Associated message type")
    account_type: Optional[AccountType] = Field(None, description="Associated account type")
    
    # Pattern frequency
    occurrence_count: int = Field(..., description="Number of times pattern occurred")
    unique_users: int = Field(..., description="Number of different users who made this repair")
    
    # Pattern examples
    example_logs: List[str] = Field(..., description="Example audit log IDs")
    
    # Automation potential
    automation_feasibility: float = Field(..., description="Feasibility score for automation")
    automation_confidence: float = Field(..., description="Confidence in automation")
    potential_rule: Optional[str] = Field(None, description="Suggested rule description")
    
    class Config:
        use_enum_values = True