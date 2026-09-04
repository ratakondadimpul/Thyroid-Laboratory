"""
Train thyroid classifier on thyroid0387_processed.csv
- 5 models: LogisticRegression, DecisionTree, RandomForest, SVM, XGBoost
- Primary task: Positive (hypo/hyper) vs Negative
- Secondary: Category within Positive (hypothyroid vs hyperthyroid)
"""
import pathlib, json, joblib, numpy as np, pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score, confusion_matrix, classification_report

try:
    from xgboost import XGBClassifier
    HAS_XGB=True
except: HAS_XGB=False

FEATURES = ['age','sex','TSH','T3','TT4','T4U','FTI','TBG','on_thyroxine','query_on_thyroxine','on_antithyroid_medication','sick','pregnant','thyroid_surgery','I131_treatment','query_hypothyroid','query_hyperthyroid','lithium','goitre','tumor','hypopituitary','psych','referral_source']

ROOT = pathlib.Path(__file__).parent.parent
DATA_CSV = ROOT.parent / "data" / "processed" / "thyroid0387_processed.csv"
MODELS_DIR = ROOT / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

def load_dataset():
    df = pd.read_csv(DATA_CSV)
    # Clean similar to processor
    df = df.replace('?', np.nan)
    # map sex M/F -> 1/0
    df['sex'] = df['sex'].map({'M':1,'F':0,'m':1,'f':0}).fillna(0)
    for col in ['on_thyroxine','query_on_thyroxine','on_antithyroid_medication','sick','pregnant','thyroid_surgery','I131_treatment','query_hypothyroid','query_hyperthyroid','lithium','goitre','tumor','hypopituitary','psych']:
        if col in df.columns:
            df[col]=df[col].map({'f':0,'t':1,'F':0,'T':1}).fillna(0)
        else:
            df[col]=0
    mapping = {'WEST':0,'STMW':1,'SVHC':2,'SVI':3,'SVHD':4,'other':5}
    df['referral_source']=df['referral_source'].map(mapping).fillna(5)
    # numeric labs
    for col in ['age','TSH','T3','TT4','T4U','FTI','TBG']:
        df[col]=pd.to_numeric(df[col], errors='coerce')
        df[col]=df[col].fillna(df[col].median())
    # binary label: Positive vs Negative (treat K/I etc as Negative for primary task)
    df['label_binary'] = (df['Overall']=='Positive').astype(int)
    # multi-class for positives: 0=negative,1=hypothyroid,2=hyperthyroid
    def cat_multi(row):
        if row['Overall']=='Negative':
            return 0
        if row['Category']=='hypothyroid':
            return 1
        if row['Category']=='hyperthyroid':
            return 2
        return 0
    df['label_multi'] = df.apply(cat_multi, axis=1)
    return df

def train():
    df = load_dataset()
    X = df[FEATURES].astype(float)
    y = df['label_binary']
    y_multi = df['label_multi']

    # scaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test, y_multi_train, y_multi_test = train_test_split(X_scaled, y, y_multi, test_size=0.2, random_state=42, stratify=y)

    models = {
        'LogisticRegression': LogisticRegression(max_iter=500, class_weight='balanced'),
        'DecisionTree': DecisionTreeClassifier(max_depth=10, random_state=42, class_weight='balanced'),
        'RandomForest': RandomForestClassifier(n_estimators=200, max_depth=14, random_state=42, n_jobs=-1, class_weight='balanced'),
        'SVM': SVC(probability=True, kernel='rbf', class_weight='balanced', random_state=42),
    }
    if HAS_XGB:
        models['XGBoost'] = XGBClassifier(n_estimators=150, max_depth=6, learning_rate=0.08, subsample=0.9, colsample_bytree=0.9, random_state=42, n_jobs=-1, eval_metric='logloss', scale_pos_weight=9)

    results=[]
    best_model=None
    best_f1=0
    best_name=""

    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:,1] if hasattr(model,'predict_proba') else np.zeros(len(y_test))
        acc = accuracy_score(y_test, y_pred)
        prec, rec, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='binary', zero_division=0)
        try: auc = roc_auc_score(y_test, y_proba)
        except: auc=0.5
        # cross val 5-fold for robustness (on train)
        cv_scores = cross_val_score(model, X_train, y_train, cv=StratifiedKFold(5, shuffle=True, random_state=42), scoring='f1')
        print(f"{name}: acc={acc:.4f} prec={prec:.4f} rec={rec:.4f} f1={f1:.4f} auc={auc:.4f} cv_f1={cv_scores.mean():.4f}±{cv_scores.std():.4f}")
        print(classification_report(y_test, y_pred, target_names=['Negative','Positive'], zero_division=0))
        res = {"model": name, "accuracy": float(acc), "precision": float(prec), "recall": float(rec), "f1": float(f1), "auc": float(auc), "cv_f1_mean": float(cv_scores.mean()), "cv_f1_std": float(cv_scores.std()), "confusion_matrix": confusion_matrix(y_test, y_pred).tolist()}
        if hasattr(model,'feature_importances_'):
            res['feature_importance'] = dict(zip(FEATURES, model.feature_importances_.tolist()))
        elif hasattr(model,'coef_'):
            # abs coef
            coef = np.abs(model.coef_[0])
            coef = coef/coef.sum()
            res['feature_importance'] = dict(zip(FEATURES, coef.tolist()))
        else:
            res['feature_importance'] = {}
        results.append(res)
        if f1 > best_f1:
            best_f1 = f1
            best_model = model
            best_name = name

    print(f"\nBest model: {best_name} f1={best_f1:.4f}")

    # Save best model + scaler
    joblib.dump(best_model, MODELS_DIR/"thyroid_model.pkl")
    joblib.dump(scaler, MODELS_DIR/"scaler.pkl")
    # Also train multiclass for category (only on positives + sample negatives)
    # Use XGBoost or RandomForest for multi
    from sklearn.ensemble import RandomForestClassifier as RFC2
    multi_model = RFC2(n_estimators=200, random_state=42, n_jobs=-1, class_weight='balanced')
    # Use all data for multiclass training
    X_multi_scaled = scaler.transform(X) # reuse same scaler
    multi_model.fit(X_multi_scaled, y_multi)
    joblib.dump(multi_model, MODELS_DIR/"category_model.pkl")

    # Save risk model: for Negative -> risk stratification using probability threshold approach
    # Train a simple logistic to predict high-risk among negatives based on age+TSH pattern synthetic
    # For now, we reuse binary proba as risk score (no separate model)
    # But create a dummy risk model that uses same features to score negatives
    risk_model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    # create synthetic risk labels among negatives: older age + abnormal TSH => higher
    neg_mask = df['label_binary']==0
    df_neg = df[neg_mask].copy()
    # heuristic: high risk if age>50 and (TSH>5 or TSH<0.4 or TT4<50 or TT4>150)
    def heuristic_high(row):
        try:
            tsh=float(row['TSH']) if pd.notna(row['TSH']) else 1.5
            tt4=float(row['TT4']) if pd.notna(row['TT4']) else 100
            age=float(row['age']) if pd.notna(row['age']) else 40
            if age>50 and (tsh>5 or tsh<0.4 or tt4<60 or tt4>140):
                return 1
            return 0
        except: return 0
    y_risk = df_neg.apply(heuristic_high, axis=1)
    if y_risk.sum()>10 and y_risk.sum()<len(y_risk)-10:
        X_risk = scaler.transform(df_neg[FEATURES].astype(float))
        risk_model.fit(X_risk, y_risk)
        joblib.dump(risk_model, MODELS_DIR/"risk_model.pkl")
        print(f"Risk model trained: pos {y_risk.sum()} / {len(y_risk)}")
    else:
        print("Risk model not trained due to imbalance, will use threshold method")

    # evaluation.json
    eval_data = {
        "best_model": best_name,
        "models": results,
        "feature_importance": results[0]['feature_importance'] if results else {},
        "n_train": len(X_train),
        "n_test": len(X_test),
        "has_xgb": HAS_XGB,
        "features": FEATURES
    }
    # provide compatibility fields for frontend
    best_res = next((r for r in results if r['model']==best_name), results[0] if results else {})
    eval_data.update({"accuracy": best_res.get('accuracy'), "precision": best_res.get('precision'), "recall": best_res.get('recall'), "f1": best_res.get('f1'), "auc": best_res.get('auc'), "confusion_matrix": best_res.get('confusion_matrix')})
    import json as js
    with open(MODELS_DIR/"evaluation.json","w") as f:
        js.dump(eval_data, f, indent=2)
    print(f"Saved to {MODELS_DIR/'thyroid_model.pkl'} and evaluation.json")
    return best_model

if __name__=="__main__":
    train()
