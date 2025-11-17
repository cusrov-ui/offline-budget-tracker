
# Offline Budget Tracker (Flask)

This is a simple offline Budget Tracker web app built with Flask.
It stores data locally in a SQLite database.

## Features
- Add income and expense transactions (with date, category, note)
- View recent transactions
- Delete transactions
- Monthly summary (income, expense, net)
- Expense breakdown chart by category for the current month
- Export all transactions to CSV
- Data stored in `data/budget.db` (SQLite)

## Run locally

1. Create and activate a virtual environment (optional):
```bash
python -m venv venv
source venv/bin/activate   # macOS / Linux
venv\\Scripts\\activate  # Windows PowerShell
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open in your browser:
```
http://127.0.0.1:5000
```