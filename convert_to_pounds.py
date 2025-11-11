"""Convert all currency from $ to £ in main.py"""

import re

# Read the file
with open('streamlit_app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all dollar formatting with pounds
replacements = [
    # Format strings
    (r'f"(\{[^}]+\}),"', r'f"£\1,"'),  # f"{value},"
    (r'f"(\{[^}]+\})"', r'f"£\1"'),     # f"{value}"
    (r'f"-(\{[^}]+\})"', r'f"-£\1"'),   # f"-{value}"
    
    # Column headers and labels
    ('Cost ()', 'Cost (£)'),
    ('Fee ()', 'Fee (£)'),
    ('(/kWh)', '(£/kWh)'),
    
    # Number format strings
    ('format="%.2f"', 'format="£%.2f"'),
    ('format="%.3f', 'format="£%.3f'),
    
    # Help text references
    ('~0.09/kWh', '~£0.09/kWh'),
    ('~0.18/kWh', '~£0.18/kWh'),
    ('0.08-0.13 /kWh', '0.08-0.13 £/kWh'),
]

for old, new in replacements:
    content = content.replace(old, new)

# Write back
with open('streamlit_app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Converted all currency to pounds (£)")
