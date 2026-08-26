#!/usr/bin/env python3
"""Test script to verify groq_analyzer fixes"""

import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ai.groq_analyzer import GroqPatternAnalyzer

# Create test data matching hi.json structure
test_data = [
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
        "log_type": "CR_ACCOUNT_MANUAL_REPAIR",
        "clearing_type": "FEDNW", 
        "message_type": "pacs.008.001.08",
        "oldAccount": "892434390",
        "newAccount": "1892434390",
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

print("Testing Groq Analyzer with corrected field names...")
print(f"Test data: {len(test_data)} entries (2 real transactions + 1 empty)")

analyzer = GroqPatternAnalyzer()
result = analyzer.analyze_manual_repairs(test_data)

print(f"\nResults:")
print(f"Patterns detected: {len(result.patterns)}")
print(f"Confidence: {result.confidence:.1f}%")

if result.automation_opportunities:
    for opp in result.automation_opportunities:
        print(f"Automation rate: {opp.get('automation_rate', 'N/A')}")
        print(f"Transactions: {opp.get('transactions', 'N/A')}")
        
print(f"\nExpected: 100% automation rate for 2/2 real transactions")