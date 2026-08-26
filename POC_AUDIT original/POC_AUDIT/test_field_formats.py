#!/usr/bin/env python3
"""Test script to verify both field name formats work"""

import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ai.groq_analyzer import GroqAnalyzer

# Test data with "oldAccount" format (user's format)
test_data_format1 = [
    {
        "log_type": "CR_ACCOUNT_MANUAL_REPAIR",
        "clearing_type": "FEDNW", 
        "message_type": "pacs.008.001.08",
        "oldAccount": "892434389",
        "newAccount": "1892434389",
        "oldIban": "",
        "newIban": ""
    },
    {
        "log_type": "",
        "clearing_type": "",
        "message_type": "",
        "oldAccount": "",
        "newAccount": "",
        "oldIban": "",
        "newIban": ""
    }
]

# Test data with "old_account_id" format (sample data format) 
test_data_format2 = [
    {
        "log_type": "CR_ACCOUNT_MANUAL_REPAIR",
        "clearing_type": "FEDNW",
        "message_type": "pacs.008.001.08", 
        "old_account_id": "892434389",
        "new_account_id": "1892434389",
        "old_iban": "",
        "new_iban": ""
    },
    {
        "log_type": "",
        "clearing_type": "",
        "message_type": "",
        "old_account_id": "", 
        "new_account_id": "",
        "old_iban": "",
        "new_iban": ""
    }
]

analyzer = GroqAnalyzer()

print("Testing Format 1: oldAccount/newAccount (User format)")
print("="*60)
result1 = analyzer.analyze_manual_repairs(test_data_format1)
print(f"Patterns: {len(result1.patterns)}")
print(f"Confidence: {result1.confidence:.1f}%")
if result1.automation_opportunities:
    for opp in result1.automation_opportunities:
        print(f"Automation Rate: {opp.get('automation_rate', 'N/A')}")

print("\nTesting Format 2: old_account_id/new_account_id (Sample format)")
print("="*60) 
result2 = analyzer.analyze_manual_repairs(test_data_format2)
print(f"Patterns: {len(result2.patterns)}")
print(f"Confidence: {result2.confidence:.1f}%")
if result2.automation_opportunities:
    for opp in result2.automation_opportunities:
        print(f"Automation Rate: {opp.get('automation_rate', 'N/A')}")

print(f"\nBoth formats should show ~100% automation rate!")