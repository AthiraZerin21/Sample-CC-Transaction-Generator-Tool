from flask import Flask, render_template, request, send_file
import random, csv, io, json
from datetime import datetime, timedelta
from openpyxl import Workbook

app = Flask(__name__)

# ---------------- STATIC DATA ----------------
VENDORS = [
    "Amazon", "Flipkart", "Uber", "Swiggy", "Zomato", "Indigo Airlines",
    "MakeMyTrip", "Ola", "Reliance Trends", "Big Bazaar", "ABC Hotel", "XYZ Restaurant"
]

CURRENCY_SYMBOLS = {
    "INR": "₹",
    "USD": "$",
    "EUR": "€",
    "CAD": "C$"
}

# ✅ Currency-based realistic ranges
CURRENCY_RANGES = {
    "INR": (100, 5000),
    "USD": (5, 500),
    "EUR": (5, 450),
    "CAD": (5, 600)
}

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template('CC_Transaction.html')

@app.route("/about")
def about():
    return render_template('about.html')


@app.route("/preview", methods=["POST"])
def preview():

    user_count = int(request.form.get("user_count", 1))
    card_types = request.form.getlist("card_types") or request.form.getlist("card_type") or []
    negative_count = int(request.form.get("negative_count", 0))
    cardholder_name_input = request.form.get("cardholder_name", "Cardholder")

    currencies = request.form.getlist("currencies")
    if not currencies:
        currencies = ["INR"]

    start_date = request.form.get("from_date")
    end_date = request.form.get("to_date")

    start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else datetime.now() - timedelta(days=30)
    end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.now()

    expense_keys = ["Airfare", "Accommodation", "Taxi", "Group Meals", "Entertainment&Hospitality", "Gifts"]
    expense_types = {}

    for k in expense_keys:
        try:
            v = int(request.form.get(k, 0) or 0)
        except ValueError:
            v = 0
        if v > 0:
            expense_types[k] = v

    transactions = []

    for u in range(user_count):

        employee_id = f"EMP{random.randint(1000, 9999)}"
        cardholder_name = cardholder_name_input

        # One card per user
        card_number = f"{random.randint(4000,4999)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}"

        # -------- Positive Transactions --------
        for expense, count in expense_types.items():
            for t in range(count):

                card_type = random.choice(card_types) if card_types else ""
                currency = random.choice(currencies)
                symbol = CURRENCY_SYMBOLS.get(currency, "")
                low, high = CURRENCY_RANGES.get(currency, (100, 5000))

                amount_val = round(random.uniform(low, high), 2)
                amount = f"{symbol}{amount_val}"

                vendor = random.choice(VENDORS)
                txn_date = start + (end - start) * random.random()

                transactions.append({
                    "employee_id": employee_id,
                    "cardholder_name": cardholder_name,
                    "card_type": card_type,
                    "card_number": card_number,
                    "expense_type": expense,
                    "vendor_name": vendor,
                    "date": txn_date.strftime("%Y-%m-%d"),
                    "amount": amount,
                    "transaction_currency": currency
                })

        # -------- Negative Transactions --------
        for n in range(negative_count):

            card_type = random.choice(card_types) if card_types else ""
            currency = random.choice(currencies)
            symbol = CURRENCY_SYMBOLS.get(currency, "")
            low, high = CURRENCY_RANGES.get(currency, (50, 2000))

            neg_val = round(random.uniform(low/2, high/2), 2)
            neg_amount = f"-{symbol}{neg_val}"

            expense = random.choice(list(expense_types.keys()) or ["Misc"])
            vendor = random.choice(VENDORS)
            txn_date = start + (end - start) * random.random()

            transactions.append({
                "employee_id": employee_id,
                "cardholder_name": cardholder_name,
                "card_type": card_type,
                "card_number": card_number,
                "expense_type": expense,
                "vendor_name": vendor,
                "date": txn_date.strftime("%Y-%m-%d"),
                "amount": neg_amount,
                "transaction_currency": currency
            })

    return render_template("CC_Transaction.html", data=transactions)


@app.route("/download", methods=["POST"])
def download():

    data = request.form.get("data", "[]")
    file_type = request.form.get("file_type", "txt")

    try:
        transactions = json.loads(data)
    except Exception:
        transactions = []

    rows = []

    for idx, row in enumerate(transactions, start=1):

        txn_id = f"TXN{idx:05d}"
        name_on_card = row.get("cardholder_name", "")
        card_number = row.get("card_number", "")
        last_segment = card_number.split("-")[-1] if card_number else ""
        txn_type = row.get("expense_type", "")

        amount_raw = row.get("amount", "")
        for sym in CURRENCY_SYMBOLS.values():
            amount_raw = amount_raw.replace(sym, "")
        amount_raw = amount_raw.replace("-", "").strip()

        txn_currency = row.get("transaction_currency", "INR")
        txn_date = row.get("date", "")
        merchant = row.get("vendor_name", "")
        emp_id = row.get("employee_id", "")
        emp_name = f"Emp_{emp_id[-3:]}"

        rows.append([
            txn_id, name_on_card, last_segment, txn_type,
            amount_raw, txn_currency, txn_date, merchant,
            emp_id, emp_name
        ])
 # -------- TXT DOWNLOAD --------
    if file_type == "txt":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(rows)
        output.seek(0)

        return send_file(
            io.BytesIO(output.getvalue().encode("utf-8")),
            mimetype="text/csv",
            as_attachment=True,
            download_name="Transactions.txt"
        )

    # -------- EXCEL DOWNLOAD --------
    wb = Workbook()
    ws = wb.active

    for r in rows:
        ws.append(r)

    excel_stream = io.BytesIO()
    wb.save(excel_stream)
    excel_stream.seek(0)

    return send_file(
        excel_stream,
        as_attachment=True,
        download_name="Transactions.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


if __name__ == "__main__":
    app.run(debug=True)
