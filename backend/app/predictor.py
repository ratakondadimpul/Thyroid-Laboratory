import pathlib, joblib, numpy as np, pandas as pd
from .processor import feature_matrix, clean_frame, impute_and_scale

ROOT = pathlib.Path(__file__).parent.parent
MODEL_PATH = ROOT / "models" / "thyroid_model.pkl"
CATEGORY_PATH = ROOT / "models" / "category_model.pkl"
RISK_PATH = ROOT / "models" / "risk_model.pkl"
SCALER_PATH = ROOT / "models" / "scaler.pkl"
EVAL_PATH = ROOT / "models" / "evaluation.json"

_FEATURES = ['age','sex','TSH','T3','TT4','T4U','FTI','TBG','on_thyroxine','query_on_thyroxine','on_antithyroid_medication','sick','pregnant','thyroid_surgery','I131_treatment','query_hypothyroid','query_hyperthyroid','lithium','goitre','tumor','hypopituitary','psych','referral_source']

_model=None
_cat_model=None
_risk_model=None
_scaler=None

def load_models():
    global _model, _cat_model, _risk_model, _scaler
    if _model is None and MODEL_PATH.exists():
        try: _model = joblib.load(MODEL_PATH)
        except: _model=None
    if _cat_model is None and CATEGORY_PATH.exists():
        try: _cat_model = joblib.load(CATEGORY_PATH)
        except: _cat_model=None
    if _risk_model is None and RISK_PATH.exists():
        try: _risk_model = joblib.load(RISK_PATH)
        except: _risk_model=None
    if _scaler is None and SCALER_PATH.exists():
        try: _scaler = joblib.load(SCALER_PATH)
        except: _scaler=None
    return _model, _cat_model, _risk_model, _scaler

def predict_batch(df_clean: pd.DataFrame):
    model, cat_model, risk_model, scaler = load_models()
    if model is None or scaler is None:
        # fallback rule-based
        return fallback_predict(df_clean)
    X, cols = feature_matrix(df_clean)
    X_scaled = scaler.transform(X)
    proba = model.predict_proba(X_scaled)[:,1] if hasattr(model,'predict_proba') else model.predict(X_scaled).astype(float)
    preds = (proba>0.5).astype(int)
    # category
    cat_preds = cat_model.predict(X_scaled) if cat_model is not None else np.zeros(len(X))
    # risk for negatives
    risk_proba = None
    if risk_model is not None:
        try: risk_proba = risk_model.predict_proba(X_scaled)[:,1]
        except: risk_proba = None
    results=[]
    for i in range(len(df_clean)):
        p = float(proba[i])
        score = round(p*100,1)
        overall = "Positive" if preds[i]==1 else "Negative"
        # Determine category
        if overall=="Positive":
            cp = int(cat_preds[i])
            if cp==1: category="hypothyroid"
            elif cp==2: category="hyperthyroid"
            else: category="hypothyroid" # default
            # need to differentiate hypo vs hyper subtypes; use Category mapping
            # if we have more granular, fallback to hypo/hyper
            risk = None
        else:
            category = "negative"
            # risk stratification
            if risk_proba is not None:
                rp = float(risk_proba[i])
                risk = "Higher Risk" if rp>0.5 else "Lower Risk"
                # risk score is separate from main score
            else:
                # threshold heuristic: high TSH + age
                risk = "Higher Risk" if p>0.35 else "Lower Risk" # use proba as proxy
        confidence = float(max(p,1-p))
        results.append({
            "overall": overall,
            "category": category,
            "risk": risk,
            "score": score,
            "proba": p,
            "confidence": round(confidence,2),
            "cat_pred": int(cat_preds[i]) if cat_preds is not None else 0
        })
    return results

def fallback_predict(df_clean: pd.DataFrame):
    results=[]
    for _, row in df_clean.iterrows():
        # heuristic: TSH >10 or TSH<0.4 or TT4 extreme
        try: tsh = float(row.get('TSH', 1.5))
        except: tsh=1.5
        try: tt4 = float(row.get('TT4', 100))
        except: tt4=100
        try: age=float(row.get('age',40))
        except: age=40
        score = 0
        if tsh>10 or tsh<0.4: score+=40
        if tt4<60 or tt4>140: score+=30
        if row.get('query_hypothyroid',0)==1 or row.get('query_hyperthyroid',0)==1: score+=20
        if age>60: score+=10
        p = min(0.95, score/100)
        overall = "Positive" if p>0.5 else "Negative"
        if overall=="Positive":
            category = "hypothyroid" if tsh>5 else "hyperthyroid"
            risk=None
        else:
            category="negative"
            risk="Higher Risk" if p>0.3 else "Lower Risk"
        results.append({"overall":overall,"category":category,"risk":risk,"score":round(p*100,1),"proba":float(p),"confidence":0.7,"cat_pred":0})
    return results

_explainer_cache = None
def _get_explainer():
    global _explainer_cache
    if _explainer_cache is not None:
        return _explainer_cache
    try:
        import shap
        model,_,_,scaler = load_models()
        if model is not None and hasattr(model, 'predict'):
            # Use background dataset of zeros for faster approx, or TreeExplainer with model
            _explainer_cache = shap.TreeExplainer(model)
            return _explainer_cache
    except: pass
    return None

def explain_instance(row_clean: dict, proba: float, use_shap: bool = True):
    # SHAP if available else heuristic; use_shap=False for bulk fast path
    if use_shap:
        try:
            explainer = _get_explainer()
            model,_,_,scaler = load_models()
            if explainer is not None and model is not None and scaler is not None:
                X, cols = feature_matrix(pd.DataFrame([row_clean]))
                X_scaled = scaler.transform(X)
                try:
                    shap_vals = explainer.shap_values(X_scaled)
                    if isinstance(shap_vals, list):
                        shap_vals = shap_vals[1] if len(shap_vals)>1 else shap_vals[0]
                    shap_vals = np.array(shap_vals).flatten()
                    contribs = sorted([{"feature":f, "value": float(X.iloc[0][f]) if f in X.columns else 0, "impact": float(sv)} for f,sv in zip(cols, shap_vals)], key=lambda x: abs(x["impact"]), reverse=True)
                    return contribs[:6]
                except: pass
        except: pass
    # heuristic: impact based on deviation from healthy range
    medians = {"TSH":2.0,"T3":1.8,"TT4":100,"T4U":1.0,"FTI":100,"age":45,"sex":0.5}
    impacts=[]
    for f in _FEATURES:
        val = float(row_clean.get(f,0) or 0)
        med = medians.get(f, 0)
        if f in ['TSH','T3','TT4','FTI']:
            impact = (val-med)/max(1, med)
        elif f=='age':
            impact = (val-45)/30
        elif f in ['query_hypothyroid','query_hyperthyroid','on_thyroxine']:
            impact = val*0.8
        else:
            impact = val*0.3
        impacts.append({"feature":f,"value":val,"impact":float(np.clip(impact,-1,1))})
    impacts=sorted(impacts, key=lambda x: abs(x["impact"]), reverse=True)
    return impacts[:6]
