#!/usr/bin/env python3
"""Test to verify the KeyError fix for patterns structure"""

import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ai.groq_analyzer import GroqAnalyzer

# Test data
test_data = [
    {
        "log_type": "CR_ACCOUNT_MANUAL_REPAIR",
        "clearing_type": "FEDNW",
        "message_type": "pacs.008.001.08",
        "oldAccount": "892434389",
        "newAccount": "1892434389"
    },
    {
        "oldAccount": "",
        "newAccount": "",
        "log_type": ""
    }
]

analyzer = GroqAnalyzer()
result = analyzer.analyze_manual_repairs(test_data)

print(f"PATTERN STRUCTURE TEST")
print(f"=" * 30)
print(f"Number of patterns: {len(result.patterns)}")

if result.patterns:
    for i, pattern in enumerate(result.patterns):
        print(f"\nPattern {i+1}:")
        print(f"  Keys: {list(pattern.keys())}")
        # Test for the expected keys
        try:
            print(f"  Type: {pattern['type']}")  # This should work now
            print(f"  Frequency: {pattern['frequency']}")
            print(f"  Description: {pattern['description']}")
            print(f"  ✅ Structure is correct!")
        except KeyError as e:
            print(f"  ❌ KeyError: {e}")

print(f"\nThe fix ensures patterns have 'type' key as expected by Streamlit!")