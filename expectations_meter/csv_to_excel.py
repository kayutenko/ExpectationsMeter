import pandas as pd

data = pd.read_csv('AppleInsider_6_1.csv')
data.to_excel('AppleInsider_latest.xlsx', index=False)