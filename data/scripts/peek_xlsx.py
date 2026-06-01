import pandas as pd

file_path = "data/raw/DTM Nigeria Site Assessment Round 50.xlsx"
xl = pd.ExcelFile(file_path)
print(f"Sheet names: {xl.sheet_names}")

# Read first few rows of the 'Data' sheet to check columns
df = pd.read_excel(file_path, sheet_name='Data', nrows=5)
print("\nColumn names for 'Data' sheet:")
print(df.columns.tolist())
