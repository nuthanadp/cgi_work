#!/usr/bin/env python3
"""Debug script to trace exactly what's happening in the Streamlit analysis"""

import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ai.groq_analyzer import GroqAnalyzer

# Try to load the actual hi.json data if it exists
try:
    with open('hi.json', 'r') as f:
        actual_data = json.load(f)
    print(f"Loaded hi.json with {len(actual_data)} entries")
    
    # Show first few entries to understand structure
    print("\nFirst 3 entries:")
    for i, entry in enumerate(actual_data[:3]):
        print(f"Entry {i+1}: {entry}")
    
    # Check for empty entries
    empty_count = sum(1 for entry in actual_data 
                     if not entry.get('oldAccount', '').strip() and 
                        not entry.get('newAccount', '').strip())
    print(f"\nEmpty entries: {empty_count}/{len(actual_data)}")
    
except FileNotFoundError:
    print("hi.json not found, creating sample data...")
    actual_data = [
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

print("\n" + "="*60)
print("DEBUGGING GROQ ANALYZER")
print("="*60)

# Test with GroqAnalyzer (same as Streamlit)
analyzer = GroqAnalyzer()
result = analyzer.analyze_manual_repairs(actual_data)

print(f"\nAnalysis Results:")
print(f"Patterns detected: {len(result.patterns)}")
print(f"Confidence: {result.confidence:.1f}%")
print(f"Automation opportunities: {len(result.automation_opportunities)}")

if result.automation_opportunities:
    for i, opp in enumerate(result.automation_opportunities):
        print(f"\nOpportunity {i+1}:")
        for key, value in opp.items():
            print(f"  {key}: {value}")

if hasattr(result, 'summary_stats') and result.summary_stats:
    print(f"\nSummary stats: {result.summary_stats}")