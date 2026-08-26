"""
Configuration settings for the APS system
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


class APSConfig:
    """Configuration class for APS settings"""
    
    # Database settings
    DATABASE_PATH = os.getenv("APS_DATABASE_PATH", "data/aps_database.sqlite")
    AUDIT_LOG_PATH = os.getenv("APS_AUDIT_LOG_PATH", "data/audit_logs.json")
    
    # AI Analysis settings - Updated for Groq AI and Phi-3
    USE_GROQ = True  # Enable Groq AI analysis
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")  # Set via environment variable
    GROQ_MODEL = "llama3-8b-8192"  # Fast and efficient Llama model
    
    # Microsoft Phi-3 Configuration
    USE_PHI3 = True  # Enable Phi-3 local analysis
    PHI3_MODEL = "microsoft/Phi-3-mini-4k-instruct"
    PHI3_DEVICE = "auto"  # auto, cpu, or cuda
    PHI3_MAX_TOKENS = 1000
    PHI3_TEMPERATURE = 0.3
    
    # Legacy Gemini settings (kept for compatibility)
    USE_GEMINI = os.getenv("APS_USE_GEMINI", "false").lower() == "true"
    GEMINI_API_KEY = os.getenv("APS_GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("APS_GEMINI_MODEL", "gemini-1.5-flash")
    
    MIN_PATTERN_FREQUENCY = int(os.getenv("APS_MIN_PATTERN_FREQUENCY", "3"))
    MIN_AUTOMATION_SCORE = float(os.getenv("APS_MIN_AUTOMATION_SCORE", "0.6"))
    CLUSTERING_EPS = float(os.getenv("APS_CLUSTERING_EPS", "0.3"))
    
    # Gemini AI settings
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.2"))
    USE_GEMINI = bool(GEMINI_API_KEY)
    
    # Repair engine settings
    MAX_AUTO_REPAIR_ATTEMPTS = int(os.getenv("APS_MAX_AUTO_REPAIR_ATTEMPTS", "3"))
    ENABLE_AUTO_REPAIR = os.getenv("APS_ENABLE_AUTO_REPAIR", "true").lower() == "true"
    
    # API settings
    API_HOST = os.getenv("APS_API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("APS_API_PORT", "8000"))
    API_DEBUG = os.getenv("APS_API_DEBUG", "false").lower() == "true"
    
    # Validation settings
    SUPPORTED_COUNTRIES = ["DE", "FR", "GB", "US", "NL"]
    SUPPORTED_CURRENCIES = ["EUR", "USD", "GBP"]
    
    # Risk thresholds
    HIGH_VALUE_THRESHOLD = float(os.getenv("APS_HIGH_VALUE_THRESHOLD", "50000.00"))
    RISK_SCORE_THRESHOLD = float(os.getenv("APS_RISK_SCORE_THRESHOLD", "0.7"))
    
    @classmethod
    def get_all_settings(cls) -> Dict[str, Any]:
        """Get all configuration settings as a dictionary"""
        return {
            "database_path": cls.DATABASE_PATH,
            "audit_log_path": cls.AUDIT_LOG_PATH,
            "min_pattern_frequency": cls.MIN_PATTERN_FREQUENCY,
            "min_automation_score": cls.MIN_AUTOMATION_SCORE,
            "clustering_eps": cls.CLUSTERING_EPS,
            "max_auto_repair_attempts": cls.MAX_AUTO_REPAIR_ATTEMPTS,
            "enable_auto_repair": cls.ENABLE_AUTO_REPAIR,
            "api_host": cls.API_HOST,
            "api_port": cls.API_PORT,
            "api_debug": cls.API_DEBUG,
            "supported_countries": cls.SUPPORTED_COUNTRIES,
            "supported_currencies": cls.SUPPORTED_CURRENCIES,
            "high_value_threshold": cls.HIGH_VALUE_THRESHOLD,
            "risk_score_threshold": cls.RISK_SCORE_THRESHOLD
        }
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration settings"""
        try:
            # Check required paths exist or can be created
            import pathlib
            pathlib.Path(cls.DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
            pathlib.Path(cls.AUDIT_LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
            
            # Validate numeric ranges
            assert 0 < cls.MIN_AUTOMATION_SCORE <= 1.0, "MIN_AUTOMATION_SCORE must be between 0 and 1"
            assert 0 < cls.CLUSTERING_EPS <= 1.0, "CLUSTERING_EPS must be between 0 and 1"
            assert cls.MIN_PATTERN_FREQUENCY >= 2, "MIN_PATTERN_FREQUENCY must be at least 2"
            
            return True
        except Exception as e:
            print(f"Configuration validation failed: {e}")
            return False


# Environment-specific configurations
DEVELOPMENT_CONFIG = {
    "database_path": "data/dev_database.sqlite",
    "audit_log_path": "data/dev_audit_logs.json",
    "api_debug": True,
    "min_pattern_frequency": 2,
    "enable_auto_repair": True
}

PRODUCTION_CONFIG = {
    "database_path": "/var/lib/aps/database.sqlite", 
    "audit_log_path": "/var/log/aps/audit_logs.json",
    "api_debug": False,
    "min_pattern_frequency": 5,
    "enable_auto_repair": True,
    "api_host": "127.0.0.1"
}

TEST_CONFIG = {
    "database_path": "tests/test_database.sqlite",
    "audit_log_path": "tests/test_audit_logs.json", 
    "api_debug": True,
    "min_pattern_frequency": 1,
    "enable_auto_repair": False
}