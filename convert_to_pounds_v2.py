"""Properly convert all currency displays to £"""

import re

# Read the file
with open('streamlit_app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace currency formatting patterns
# Pattern 1: f"{number:.2f}" or f"{number:,.2f}" for currency (but not percentages or kWh)
content = re.sub(
    r'f"(\{[^}]*(?:cost|Cost|fee|Fee|service|Service|premium|Premium|degradation|Degradation|discount|Discount|hotelling|Hotelling|total|Total|charging|Charging)[^}]*:[,\.]2f\})"',
    r'f"£\1"',
    content
)

# Pattern 2: f"-{number:.2f}" for negative values
content = re.sub(
    r'f"-(\{[^}]*:[,\.]2f\})"',
    r'f"-£\1"',
    content
)

# Pattern 3: Column config formats
content = content.replace('format="%.2f"', 'format="£%.2f"')
content = content.replace('format="%.3f', 'format="£%.3f')

# Pattern 4: Column headers
content = content.replace('Cost ()', 'Cost (£)')
content = content.replace('Fee ()', 'Fee (£)')
content = content.replace('(/kWh)', '(£/kWh)')

# Pattern 5: Help text
content = content.replace('~0.09/kWh', '~£0.09/kWh')
content = content.replace('~0.18/kWh', '~£0.18/kWh')  
content = content.replace('0.08-0.13 /kWh', '0.08-0.13 £/kWh')

# Write back
with open('streamlit_app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Properly converted currency to pounds (£)")
print(f"Total length: {len(content)} characters")
