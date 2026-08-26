"""
Manual repair API interface for handling manual account corrections
"""

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from ..models import (
    PaymentTransaction, Account, ManualRepairAuditLog, AccountType,
    ClearingType, MessageType
)
from ..logging.audit_logger import AuditLogger
from ..core.payment_processor import PaymentProcessor


class ManualRepairRequest(BaseModel):
    """Request model for manual repair"""
    transaction_id: str
    account_type: AccountType  # DR or CR
    new_account: Account
    repair_reason: Optional[str] = None
    repaired_by: str


class ManualRepairResponse(BaseModel):
    """Response model for manual repair"""
    success: bool
    repair_log_id: Optional[str] = None
    message: str
    validation_result: Optional[Dict[str, Any]] = None


class ManualRepairStats(BaseModel):
    """Statistics for manual repairs"""
    total_repairs: int
    repairs_by_type: Dict[str, int]
    repairs_by_user: Dict[str, int]
    recent_repairs: List[Dict[str, Any]]


class ManualRepairAPI:
    """API interface for manual repair operations"""
    
    def __init__(self, audit_logger: AuditLogger, payment_processor: PaymentProcessor):
        self.audit_logger = audit_logger
        self.payment_processor = payment_processor
        self.app = FastAPI(title="APS Manual Repair API", version="1.0.0")
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.post("/repair/manual", response_model=ManualRepairResponse)
        async def perform_manual_repair(request: ManualRepairRequest):
            """Perform manual account repair and log the action"""
            try:
                return self._process_manual_repair(request)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/repair/suggestions/{transaction_id}")
        async def get_repair_suggestions(transaction_id: str):
            """Get suggested fixes for a transaction"""
            try:
                return self._get_repair_suggestions(transaction_id)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/repair/history", response_model=List[ManualRepairAuditLog])
        async def get_repair_history(
            days_back: int = 30,
            user: Optional[str] = None,
            clearing_type: Optional[str] = None
        ):
            """Get manual repair history"""
            try:
                return self._get_repair_history(days_back, user, clearing_type)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/repair/stats", response_model=ManualRepairStats)
        async def get_repair_statistics(days_back: int = 30):
            """Get manual repair statistics"""
            try:
                return self._get_repair_statistics(days_back)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/repair/patterns")
        async def get_repair_patterns(days_back: int = 30):
            """Get identified repair patterns for automation"""
            try:
                return self._get_repair_patterns(days_back)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/repair/validate")
        async def validate_repair(account: Account, clearing_type: str, message_type: str):
            """Validate a proposed account repair"""
            try:
                return self._validate_repair(account, clearing_type, message_type)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    def _process_manual_repair(self, request: ManualRepairRequest) -> ManualRepairResponse:
        """Process a manual repair request"""
        # First, validate the repaired account
        try:
            is_valid, errors = self.payment_processor.validator.validate_account(
                request.new_account,
                ClearingType(request.clearing_type) if hasattr(request, 'clearing_type') else ClearingType.DOMESTIC,
                MessageType(request.message_type) if hasattr(request, 'message_type') else MessageType.ISO20022_PACS008
            )
            
            if not is_valid:
                return ManualRepairResponse(
                    success=False,
                    message=f"Repaired account still has validation errors: {[e.error_message for e in errors]}",
                    validation_result={"valid": False, "errors": [e.dict() for e in errors]}
                )
            
            # For POC purposes, create a mock old account
            # In real system, this would be retrieved from the transaction
            old_account = Account(
                account_id="OLD_ACCOUNT_123",
                iban="DE89 3704 0044 0532 013000",  # Invalid format with spaces
                bank_code="12345678",
                account_type=request.account_type,
                account_name="Old Account Name"
            )
            
            # Log the manual repair
            log_id = self.audit_logger.log_manual_repair(
                transaction_id=request.transaction_id,
                old_account=old_account,
                new_account=request.new_account,
                clearing_type=ClearingType.DOMESTIC,  # Default for POC
                message_type=MessageType.ISO20022_PACS008,  # Default for POC
                repaired_by=request.repaired_by,
                repair_reason=request.repair_reason,
                validation_errors=["IBAN_INVALID_FORMAT", "BANK_CODE_INVALID"],
                auto_repair_attempts=2
            )
            
            return ManualRepairResponse(
                success=True,
                repair_log_id=log_id,
                message="Manual repair completed successfully",
                validation_result={"valid": True, "errors": []}
            )
            
        except Exception as e:
            return ManualRepairResponse(
                success=False,
                message=f"Error processing manual repair: {str(e)}"
            )
    
    def _get_repair_suggestions(self, transaction_id: str) -> Dict[str, Any]:
        """Get repair suggestions for a transaction"""
        # For POC, return mock suggestions based on common patterns
        return {
            "transaction_id": transaction_id,
            "suggestions": [
                {
                    "type": "IBAN_FORMATTING",
                    "description": "Remove spaces from IBAN",
                    "old_value": "DE89 3704 0044 0532 013000",
                    "suggested_value": "DE89370400440532013000",
                    "confidence": 0.95
                },
                {
                    "type": "BANK_CODE_MAPPING",
                    "description": "Update bank code to standard format",
                    "old_value": "BARC",
                    "suggested_value": "BARCGB22",
                    "confidence": 0.8
                }
            ],
            "auto_repair_attempts": 2,
            "validation_errors": [
                "IBAN_INVALID_FORMAT",
                "BANK_CODE_INVALID"
            ]
        }
    
    def _get_repair_history(self, days_back: int, user: Optional[str], 
                          clearing_type: Optional[str]) -> List[Dict[str, Any]]:
        """Get manual repair history"""
        end_date = datetime.now()
        start_date = end_date - datetime.timedelta(days=days_back)
        
        logs = self.audit_logger.get_logs_by_date_range(start_date, end_date)
        
        # Filter by user if specified
        if user:
            logs = [log for log in logs if log.repaired_by == user]
        
        # Filter by clearing type if specified
        if clearing_type:
            logs = [log for log in logs if log.clearing_type == clearing_type]
        
        # Convert to dict format for JSON response
        return [log.dict() for log in logs]
    
    def _get_repair_statistics(self, days_back: int) -> ManualRepairStats:
        """Get repair statistics"""
        summary = self.audit_logger.generate_summary(days_back)
        
        # Get recent repairs for display
        recent_logs = self.audit_logger.get_logs_by_date_range(
            datetime.now() - datetime.timedelta(days=7),
            datetime.now()
        )
        
        recent_repairs = [
            {
                "log_id": log.log_id,
                "transaction_id": log.transaction_id,
                "repair_type": log.log_type,
                "repaired_by": log.repaired_by,
                "repair_timestamp": log.repair_timestamp.isoformat(),
                "clearing_type": log.clearing_type,
                "message_type": log.message_type
            }
            for log in recent_logs[:10]
        ]
        
        return ManualRepairStats(
            total_repairs=summary.total_repairs,
            repairs_by_type={
                "DR_REPAIRS": summary.dr_repairs,
                "CR_REPAIRS": summary.cr_repairs
            },
            repairs_by_user=summary.repairs_by_user,
            recent_repairs=recent_repairs
        )
    
    def _get_repair_patterns(self, days_back: int) -> Dict[str, Any]:
        """Get repair patterns for automation analysis"""
        patterns = self.audit_logger.identify_patterns(min_occurrences=2)
        
        pattern_data = {
            "analysis_period_days": days_back,
            "patterns_identified": len(patterns),
            "patterns": [
                {
                    "pattern_id": pattern.pattern_id,
                    "pattern_type": pattern.pattern_type,
                    "description": pattern.pattern_description,
                    "occurrence_count": pattern.occurrence_count,
                    "unique_users": pattern.unique_users,
                    "automation_feasibility": pattern.automation_feasibility,
                    "automation_confidence": pattern.automation_confidence,
                    "potential_rule": pattern.potential_rule,
                    "clearing_type": pattern.clearing_type,
                    "message_type": pattern.message_type
                }
                for pattern in patterns
            ],
            "automation_recommendations": [
                pattern.potential_rule 
                for pattern in patterns 
                if pattern.automation_feasibility > 0.7
            ][:5]
        }
        
        return pattern_data
    
    def _validate_repair(self, account: Account, clearing_type: str, 
                        message_type: str) -> Dict[str, Any]:
        """Validate a proposed account repair"""
        try:
            clearing_enum = ClearingType(clearing_type)
            message_enum = MessageType(message_type)
            
            is_valid, errors = self.payment_processor.validator.validate_account(
                account, clearing_enum, message_enum
            )
            
            suggestions = []
            if not is_valid:
                suggestions = self.payment_processor.validator.get_suggested_fixes(
                    errors, account
                )
            
            return {
                "valid": is_valid,
                "errors": [
                    {
                        "error_code": error.error_code,
                        "error_message": error.error_message,
                        "field_name": error.field_name,
                        "current_value": error.current_value
                    }
                    for error in errors
                ],
                "suggestions": suggestions,
                "account_summary": {
                    "account_id": account.account_id,
                    "iban": account.iban,
                    "bank_code": account.bank_code,
                    "account_type": account.account_type
                }
            }
            
        except ValueError as e:
            return {
                "valid": False,
                "errors": [f"Invalid enum value: {str(e)}"],
                "suggestions": [],
                "account_summary": None
            }


def create_manual_repair_app(audit_logger: AuditLogger, 
                           payment_processor: PaymentProcessor) -> FastAPI:
    """Factory function to create the FastAPI app"""
    api = ManualRepairAPI(audit_logger, payment_processor)
    return api.app


# Usage example endpoints for testing
def add_demo_endpoints(app: FastAPI):
    """Add demo endpoints for testing the API"""
    
    @app.get("/demo/create-sample-repair")
    async def create_sample_repair():
        """Create a sample manual repair for testing"""
        # This would normally be called through the main repair endpoint
        return {
            "message": "Use POST /repair/manual to create actual repairs",
            "sample_request": {
                "transaction_id": "TXN_12345",
                "account_type": "DR",
                "new_account": {
                    "account_id": "NEW_ACCOUNT_456",
                    "iban": "DE89370400440532013000",
                    "bank_code": "37040044",
                    "account_type": "DR",
                    "account_name": "Fixed Account Name"
                },
                "repair_reason": "IBAN formatting correction",
                "repaired_by": "user@example.com"
            }
        }
    
    @app.get("/demo/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "APS Manual Repair API"
        }