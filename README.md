# Thyroid Lab Intelligence — AI-Powered Laboratory Analysis & Prediction System

**Garvan 9172 • XGBoost F1 0.917 • Local inference • No external APIs**

Upload → Analyze → Classify → Visualize → Download → Track History

### Workflow
```
ADMIN LOGIN → DASHBOARD → UPLOAD (CSV/XLSX) → VALIDATION → FEATURE EXTRACTION → AI/ML (XGBoost)
         → Positive (hypothyroid/hyperthyroid) / Negative (Higher/Lower Risk) → Dashboard Charts → Downloads → History
```

### Features (Spec §1-26)
- Secure admin auth (JWT, `admin@lab.local` / `admin123`)
- Dashboard: Total, Positive, Negative, Higher Risk, trends
- Upload: CSV/Excel, validation (missing/duplicates/invalid/outliers)
- AI Engine: 5 models (LogReg, DecisionTree, RandomForest, SVM, XGBoost) — best `XGBoost acc 0.983, f1 0.917, auc 0.997` on thyroid0387
- Classification: Positive/Negative + hypo/hyper subcategories + Negative High/Low risk (model-estimated)
- Downloads: complete, positive, negative, higher_risk, lower_risk, hypo, hyper
- Patient search + SHAP explainability
- Analytics: age/gender hist, lab stats, correlation heatmap
- History: re-open past batches, re-download
- Trends: line chart over batches
- Report: A4 PDF via reportlab + matplotlib

### Quick Start
```bash
# Backend (FastAPI :8000)
cd backend
pip install -r requirements.txt
python app/train.py          # trains on data/processed/thyroid0387_processed.csv → models/*.pkl
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000/docs  health: /health

# Frontend (Next.js :3001)
cd frontend
npm install   # or copy from AI_p/frontend/node_modules
npm run dev   # http://localhost:3001
# production: npm run build && npm start

# Docker
docker compose up --build
# web: http://localhost:3001  api: http://localhost:8000
```

### Data
Source: `~/Downloads/thyroid+disease/thyroid0387.data` (9172 records, Garvan Institute) normalized via `data/prepare.py` → `data/processed/thyroid0387_processed.csv` (29 attrs) + `sample_lab.csv` (800 rows demo).
Attributes: age, sex, on_thyroxine, query_on_thyroxine, on_antithyroid_medication, sick, pregnant, thyroid_surgery, I131_treatment, query_hypothyroid, query_hyperthyroid, lithium, goitre, tumor, hypopituitary, psych, TSH, T3, TT4, T4U, FTI, TBG, referral_source.
Labels: Positive = A-D hyper + E-H hypo (887), Negative = '-' (8285) per `thyroid0387.names`.

### API Examples
```bash
curl -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/json" -d '{"email":"admin@lab.local","password":"admin123"}'
curl -F file=@sample_lab.csv http://localhost:8000/api/datasets/upload -H "Authorization: Bearer <token>"
curl -X POST http://localhost:8000/api/datasets/{id}/analyze -H "Authorization: Bearer <token>"
curl http://localhost:8000/api/datasets/{id}/results?filter=positive -H "Authorization: Bearer <token>"
curl http://localhost:8000/api/datasets/{id}/downloads/complete -H "Authorization: Bearer <token>" --output complete.csv
curl -X POST http://localhost:8000/api/datasets/{id}/report -H "Authorization: Bearer <token>" --output report.pdf
curl http://localhost:8000/api/model/performance
```

### Project Structure
```
AI-Powered Thyroid/
├── backend/app/
│   ├── main.py (16 endpoints), auth.py, database.py, validator.py, processor.py, predictor.py, analytics.py, train.py
│   ├── models/thyroid_model.pkl, category_model.pkl, risk_model.pkl, scaler.pkl, evaluation.json
│   └── data/{thyroid.db, uploads/, results/{batch}/, reports/}
├── frontend/src/app/page.tsx (single-page ledger: dashboard, upload, analysis, history, model, reports)
├── data/{raw/thyroid0387.data, processed/thyroid0387_processed.csv, processed/sample_lab.csv}
└── docker-compose.yml
```

### Technology
FastAPI, Pandas, scikit-learn, XGBoost, SHAP, reportlab, matplotlib, SQLAlchemy (SQLite), Next.js 16, Tailwind 4, Recharts 2.13.

### Medical Note
All outputs labeled “Model-estimated higher/lower predicted risk based on available laboratory data” — not a definitive diagnosis. For clinical decision support only.

### Verification
```bash
cd backend && python -c "from app.main import app; print('ok')"
curl http://localhost:8000/health
cd frontend && npm run build  # must succeed
```
