"""
Database storage layer for the APS system
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import uuid

from ..models import (
    PaymentTransaction, ManualRepairAuditLog, RepairRule, SuggestedRule,
    Account, ValidationError
)


class DatabaseManager:
    """Database manager for APS data persistence"""
    
    def __init__(self, db_path: str = "data/aps_database.sqlite"):
        self.db_path = db_path
        self._ensure_db_directory()
        self._initialize_database()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def _initialize_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Payment transactions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payment_transactions (
                    transaction_id TEXT PRIMARY KEY,
                    debitor_account TEXT NOT NULL,
                    creditor_account TEXT NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT NOT NULL,
                    clearing_type TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    transaction_date TEXT NOT NULL,
                    validation_status TEXT NOT NULL,
                    repair_attempts INTEGER DEFAULT 0,
                    is_manually_repaired BOOLEAN DEFAULT FALSE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Manual repair audit logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS manual_repair_logs (
                    log_id TEXT PRIMARY KEY,
                    log_type TEXT NOT NULL,
                    transaction_id TEXT NOT NULL,
                    clearing_type TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    old_account_id TEXT NOT NULL,
                    old_iban TEXT NOT NULL,
                    new_account_id TEXT NOT NULL,
                    new_iban TEXT NOT NULL,
                    repaired_by TEXT NOT NULL,
                    repair_timestamp TEXT NOT NULL,
                    repair_reason TEXT,
                    validation_errors TEXT,
                    auto_repair_attempts INTEGER DEFAULT 0,
                    additional_data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Repair rules table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS repair_rules (
                    rule_id TEXT PRIMARY KEY,
                    rule_name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    clearing_types TEXT,
                    message_types TEXT,
                    account_types TEXT,
                    conditions TEXT NOT NULL,
                    actions TEXT NOT NULL,
                    priority INTEGER DEFAULT 100,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_date TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Suggested rules table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS suggested_rules (
                    suggestion_id TEXT PRIMARY KEY,
                    suggested_rule_id TEXT NOT NULL,
                    confidence_score REAL NOT NULL,
                    pattern_frequency INTEGER NOT NULL,
                    manual_repair_count INTEGER NOT NULL,
                    supporting_cases TEXT NOT NULL,
                    feasibility_score REAL NOT NULL,
                    risk_level TEXT NOT NULL,
                    status TEXT DEFAULT 'PENDING',
                    reviewed_by TEXT,
                    review_date TEXT,
                    review_notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Validation errors table (for tracking error patterns)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS validation_errors (
                    error_id TEXT PRIMARY KEY,
                    transaction_id TEXT NOT NULL,
                    account_type TEXT NOT NULL,
                    error_code TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    field_name TEXT NOT NULL,
                    current_value TEXT,
                    error_timestamp TEXT NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE
                )
            ''')
            
            conn.commit()
    
    def save_payment_transaction(self, transaction: PaymentTransaction) -> bool:
        """Save a payment transaction to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO payment_transactions 
                    (transaction_id, debitor_account, creditor_account, amount, currency,
                     clearing_type, message_type, transaction_date, validation_status,
                     repair_attempts, is_manually_repaired)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    transaction.transaction_id,
                    json.dumps(transaction.debitor_account.dict()),
                    json.dumps(transaction.creditor_account.dict()),
                    transaction.amount,
                    transaction.currency,
                    transaction.clearing_type,
                    transaction.message_type,
                    transaction.transaction_date.isoformat(),
                    transaction.validation_status,
                    transaction.repair_attempts,
                    transaction.is_manually_repaired
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving payment transaction: {e}")
            return False
    
    def get_payment_transaction(self, transaction_id: str) -> Optional[PaymentTransaction]:
        """Retrieve a payment transaction by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT * FROM payment_transactions WHERE transaction_id = ?',
                    (transaction_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_payment_transaction(row)
                return None
        except Exception as e:
            print(f"Error retrieving payment transaction: {e}")
            return None
    
    def save_manual_repair_log(self, log: ManualRepairAuditLog) -> bool:
        """Save a manual repair audit log"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO manual_repair_logs 
                    (log_id, log_type, transaction_id, clearing_type, message_type,
                     old_account_id, old_iban, new_account_id, new_iban, repaired_by,
                     repair_timestamp, repair_reason, validation_errors, 
                     auto_repair_attempts, additional_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    log.log_id,
                    log.log_type,
                    log.transaction_id,
                    log.clearing_type,
                    log.message_type,
                    log.old_account_id,
                    log.old_iban,
                    log.new_account_id,
                    log.new_iban,
                    log.repaired_by,
                    log.repair_timestamp.isoformat(),
                    log.repair_reason,
                    json.dumps(log.validation_errors) if log.validation_errors else None,
                    log.auto_repair_attempts,
                    json.dumps(log.additional_data) if log.additional_data else None
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving manual repair log: {e}")
            return False
    
    def get_manual_repair_logs(self, limit: int = 100, offset: int = 0) -> List[ManualRepairAuditLog]:
        """Get manual repair logs with pagination"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM manual_repair_logs 
                    ORDER BY repair_timestamp DESC 
                    LIMIT ? OFFSET ?
                ''', (limit, offset))
                
                rows = cursor.fetchall()
                return [self._row_to_manual_repair_log(row) for row in rows]
        except Exception as e:
            print(f"Error retrieving manual repair logs: {e}")
            return []
    
    def get_repair_logs_by_date_range(self, start_date: datetime, 
                                    end_date: datetime) -> List[ManualRepairAuditLog]:
        """Get repair logs within a date range"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM manual_repair_logs 
                    WHERE repair_timestamp BETWEEN ? AND ?
                    ORDER BY repair_timestamp DESC
                ''', (start_date.isoformat(), end_date.isoformat()))
                
                rows = cursor.fetchall()
                return [self._row_to_manual_repair_log(row) for row in rows]
        except Exception as e:
            print(f"Error retrieving repair logs by date range: {e}")
            return []
    
    def save_repair_rule(self, rule: RepairRule) -> bool:
        """Save a repair rule"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO repair_rules
                    (rule_id, rule_name, description, clearing_types, message_types,
                     account_types, conditions, actions, priority, is_active,
                     created_date, created_by, success_count, failure_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    rule.rule_id,
                    rule.rule_name,
                    rule.description,
                    json.dumps([ct.value for ct in rule.clearing_types]),
                    json.dumps([mt.value for mt in rule.message_types]),
                    json.dumps([at.value for at in rule.account_types]),
                    json.dumps([c.dict() for c in rule.conditions]),
                    json.dumps([a.dict() for a in rule.actions]),
                    rule.priority,
                    rule.is_active,
                    rule.created_date.isoformat(),
                    rule.created_by,
                    rule.success_count,
                    rule.failure_count
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving repair rule: {e}")
            return False
    
    def get_repair_rules(self, active_only: bool = True) -> List[RepairRule]:
        """Get repair rules"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if active_only:
                    cursor.execute('SELECT * FROM repair_rules WHERE is_active = TRUE')
                else:
                    cursor.execute('SELECT * FROM repair_rules')
                
                rows = cursor.fetchall()
                return [self._row_to_repair_rule(row) for row in rows]
        except Exception as e:
            print(f"Error retrieving repair rules: {e}")
            return []
    
    def save_suggested_rule(self, suggestion: SuggestedRule) -> bool:
        """Save a suggested rule"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # First save the repair rule
                self.save_repair_rule(suggestion.suggested_rule)
                
                # Then save the suggestion metadata
                cursor.execute('''
                    INSERT OR REPLACE INTO suggested_rules
                    (suggestion_id, suggested_rule_id, confidence_score, pattern_frequency,
                     manual_repair_count, supporting_cases, feasibility_score, risk_level,
                     status, reviewed_by, review_date, review_notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    suggestion.suggestion_id,
                    suggestion.suggested_rule.rule_id,
                    suggestion.confidence_score,
                    suggestion.pattern_frequency,
                    suggestion.manual_repair_count,
                    json.dumps(suggestion.supporting_cases),
                    suggestion.feasibility_score,
                    suggestion.risk_level,
                    suggestion.status,
                    suggestion.reviewed_by,
                    suggestion.review_date.isoformat() if suggestion.review_date else None,
                    suggestion.review_notes
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving suggested rule: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count records in each table
                stats = {}
                
                cursor.execute('SELECT COUNT(*) FROM payment_transactions')
                stats['payment_transactions'] = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM manual_repair_logs')
                stats['manual_repair_logs'] = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM repair_rules')
                stats['repair_rules'] = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM suggested_rules')
                stats['suggested_rules'] = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM validation_errors')
                stats['validation_errors'] = cursor.fetchone()[0]
                
                # Get recent activity
                cursor.execute('''
                    SELECT COUNT(*) FROM manual_repair_logs 
                    WHERE repair_timestamp > datetime('now', '-7 days')
                ''')
                stats['repairs_last_7_days'] = cursor.fetchone()[0]
                
                return stats
        except Exception as e:
            print(f"Error getting database stats: {e}")
            return {}
    
    def _row_to_payment_transaction(self, row) -> PaymentTransaction:
        """Convert database row to PaymentTransaction"""
        # Simplified conversion for POC
        from ..models import Account
        
        debitor_data = json.loads(row[1])
        creditor_data = json.loads(row[2])
        
        return PaymentTransaction(
            transaction_id=row[0],
            debitor_account=Account(**debitor_data),
            creditor_account=Account(**creditor_data),
            amount=row[3],
            currency=row[4],
            clearing_type=row[5],
            message_type=row[6],
            transaction_date=datetime.fromisoformat(row[7]),
            validation_status=row[8],
            repair_attempts=row[9],
            is_manually_repaired=row[10]
        )
    
    def _row_to_manual_repair_log(self, row) -> ManualRepairAuditLog:
        """Convert database row to ManualRepairAuditLog"""
        validation_errors = json.loads(row[12]) if row[12] else None
        additional_data = json.loads(row[14]) if row[14] else None
        
        return ManualRepairAuditLog(
            log_id=row[0],
            log_type=row[1],
            transaction_id=row[2],
            clearing_type=row[3],
            message_type=row[4],
            old_account_id=row[5],
            old_iban=row[6],
            new_account_id=row[7],
            new_iban=row[8],
            repaired_by=row[9],
            repair_timestamp=datetime.fromisoformat(row[10]),
            repair_reason=row[11],
            validation_errors=validation_errors,
            auto_repair_attempts=row[13],
            additional_data=additional_data
        )
    
    def _row_to_repair_rule(self, row) -> RepairRule:
        """Convert database row to RepairRule"""
        from ..models import RuleCondition, RuleAction
        
        clearing_types = [ClearingType(ct) for ct in json.loads(row[3])]
        message_types = [MessageType(mt) for mt in json.loads(row[4])]
        account_types = [AccountType(at) for at in json.loads(row[5])]
        conditions = [RuleCondition(**c) for c in json.loads(row[6])]
        actions = [RuleAction(**a) for a in json.loads(row[7])]
        
        return RepairRule(
            rule_id=row[0],
            rule_name=row[1],
            description=row[2],
            clearing_types=clearing_types,
            message_types=message_types,
            account_types=account_types,
            conditions=conditions,
            actions=actions,
            priority=row[8],
            is_active=row[9],
            created_date=datetime.fromisoformat(row[10]),
            created_by=row[11],
            success_count=row[12],
            failure_count=row[13]
        )
    
    def export_data(self, table_name: str, output_file: str) -> bool:
        """Export table data to JSON file"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f'SELECT * FROM {table_name}')
                
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                
                data = []
                for row in rows:
                    data.append(dict(zip(columns, row)))
                
                with open(output_file, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
                
                return True
        except Exception as e:
            print(f"Error exporting data: {e}")
            return False