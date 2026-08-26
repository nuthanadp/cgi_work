import json

# Load and analyze the data more thoroughly
data = json.load(open('c:/Users/sanjukta.das/Downloads/hi.json'))
print(f'Total entries: {len(data)}')

print('\nDetailed analysis of first 10 entries:')
for i, entry in enumerate(data[:10]):
    old_acc = str(entry.get('old_account_id', ''))
    new_acc = str(entry.get('new_account_id', ''))
    old_iban = entry.get('old_iban', '')
    new_iban = entry.get('new_iban', '')
    
    print(f'{i+1}. Account: "{old_acc}" → "{new_acc}" (lengths: {len(old_acc)}, {len(new_acc)})')
    if new_acc.endswith(old_acc):
        prefix = new_acc[:-len(old_acc)]
        print(f'   ✓ Prefix addition: "{prefix}"')
    else:
        print(f'   ❌ No prefix pattern detected')
    
    if old_iban == new_iban == '':
        print(f'   ✓ IBAN: both empty (no change)')
    else:
        print(f'   IBAN: "{old_iban}" → "{new_iban}"')

# Check ALL entries for account patterns
account_changes = 0
prefix_1_additions = 0
other_patterns = []

for entry in data:
    old_acc = str(entry.get('old_account_id', ''))
    new_acc = str(entry.get('new_account_id', ''))
    
    if old_acc != new_acc:
        account_changes += 1
        if new_acc.endswith(old_acc) and len(new_acc) > len(old_acc):
            prefix = new_acc[:-len(old_acc)]
            if prefix == '1':
                prefix_1_additions += 1
            else:
                other_patterns.append(f'{old_acc}→{new_acc} (prefix: {prefix})')

print(f'\nSUMMARY:')
print(f'Total account changes: {account_changes}/78')
print(f'Prefix "1" additions: {prefix_1_additions}/78')
print(f'Other patterns: {len(other_patterns)}')
if other_patterns:
    print('Other patterns found:')
    for pattern in other_patterns[:5]:
        print(f'  {pattern}')

if prefix_1_additions > 0:
    real_automation_rate = (prefix_1_additions / len(data)) * 100
    print(f'\nREAL AUTOMATION RATE should be: {real_automation_rate:.1f}%')
    if real_automation_rate > 90:
        print('→ This should be classified as "Very High" automation potential!')