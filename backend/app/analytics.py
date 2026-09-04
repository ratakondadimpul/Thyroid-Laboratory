import pandas as pd
import numpy as np

def compute_analytics(df_clean: pd.DataFrame, preds: list):
    # preds aligns with df_clean
    total=len(df_clean)
    pos=sum(1 for p in preds if p['overall']=='Positive')
    neg=total-pos
    hypo=sum(1 for p in preds if p['category']=='hypothyroid')
    hyper=sum(1 for p in preds if p['category']=='hyperthyroid')
    high=sum(1 for p in preds if p['risk']=='Higher Risk')
    low=sum(1 for p in preds if p['risk']=='Lower Risk')
    # demographics
    age_series = pd.to_numeric(df_clean.get('age', pd.Series(dtype=float)), errors='coerce').dropna()
    age_hist = []
    if not age_series.empty:
        bins=[0,20,40,60,80,120]
        hist, edges=np.histogram(age_series, bins=bins)
        age_hist=[{"range": f"{edges[i]:.0f}-{edges[i+1]:.0f}", "count": int(hist[i])} for i in range(len(hist))]
    gender_counts={}
    if 'sex' in df_clean.columns:
        # sex is numeric 0 Female 1 Male after clean
        vc=df_clean['sex'].value_counts(dropna=False)
        gender_counts={str(k): int(v) for k,v in vc.items()}
        # map 0->F, 1->M
        gender_counts={'Female': int((df_clean['sex']==0).sum()), 'Male': int((df_clean['sex']==1).sum())}
    # lab distributions
    lab_stats={}
    for col in ['TSH','T3','TT4','FTI']:
        if col in df_clean.columns:
            vals=pd.to_numeric(df_clean[col], errors='coerce').dropna()
            if not vals.empty:
                def safe_float(x):
                    if pd.isna(x) or np.isinf(x):
                        return 0.0
                    return float(x)
                lab_stats[col]={"mean": safe_float(vals.mean()), "median": safe_float(vals.median()), "std": safe_float(vals.std() if len(vals)>1 else 0), "min": safe_float(vals.min()), "max": safe_float(vals.max())}
    # correlation matrix for heatmap
    corr={}
    num_cols=[c for c in ['age','TSH','T3','TT4','T4U','FTI'] if c in df_clean.columns]
    if len(num_cols)>=2:
        try:
            corr_mat=pd.DataFrame(df_clean[num_cols].apply(pd.to_numeric, errors='coerce')).corr()
            corr=corr_mat.round(2).fillna(0).to_dict()
            # sanitize nan in corr
            for k in corr:
                for kk in corr[k]:
                    v=corr[k][kk]
                    if pd.isna(v) or np.isinf(v):
                        corr[k][kk]=0
                    else:
                        corr[k][kk]=float(v)
        except: pass
    return {
        "total": total, "positive": pos, "negative": neg, "hypothyroid": hypo, "hyperthyroid": hyper,
        "higher_risk": high, "lower_risk": low,
        "positive_pct": round(pos/total*100,1) if total else 0,
        "negative_pct": round(neg/total*100,1) if total else 0,
        "high_pct": round(high/neg*100,1) if neg else 0,
        "age_hist": age_hist,
        "gender_counts": gender_counts,
        "lab_stats": lab_stats,
        "correlation": corr
    }
