import json

# Load and analyze ALL entries in detail
data = json.load(open('c:/Users/sanjukta.das/Downloads/hi.json'))

# Categorize all entries
no_account_changes = []
prefix_additions = []
other_changes = []

for i, entry in enumerate(data):
    old_acc = str(entry.get('old_account_id', ''))
    new_acc = str(entry.get('new_account_id', ''))
    
    if old_acc == new_acc:
        no_account_changes.append(f'{i+1}. {old_acc} (no change)')
    elif new_acc.endswith(old_acc) and len(new_acc) > len(old_acc):
        prefix = new_acc[:-len(old_acc)]
        if prefix == '1':
            prefix_additions.append(f'{i+1}. {old_acc} → {new_acc}')
        else:
            other_changes.append(f'{i+1}. {old_acc} → {new_acc} (prefix: {prefix})')
    else:
        other_changes.append(f'{i+1}. {old_acc} → {new_acc} (other change)')

print(f'CATEGORIZATION OF ALL 78 ENTRIES:')
print(f'No account changes: {len(no_account_changes)}')
print(f'Prefix "1" additions: {len(prefix_additions)}') 
print(f'Other changes: {len(other_changes)}')

if no_account_changes:
    print(f'\nSample entries with NO account changes:')
    for entry in no_account_changes[:5]:
        print(f'  {entry}')

if len(no_account_changes) > 10:
    print(f'\nERROR: {len(no_account_changes)} entries have no account changes!')
    print('This suggests the data might not be what was expected.')
    
    # Check a few specific entries
    print('\nChecking specific entries from the dataset:')
    for i in range(0, min(78, 78), 10):
        entry = data[i]
        old_acc = entry.get('old_account_id', '')
        new_acc = entry.get('new_account_id', '')
        print(f'Entry {i+1}: "{old_acc}" → "{new_acc}"')
        
print(f'\nIf only prefix additions should be automated:') 
print(f'Automation rate = {len(prefix_additions)}/78 = {len(prefix_additions)/78*100:.1f}%')

print(f'\nIf we want to detect accounts that NEED prefix addition:')
need_prefix = len([e for e in data if not str(e.get('new_account_id', '')).startswith('1')])
print(f'Accounts that need "1" prefix: {need_prefix}/78')