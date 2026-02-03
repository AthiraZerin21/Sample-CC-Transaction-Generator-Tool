from flask import Flask, render_template, request, send_file
import random, json, io
import pandas as pd
from datetime import datetime, timedelta
 
app = Flask(__name__)
 
VENDORS = [
    "Amazon", "Flipkart", "Uber", "Swiggy", "Zomato",
    "Indigo Airlines", "MakeMyTrip", "Ola",
    "Reliance Trends", "Big Bazaar", "ABC Hotel", "XYZ Restaurant"
]
 
CURRENCY_SYMBOLS = {
    "INR": "₹",
    "USD": "$",
    "EUR": "€",
    "CAD": "C$"
}
 
# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("CC_Transaction.html")
 
@app.route("/about")
def about():
    return "<h2>Credit Card Transaction Generator Tool</h2>"
 
# ---------------- PREVIEW ----------------
@app.route("/preview", methods=["POST"])
def preview():
 
    cardholder_name = request.form.get("cardholder_name")
    payment_type = request.form.get("payment_type")
    card_types = request.form.getlist("card_types")
    currencies = request.form.getlist("currencies")
    negative_count = int(request.form.get("negative_count", 0))
    file_type = request.form.get("file_type")
 
    start = datetime.strptime(request.form["from_date"], "%Y-%m-%d")
    end = datetime.strptime(request.form["to_date"], "%Y-%m-%d")
 
    # Dynamic expense types
    expense_names = request.form.getlist("expense_name[]")
    expense_counts = request.form.getlist("expense_count[]")
 
    expense_types = {}
    for n, c in zip(expense_names, expense_counts):
        if n.strip() and int(c) > 0:
            expense_types[n.strip()] = int(c)
 
    total_transactions = sum(expense_types.values())
 
    # Ensure negative < total
    if negative_count >= total_transactions:
        negative_count = max(0, total_transactions - 1)
 
    transactions = []
 
    employee_id = f"EMP{random.randint(1000,9999)}"
    card_number = f"{random.randint(4000,4999)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}"
 
    # Generate normal transactions
    for expense, count in expense_types.items():
        for _ in range(count):
            currency = random.choice(currencies)
            symbol = CURRENCY_SYMBOLS[currency]
            amount_val = round(random.uniform(100, 5000), 2)
 
            transactions.append({
                "employee_id": employee_id,
                "cardholder_name": cardholder_name,
                "card_type": random.choice(card_types),
                "card_number": card_number,
                "expense_type": expense,
                "vendor_name": random.choice(VENDORS),
                "date": (start + (end - start) * random.random()).strftime("%Y-%m-%d"),
                "amount": f"{symbol}{amount_val}",
                "transaction_currency": currency
            })
 
    # Generate negative transactions
    for _ in range(negative_count):
        currency = random.choice(currencies)
        symbol = CURRENCY_SYMBOLS[currency]
        amount_val = round(random.uniform(50, 2000), 2)
 
        transactions.append({
            "employee_id": employee_id,
            "cardholder_name": cardholder_name,
            "card_type": random.choice(card_types),
            "card_number": card_number,
            "expense_type": random.choice(list(expense_types.keys())),
            "vendor_name": random.choice(VENDORS),
            "date": (start + (end - start) * random.random()).strftime("%Y-%m-%d"),
            "amount": f"-{symbol}{amount_val}",
            "transaction_currency": currency
        })
 
    return render_template("CC_Transaction.html", data=transactions, file_type=file_type)
 
# ---------------- DOWNLOAD ----------------
@app.route("/download", methods=["POST"])
def download():
 
    data = json.loads(request.form["data"])
    file_type = request.form["file_type"]
 
    rows = []
 
    for idx, row in enumerate(data, start=1):
        last_segment = row["card_number"].split("-")[-1]
 
        amt = row["amount"]
        for sym in CURRENCY_SYMBOLS.values():
            amt = amt.replace(sym, "")
        amt = amt.strip()
 
        rows.append([
            f"TXN{idx:05d}",
            row["employee_id"],
            row["cardholder_name"],
            last_segment,
            row["expense_type"],
            amt,
            row["transaction_currency"],
            row["date"],
            row["vendor_name"]
        ])
 
    df = pd.DataFrame(rows)
 
    if file_type == "xlsx":
        output = io.BytesIO()
        df.to_excel(output, index=False, header=False)
        output.seek(0)
        return send_file(output, download_name="transactions.xlsx", as_attachment=True)
 
    elif file_type == "csv":
        output = io.StringIO()
        df.to_csv(output, index=False, header=False)
        mem = io.BytesIO(output.getvalue().encode("utf-8"))
        mem.seek(0)
        return send_file(mem, download_name="transactions.txt", mimetype="text/plain", as_attachment=True)
 
    return "Invalid format selected"
 
 
if __name__ == "__main__":
    app.run(debug=True)
