# GitHub push checklist

1. Create a new empty repo on GitHub (do not add README there if you already have one locally).

2. In this folder:

```powershell
cd "c:\Users\saich\Downloads\1-TASK\Multi-Agent-Fraud-Detection"
git init
git add .
git status
git commit -m "Add multi-agent online fraud detection system"
git branch -M main
git remote add origin https://github.com/<YOUR_USER>/<YOUR_REPO>.git
git push -u origin main
```

3. Large model files under `artifacts/models/` are gitignored. After clone, run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m src.training.train --n 200000
python scripts/run_api.py
```

4. Interview numbers live in `INTERVIEW_ANSWERS.md` and `artifacts/metrics/results.json`.
