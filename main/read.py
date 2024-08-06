import pandas as pd

gsheetkey = "1FbHzeuPFUezX3zVh6CPXj0G8sSFof7k9und-es9DDNU"
sheet_name = 'Sheet1'

url = f'https://docs.google.com/spreadsheets/d/{gsheetkey}/export?format=xlsx&gid=0'
df = pd.read_excel(url, sheet_name=sheet_name)

track_id_df = df[['Track ID']]
print(track_id_df)
