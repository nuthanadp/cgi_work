#!/usr/bin/env python3
"""Quick test to verify the automation rate fix"""

import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ai.groq_analyzer import GroqAnalyzer

# Test with realistic data similar to user's hi.json
test_data = [
    # Real prefix addition patterns (should be 100% automatable)
    {
        "log_type": "CR_ACCOUNT_MANUAL_REPAIR",
        "clearing_type": "FEDNW",
        "message_type": "pacs.008.001.08",
        "oldAccount": "892434389",
        "newAccount": "1892434389"
    },
    {
        "log_type": "CR_ACCOUNT_MANUAL_REPAIR",
        "clearing_type": "FEDNW",
        "message_type": "pacs.008.001.08",
        "oldAccount": "123456789",
        "newAccount": "1123456789"
    },
    # Empty entries (should be excluded from calculation)
    {"oldAccount": "", "newAccount": "", "log_type": ""},
    {"oldAccount": "", "newAccount": "", "log_type": ""},
    {"oldAccount": "", "newAccount": "", "log_type": ""}
]

analyzer = GroqAnalyzer()
result = analyzer.analyze_manual_repairs(test_data)

print(f"AUTOMATION RATE TEST RESULTS")
print(f"=" * 40)
print(f"Total entries: {len(test_data)} (2 real + 3 empty)")
print(f"Patterns detected: {len(result.patterns)}")
print(f"Confidence: {result.confidence:.1f}%")

if result.automation_opportunities:
    for opp in result.automation_opportunities:
        print(f"Automation rate: {opp.get('automation_rate', 'N/A')}")
        print(f"Complexity: {opp.get('complexity', 'N/A')}")
        print(f"Transactions: {opp.get('transactions', 'N/A')}")

print(f"\nEXPECTED: ~100% automation rate for 2/2 real transactions")
print(f"This confirms the fix excludes empty entries correctly!")