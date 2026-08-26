from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum
from .account import ClearingType, MessageType, AccountType


class RuleCondition(BaseModel):
    """Individual condition within a repair rule"""
    field_name: str = Field(..., description="Field to check")
    operator: str = Field(..., description="Comparison operator (eq, ne, contains, regex)")
    value: Any = Field(..., description="Value to compare against")
    
    
class RuleAction(BaseModel):
    """Action to take when rule conditions are met"""
    action_type: str = Field(..., description="Type of action (replace, transform, lookup)")
    target_field: str = Field(..., description="Field to modify")
    action_value: Optional[str] = Field(None, description="Static replacement value")
    transformation: Optional[str] = Field(None, description="Transformation function")
    lookup_table: Optional[str] = Field(None, description="Reference to lookup table")


class RepairRule(BaseModel):
    """Automated repair rule definition"""
    rule_id: str = Field(..., description="Unique rule identifier")
    rule_name: str = Field(..., description="Human readable rule name")
    description: str = Field(..., description="Rule description")
    
    # Rule targeting
    clearing_types: List[ClearingType] = Field(default=[], description="Applicable clearing types")
    message_types: List[MessageType] = Field(default=[], description="Applicable message types")
    account_types: List[AccountType] = Field(default=[], description="Applicable account types")
    
    # Rule logic
    conditions: List[RuleCondition] = Field(..., description="Conditions that must be met")
    actions: List[RuleAction] = Field(..., description="Actions to perform")
    
    # Rule metadata
    priority: int = Field(default=100, description="Rule priority (lower = higher priority)")
    is_active: bool = Field(default=True, description="Rule active status")
    created_date: datetime = Field(default_factory=datetime.now)
    created_by: str = Field(..., description="Rule creator")
    
    # Statistics
    success_count: int = Field(default=0, description="Successful applications")
    failure_count: int = Field(default=0, description="Failed applications")
    
    class Config:
        use_enum_values = True


class RuleTemplate(BaseModel):
    """Template for common repair patterns"""
    template_id: str = Field(..., description="Template identifier")
    template_name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    pattern_type: str = Field(..., description="Type of repair pattern")
    
    # Template structure
    condition_template: Dict[str, Any] = Field(..., description="Condition template")
    action_template: Dict[str, Any] = Field(..., description="Action template")
    
    # Usage tracking
    usage_count: int = Field(default=0, description="Times template was used")
    
    
class SuggestedRule(BaseModel):
    """AI-suggested repair rule"""
    suggestion_id: str = Field(..., description="Unique suggestion identifier")
    suggested_rule: RepairRule = Field(..., description="The suggested rule")
    
    # Suggestion metadata
    confidence_score: float = Field(..., description="Confidence in suggestion (0-1)")
    pattern_frequency: int = Field(..., description="How often this pattern occurs")
    manual_repair_count: int = Field(..., description="Manual repairs this would automate")
    
    # Analysis data
    supporting_cases: List[str] = Field(..., description="Audit log IDs supporting this rule")
    feasibility_score: float = Field(..., description="Automation feasibility (0-1)")
    risk_level: str = Field(..., description="Risk level: LOW, MEDIUM, HIGH")
    
    # Status
    status: str = Field(default="PENDING", description="PENDING, APPROVED, REJECTED")
    reviewed_by: Optional[str] = Field(None, description="Reviewer")
    review_date: Optional[datetime] = Field(None, description="Review date")
    review_notes: Optional[str] = Field(None, description="Review comments")