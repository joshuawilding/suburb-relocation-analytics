import pandas as pd
import numpy as np
import io

df = pd.read_csv('tri_state_master_with_niche.csv')

total_rows = len(df)

markdown_output = f"# Master Dataset Data Profile\n\n"
markdown_output += f"**Total Rows:** {total_rows}\n"
markdown_output += f"**Total Columns:** {len(df.columns)}\n\n"

markdown_output += "## 1. Fill Rates (Completeness)\n"
markdown_output += "| Column Name | Non-Null Count | Fill Rate % |\n"
markdown_output += "| :--- | :--- | :--- |\n"

fill_rates = (df.notnull().sum() / total_rows) * 100
for col in df.columns:
    non_null = df[col].notnull().sum()
    pct = fill_rates[col]
    markdown_output += f"| `{col}` | {non_null} | {pct:.1f}% |\n"

markdown_output += "\n## 2. Summary Statistics (Numerical Columns)\n\n"
num_cols = df.select_dtypes(include=[np.number]).columns

for col in num_cols:
    desc = df[col].describe()
    markdown_output += f"### `{col}`\n"
    markdown_output += f"- **Count:** {desc['count']:.0f}\n"
    markdown_output += f"- **Mean:** {desc['mean']:.2f}\n"
    markdown_output += f"- **Std Dev:** {desc['std']:.2f}\n"
    markdown_output += f"- **Min:** {desc['min']:.2f}\n"
    markdown_output += f"- **25th Pct:** {desc['25%']:.2f}\n"
    markdown_output += f"- **Median (50%):** {desc['50%']:.2f}\n"
    markdown_output += f"- **75th Pct:** {desc['75%']:.2f}\n"
    markdown_output += f"- **Max:** {desc['max']:.2f}\n\n"

markdown_output += "## 3. Value Counts (Categorical Columns)\n\n"
cat_cols = df.select_dtypes(include=['object', 'category']).columns

for col in cat_cols:
    vc = df[col].value_counts(dropna=False).head(15) # Top 15 to keep it readable
    markdown_output += f"### `{col}`\n"
    markdown_output += "| Value | Count | % of Total |\n"
    markdown_output += "| :--- | :--- | :--- |\n"
    for val, count in vc.items():
        pct = (count / total_rows) * 100
        val_str = str(val) if not pd.isna(val) else "NaN"
        markdown_output += f"| {val_str} | {count} | {pct:.1f}% |\n"
    
    if len(df[col].unique()) > 15:
         markdown_output += f"| *(... {len(df[col].unique()) - 15} more unique values)* | - | - |\n"
    markdown_output += "\n"

with open('data_profile.md', 'w') as f:
    f.write(markdown_output)

print("Data profile generated at data_profile.md")
