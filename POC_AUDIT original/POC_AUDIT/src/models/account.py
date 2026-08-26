from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class AccountType(str, Enum):
    DEBITOR = "DR"
    CREDITOR = "CR"
    

class ClearingType(str, Enum):
    DOMESTIC = "DOMESTIC"
    INTERNATIONAL = "INTERNATIONAL"
    SAME_DAY = "SAME_DAY"
    HIGH_VALUE = "HIGH_VALUE"


class MessageType(str, Enum):
    SWIFT_MT103 = "MT103"
    SWIFT_MT202 = "MT202"
    ISO20022_PACS008 = "PACS.008"
    ISO20022_PACS009 = "PACS.009"


class Account(BaseModel):
    """Account model representing bank account information"""
    account_id: str = Field(..., description="Unique account identifier")
    iban: str = Field(..., description="International Bank Account Number")
    bank_code: str = Field(..., description="Bank identification code")
    account_type: AccountType = Field(..., description="Account type (DR/CR)")
    account_name: str = Field(..., description="Account holder name")
    currency: str = Field(default="EUR", description="Account currency")
    is_active: bool = Field(default=True, description="Account status")
    
    # Validation flags
    is_valid_iban: bool = Field(default=True, description="IBAN validation status")
    is_valid_bank_code: bool = Field(default=True, description="Bank code validation status")
    
    class Config:
        use_enum_values = True


class ValidationError(BaseModel):
    """Validation error details"""
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Human readable error message")
    field_name: str = Field(..., description="Field that failed validation")
    current_value: Optional[str] = Field(None, description="Current invalid value")


class PaymentTransaction(BaseModel):
    """Payment transaction model"""
    transaction_id: str = Field(..., description="Unique transaction identifier")
    debitor_account: Account = Field(..., description="Debitor account details")
    creditor_account: Account = Field(..., description="Creditor account details")
    amount: float = Field(..., description="Transaction amount")
    currency: str = Field(default="EUR", description="Transaction currency")
    clearing_type: ClearingType = Field(..., description="Clearing mechanism")
    message_type: MessageType = Field(..., description="Message format type")
    transaction_date: datetime = Field(default_factory=datetime.now)
    
    # Status tracking
    validation_status: str = Field(default="PENDING", description="Validation status")
    repair_attempts: int = Field(default=0, description="Number of repair attempts")
    is_manually_repaired: bool = Field(default=False, description="Manual repair flag")
    
    class Config:
        use_enum_values = True