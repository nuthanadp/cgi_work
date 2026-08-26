"""
Account validator module for validating bank accounts and IBANs
"""

import re
from typing import List, Tuple, Optional
from models import Account, ValidationError, ClearingType, MessageType


class AccountValidator:
    """Validates bank accounts and IBANs according to various rules"""
    
    # IBAN country code patterns (simplified for POC)
    IBAN_PATTERNS = {
        'DE': r'^DE\d{2}\d{8}\d{10}$',  # Germany
        'FR': r'^FR\d{2}\d{5}\d{5}\d{11}\d{2}$',  # France
        'GB': r'^GB\d{2}[A-Z]{4}\d{6}\d{8}$',  # UK
        'US': r'^US\d{2}\d{9}\d{9}$',  # USA (simplified)
        'NL': r'^NL\d{2}[A-Z]{4}\d{10}$',  # Netherlands
    }
    
    # Bank codes by country (simplified mapping)
    BANK_CODES = {
        'DE': ['12345678', '87654321', '11111111'],
        'FR': ['30004', '30003', '20041'],
        'GB': ['BARC', 'HSBC', 'LLOY'],
        'US': ['021000021', '111000025', '026009593'],
        'NL': ['ABNA', 'INGB', 'RABO']
    }
    
    def __init__(self):
        self.validation_errors = []
    
    def validate_account(self, account: Account, clearing_type: ClearingType, 
                        message_type: MessageType) -> Tuple[bool, List[ValidationError]]:
        """
        Validate a bank account
        
        Args:
            account: Account to validate
            clearing_type: Type of clearing being performed
            message_type: Message format being used
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # IBAN validation
        iban_errors = self._validate_iban(account.iban)
        errors.extend(iban_errors)
        
        # Bank code validation
        bank_code_errors = self._validate_bank_code(account.bank_code, account.iban)
        errors.extend(bank_code_errors)
        
        # Account specific validation
        account_errors = self._validate_account_specific(account, clearing_type, message_type)
        errors.extend(account_errors)
        
        # Cross-field validation
        cross_field_errors = self._validate_cross_fields(account, clearing_type)
        errors.extend(cross_field_errors)
        
        return len(errors) == 0, errors
    
    def _validate_iban(self, iban: str) -> List[ValidationError]:
        """Validate IBAN format and structure"""
        errors = []
        
        if not iban:
            errors.append(ValidationError(
                error_code="IBAN_EMPTY",
                error_message="IBAN cannot be empty",
                field_name="iban",
                current_value=iban
            ))
            return errors
        
        # Remove spaces and convert to uppercase
        clean_iban = iban.replace(' ', '').upper()
        
        # Check length
        if len(clean_iban) < 15 or len(clean_iban) > 34:
            errors.append(ValidationError(
                error_code="IBAN_INVALID_LENGTH",
                error_message="IBAN must be between 15 and 34 characters",
                field_name="iban",
                current_value=iban
            ))
        
        # Check country code
        if len(clean_iban) >= 2:
            country_code = clean_iban[:2]
            if country_code in self.IBAN_PATTERNS:
                pattern = self.IBAN_PATTERNS[country_code]
                if not re.match(pattern, clean_iban):
                    errors.append(ValidationError(
                        error_code="IBAN_INVALID_FORMAT",
                        error_message=f"IBAN format invalid for country {country_code}",
                        field_name="iban",
                        current_value=iban
                    ))
            else:
                errors.append(ValidationError(
                    error_code="IBAN_UNSUPPORTED_COUNTRY",
                    error_message=f"Country code {country_code} not supported",
                    field_name="iban",
                    current_value=iban
                ))
        
        return errors
    
    def _validate_bank_code(self, bank_code: str, iban: str) -> List[ValidationError]:
        """Validate bank code against IBAN country"""
        errors = []
        
        if not bank_code:
            errors.append(ValidationError(
                error_code="BANK_CODE_EMPTY",
                error_message="Bank code cannot be empty",
                field_name="bank_code",
                current_value=bank_code
            ))
            return errors
        
        # Extract country from IBAN
        if len(iban) >= 2:
            country_code = iban[:2].upper()
            if country_code in self.BANK_CODES:
                valid_codes = self.BANK_CODES[country_code]
                if bank_code not in valid_codes:
                    errors.append(ValidationError(
                        error_code="BANK_CODE_INVALID",
                        error_message=f"Bank code {bank_code} not valid for country {country_code}",
                        field_name="bank_code",
                        current_value=bank_code
                    ))
        
        return errors
    
    def _validate_account_specific(self, account: Account, clearing_type: ClearingType,
                                 message_type: MessageType) -> List[ValidationError]:
        """Validate account-specific rules based on clearing and message type"""
        errors = []
        
        # High value clearing requires additional validation
        if clearing_type == ClearingType.HIGH_VALUE:
            if not account.account_name or len(account.account_name.strip()) < 3:
                errors.append(ValidationError(
                    error_code="HIGH_VALUE_NAME_REQUIRED",
                    error_message="High value transactions require full account name",
                    field_name="account_name",
                    current_value=account.account_name
                ))
        
        # International clearing requires SWIFT compliance
        if clearing_type == ClearingType.INTERNATIONAL:
            if message_type in [MessageType.SWIFT_MT103, MessageType.SWIFT_MT202]:
                # SWIFT messages require specific format compliance
                if len(account.iban) < 20:  # Simplified check
                    errors.append(ValidationError(
                        error_code="SWIFT_IBAN_TOO_SHORT",
                        error_message="SWIFT messages require fully qualified IBAN",
                        field_name="iban",
                        current_value=account.iban
                    ))
        
        return errors
    
    def _validate_cross_fields(self, account: Account, clearing_type: ClearingType) -> List[ValidationError]:
        """Validate relationships between different fields"""
        errors = []
        
        # Check if IBAN country matches expected bank code country
        if len(account.iban) >= 2 and account.bank_code:
            iban_country = account.iban[:2].upper()
            if iban_country == 'DE' and not account.bank_code.isdigit():
                errors.append(ValidationError(
                    error_code="CROSS_FIELD_COUNTRY_MISMATCH",
                    error_message="German IBANs require numeric bank codes",
                    field_name="bank_code",
                    current_value=account.bank_code
                ))
            elif iban_country == 'GB' and account.bank_code.isdigit():
                errors.append(ValidationError(
                    error_code="CROSS_FIELD_COUNTRY_MISMATCH",
                    error_message="UK IBANs require alphabetic bank codes",
                    field_name="bank_code", 
                    current_value=account.bank_code
                ))
        
        return errors
    
    def get_suggested_fixes(self, errors: List[ValidationError], account: Account) -> List[str]:
        """Suggest potential fixes for validation errors"""
        suggestions = []
        
        for error in errors:
            if error.error_code == "IBAN_INVALID_FORMAT":
                suggestions.append(f"Check IBAN format for country {account.iban[:2] if account.iban else 'unknown'}")
            elif error.error_code == "BANK_CODE_INVALID":
                country = account.iban[:2] if len(account.iban) >= 2 else "unknown"
                if country in self.BANK_CODES:
                    valid_codes = ", ".join(self.BANK_CODES[country][:3])
                    suggestions.append(f"Valid bank codes for {country}: {valid_codes}")
            elif error.error_code == "CROSS_FIELD_COUNTRY_MISMATCH":
                suggestions.append("Ensure bank code format matches IBAN country requirements")
        
        return suggestions