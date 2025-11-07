import pandas as pd
import re

def extract_name_email(value):
    """Extracts name and email from combined text."""
    if pd.isna(value):
        return pd.Series([None, None])
    match = re.search(r'([A-Za-z\s]+)\s*[-–]?\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})', value)
    if match:
        name = match.group(1).strip()
        email = match.group(2).strip()
        return pd.Series([name, email])
    return pd.Series([None, None])

# 1️⃣ Read enriched_leads.csv
csv_data = pd.read_csv('enriched_leads.csv')
if 'Name and Email' in csv_data.columns:
    csv_data[['Name', 'Email']] = csv_data['Name and Email'].apply(extract_name_email)
    csv_data = csv_data[['Name', 'Email']]

# 2️⃣ Read enriched_leads for christophale310.xlsx
excel_data1 = pd.read_excel('enriched_leads for christophale310.xlsx')
if 'Name and Email' in excel_data1.columns:
    excel_data1[['Name', 'Email']] = excel_data1['Name and Email'].apply(extract_name_email)
    excel_data1 = excel_data1[['Name', 'Email']]

# 3️⃣ Read Event Sheet.xlsx
excel_data2 = pd.read_excel('Event Sheet.xlsx')
if {'First Name', 'Last Name', 'Email'}.issubset(excel_data2.columns):
    excel_data2['Name'] = excel_data2['First Name'].astype(str) + ' ' + excel_data2['Last Name'].astype(str)
    excel_data2 = excel_data2[['Name', 'Email']]

# 4️⃣ Combine all
final_data = pd.concat([csv_data, excel_data1, excel_data2], ignore_index=True)

# 5️⃣ Drop duplicates / NaN
final_data.dropna(subset=['Email'], inplace=True)
final_data.drop_duplicates(subset='Email', inplace=True)

# 6️⃣ Save as main.csv
final_data.to_csv('main.csv', index=False)
print("✅ main.csv created successfully!")
