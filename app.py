
from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3, os, csv, io, datetime

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'data', 'budget.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,          -- 'income' or 'expense'
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        note TEXT,
        created_at TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

def add_transaction(tx):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO transactions (type, category, amount, note, created_at)
                 VALUES (?, ?, ?, ?, ?)''', (tx['type'], tx['category'], tx['amount'], tx.get('note',''), tx['created_at']))
    conn.commit()
    conn.close()

def get_transactions(limit=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    q = 'SELECT id, type, category, amount, note, created_at FROM transactions ORDER BY created_at DESC'
    if limit:
        q += f' LIMIT {int(limit)}'
    c.execute(q)
    rows = c.fetchall()
    conn.close()
    return rows

def delete_transaction(tx_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM transactions WHERE id=?', (tx_id,))
    conn.commit()
    conn.close()

def summarize_month(year, month):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    start = f"{year:04d}-{month:02d}-01"
    # compute next month start
    if month == 12:
        next_start = f"{year+1:04d}-01-01"
    else:
        next_start = f"{year:04d}-{month+1:02d}-01"
    c.execute('''SELECT type, SUM(amount) FROM transactions
                 WHERE created_at>=? AND created_at<? GROUP BY type''', (start, next_start))
    rows = c.fetchall()
    conn.close()
    totals = {'income': 0.0, 'expense': 0.0}
    for r in rows:
        totals[r[0]] = r[1] if r[1] is not None else 0.0
    return totals

def export_csv():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, type, category, amount, note, created_at FROM transactions ORDER BY created_at DESC')
    rows = c.fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['id','type','category','amount','note','created_at'])
    writer.writerows(rows)
    output.seek(0)
    return output.getvalue().encode('utf-8')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'devkey'

@app.route('/', methods=['GET'])
def index():
    # show last 100 transactions and a monthly summary for current month
    now = datetime.date.today()
    txs = get_transactions(limit=100)
    summary = summarize_month(now.year, now.month)
    # gather breakdown by category for chart
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    start = f"{now.year:04d}-{now.month:02d}-01"
    if now.month == 12:
        next_start = f"{now.year+1:04d}-01-01"
    else:
        next_start = f"{now.year:04d}-{now.month+1:02d}-01"
    c.execute('''SELECT category, SUM(amount) FROM transactions
                 WHERE created_at>=? AND created_at<? AND type='expense'
                 GROUP BY category ORDER BY SUM(amount) DESC''', (start, next_start))
    cat_rows = c.fetchall()
    conn.close()
    categories = [r[0] for r in cat_rows]
    cat_values = [r[1] for r in cat_rows]
    return render_template('index.html', transactions=txs, summary=summary, categories=categories, cat_values=cat_values, current_month=start[:7])

@app.route('/add', methods=['POST'])
def add():
    ttype = request.form.get('type')
    category = request.form.get('category','Other').strip() or 'Other'
    amount = request.form.get('amount','0').strip()
    note = request.form.get('note','').strip()
    try:
        amount_f = float(amount)
    except ValueError:
        return "Invalid amount", 400
    created_at = request.form.get('date') or datetime.date.today().isoformat()
    tx = {'type': ttype, 'category': category, 'amount': amount_f, 'note': note, 'created_at': created_at}
    add_transaction(tx)
    return redirect(url_for('index'))

@app.route('/delete/<int:tx_id>', methods=['POST'])
def delete(tx_id):
    delete_transaction(tx_id)
    return redirect(url_for('index'))

@app.route('/export', methods=['GET'])
def export():
    data = export_csv()
    return send_file(io.BytesIO(data), mimetype='text/csv', as_attachment=True, download_name='budget_transactions.csv')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
