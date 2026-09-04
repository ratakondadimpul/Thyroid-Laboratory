import pandas as pd
import numpy as np
import re

# Expected lab columns mapping (flexible)
ALIASES = {
    'age': ['age','Age','AGE'],
    'sex': ['sex','Sex','gender','Gender','GENDER'],
    'TSH': ['TSH','tsh','tsh_value','TSH_value'],
    'T3': ['T3','t3','T3_value'],
    'TT4': ['TT4','tt4','T4','t4','TT4_value','T4_value'],
    'T4U': ['T4U','t4u','FTI','FTI_value'],
    'FTI': ['FTI','fti'],
}

REQUIRED_DISPLAY = ['Patient_ID','Age','Gender','TSH','T3','TT4']

def normalize_columns(df: pd.DataFrame):
    col_map = {}
    for std, aliases in ALIASES.items():
        for col in df.columns:
            if col in aliases:
                col_map[col]=std
                break
            # case-insensitive
            if col.lower() in [a.lower() for a in aliases]:
                col_map[col]=std
                break
    # also map Patient_ID
    for col in df.columns:
        if col.lower() in ['patient_id','id','patient','pid']:
            col_map[col]='Patient_ID'
            break
    df = df.rename(columns=col_map)
    return df

def validate_dataframe(df: pd.DataFrame):
    total_rows = len(df)
    total_cols = len(df.columns)
    # missing values (empty string or NaN)
    missing = int(df.isna().sum().sum() + (df.astype(str)=='').sum().sum())
    # also for '?' marker from raw data
    q_missing = int((df.astype(str)=='?').sum().sum())
    missing += q_missing
    # duplicate Patient_ID
    duplicates = 0
    if 'Patient_ID' in df.columns:
        duplicates = int(df.duplicated(subset=['Patient_ID']).sum())
    # invalid values
    invalid = 0
    details = {}
    # Age invalid
    if 'age' in df.columns:
        # try numeric
        ages = pd.to_numeric(df['age'], errors='coerce')
        invalid_age = ages.isna() & df['age'].notna() & (df['age'].astype(str)!='') & (df['age'].astype(str)!='?')
        # also out of range 0-120
        out_of_range = (ages<0) | (ages>120)
        invalid_age = invalid_age | out_of_range.fillna(False)
        invalid += int(invalid_age.sum())
        details['invalid_age'] = int(invalid_age.sum())
    # TSH invalid range 0-500 (allow up to 500 for assay)
    for col, rmax in [('TSH',500),('T3',10),('TT4',500),('T4U',10),('FTI',500)]:
        if col in df.columns:
            vals = pd.to_numeric(df[col], errors='coerce')
            # non-numeric where original not empty/? 
            mask_invalid = vals.isna() & df[col].notna() & (df[col].astype(str)!='') & (df[col].astype(str)!='?')
            invalid += int(mask_invalid.sum())
            details[f'invalid_{col}'] = int(mask_invalid.sum())
    # empty columns
    empty_cols = [c for c in df.columns if df[c].isna().all() or (df[c].astype(str).str.strip()=='').all()]
    # dtype issues
    details['empty_columns'] = empty_cols
    details['duplicate_records'] = duplicates
    details['total_rows'] = total_rows
    details['total_cols'] = total_cols
    details['missing_values'] = missing
    details['invalid_records'] = invalid
    details['valid_records'] = max(0, total_rows - duplicates - min(invalid, total_rows))
    # outliers via IQR for numeric labs
    outliers = 0
    for col in ['age','TSH','T3','TT4','T4U','FTI']:
        if col in df.columns:
            vals = pd.to_numeric(df[col], errors='coerce').dropna()
            if len(vals)>10:
                q1, q3 = vals.quantile(0.25), vals.quantile(0.75)
                iqr = q3-q1
                low, high = q1-1.5*iqr, q3+1.5*iqr
                outliers += int(((vals<low)|(vals>high)).sum())
    details['outliers'] = outliers
    return details
