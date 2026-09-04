import pandas as pd
import numpy as np
import pathlib, json, joblib

FEATURE_COLS = ['age','TSH','T3','TT4','T4U','FTI','TBG']
BOOL_COLS = ['on_thyroxine','query_on_thyroxine','on_antithyroid_medication','sick','pregnant','thyroid_surgery','I131_treatment','query_hypothyroid','query_hyperthyroid','lithium','goitre','tumor','hypopituitary','psych']
# referral source will be one-hot later but for simple model we encode as numeric fallback
ALL_FEATURES = FEATURE_COLS + BOOL_COLS

def clean_frame(df: pd.DataFrame):
    df = df.copy()
    # normalize column names lower
    df.columns = [c.strip() for c in df.columns]
    # map case-insensitive
    remap = {}
    for c in df.columns:
        lc = c.lower()
        if lc == 'patient_id': remap[c]='Patient_ID'
        elif lc == 'sex' or lc=='gender': remap[c]='sex'
        elif lc == 'age': remap[c]='age'
        elif lc in ['tsh','tsh_value']: remap[c]='TSH'
        elif lc in ['t3','t3_value']: remap[c]='T3'
        elif lc in ['tt4','t4','tt4_value']: remap[c]='TT4'
        elif lc == 't4u': remap[c]='T4U'
        elif lc == 'fti': remap[c]='FTI'
        elif lc == 'tbg': remap[c]='TBG'
        elif lc == 'on thyroxine' or lc=='on_thyroxine': remap[c]='on_thyroxine'
        elif lc == 'query on thyroxine': remap[c]='query_on_thyroxine'
        elif lc == 'on antithyroid medication' or lc=='on_antithyroid_medication': remap[c]='on_antithyroid_medication'
        elif lc == 'referral source' or lc=='referral_source': remap[c]='referral_source'
    df = df.rename(columns=remap)
    # replace '?' and '' with NaN
    df = df.replace('?', np.nan)
    df = df.replace('', np.nan)
    # sex: M->1, F->0, ?->nan
    if 'sex' in df.columns:
        df['sex'] = df['sex'].map({'M':1,'F':0,'m':1,'f':0, 'Male':1,'Female':0}).fillna(df['sex'])
        # if still string, try numeric
        df['sex'] = pd.to_numeric(df['sex'], errors='coerce')
    # bool cols: f->0, t->1
    for col in BOOL_COLS:
        if col in df.columns:
            df[col] = df[col].map({'f':0,'t':1,'F':0,'T':1, '0':0,'1':1, 0:0,1:1, False:0, True:1})
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        else:
            df[col]=0
    # numeric cols
    for col in FEATURE_COLS:
        if col in df.columns:
            df[col]=pd.to_numeric(df[col], errors='coerce')
        else:
            df[col]=np.nan
    # referral source encode
    if 'referral_source' in df.columns:
        # one-hot simplified: map to int
        mapping = {'WEST':0,'STMW':1,'SVHC':2,'SVI':3,'SVHD':4,'other':5}
        df['referral_source'] = df['referral_source'].map(mapping).fillna(5)
    else:
        df['referral_source']=5
    return df

def impute_and_scale(df: pd.DataFrame, scaler=None, fit=False):
    df = df.copy()
    # median impute for numeric
    numeric_cols = FEATURE_COLS + ['sex','referral_source']
    for col in numeric_cols:
        if col in df.columns:
            median = df[col].median() if not fit else scaler.get(col, {}).get('median', df[col].median())
            df[col]=df[col].fillna(median)
    # for bool cols already filled 0
    # scaling: StandardScaler for numeric labs
    if fit:
        # build scaler dict
        scaler = {}
        for col in numeric_cols:
            vals = df[col].astype(float)
            scaler[col]={'mean': float(vals.mean()), 'std': float(vals.std() if vals.std()!=0 else 1.0), 'median': float(vals.median())}
        # transform
        for col in numeric_cols:
            m, s = scaler[col]['mean'], scaler[col]['std']
            df[col] = (df[col]-m)/s
        return df, scaler
    else:
        if scaler is None:
            return df, None
        for col in numeric_cols:
            if col in scaler:
                m, s = scaler[col]['mean'], scaler[col]['std']
                df[col]=(df[col]-m)/s
        return df, scaler

def feature_matrix(df_clean: pd.DataFrame):
    cols = ['age','sex','TSH','T3','TT4','T4U','FTI','TBG','on_thyroxine','query_on_thyroxine','on_antithyroid_medication','sick','pregnant','thyroid_surgery','I131_treatment','query_hypothyroid','query_hyperthyroid','lithium','goitre','tumor','hypopituitary','psych','referral_source']
    # ensure all exist
    for c in cols:
        if c not in df_clean.columns:
            df_clean[c]=0
    X = df_clean[cols].fillna(0).astype(float)
    return X, cols
