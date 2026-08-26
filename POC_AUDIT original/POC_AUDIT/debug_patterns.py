import json

# Load and analyze the data
data = json.load(open('c:/Users/sanjukta.das/Downloads/hi.json'))
print(f'Total entries: {len(data)}')

print('\nFirst 5 entries:')
for i, entry in enumerate(data[:5]):
    old_acc = entry.get('old_account_id', '')
    new_acc = entry.get('new_account_id', '')
    old_iban = entry.get('old_iban', '')
    new_iban = entry.get('new_iban', '')
    print(f'{i+1}. Account: {old_acc} → {new_acc}')
    print(f'   IBAN: "{old_iban}" → "{new_iban}"')

# Count patterns
patterns = {}
iban_patterns = {}

for entry in data:
    old_acc = str(entry.get('old_account_id', ''))
    new_acc = str(entry.get('new_account_id', ''))
    old_iban = entry.get('old_iban', '')
    new_iban = entry.get('new_iban', '')
    
    # Account patterns
    if old_acc != new_acc:
        if new_acc.endswith(old_acc) and len(new_acc) > len(old_acc):
            prefix = new_acc[:-len(old_acc)]
            pattern = f'account_prefix_addition_{prefix}'
            patterns[pattern] = patterns.get(pattern, 0) + 1
    
    # IBAN patterns  
    if old_iban != new_iban:
        if old_iban and new_iban:
            iban_patterns['iban_change'] = iban_patterns.get('iban_change', 0) + 1
        elif old_iban and not new_iban:
            iban_patterns['iban_removal'] = iban_patterns.get('iban_removal', 0) + 1
        elif not old_iban and new_iban:
            iban_patterns['iban_addition'] = iban_patterns.get('iban_addition', 0) + 1

print(f'\nAccount patterns: {patterns}')
print(f'IBAN patterns: {iban_patterns}')
print(f'Account pattern coverage: {sum(patterns.values())}/{len(data)} = {sum(patterns.values())/len(data)*100:.1f}%')

# Check if there's a dominant pattern
if patterns:
    dominant_pattern = max(patterns, key=patterns.get)
    dominant_count = patterns[dominant_pattern]
    automation_rate = (dominant_count / len(data)) * 100
    print(f'Dominant pattern: {dominant_pattern} ({dominant_count} occurrences)')
    print(f'Real automation rate should be: {automation_rate:.1f}%')