import pandas as pd

url = "https://docs.google.com/spreadsheets/d/1lhur_ygXHzSVKDsM0G2f8QDmVNzlLE9OqRXdtTVd1Qs/export?format=csv"
df = pd.read_csv(url)

print(df.head())
