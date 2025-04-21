import cx_Oracle
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for

# Oracle DB connection
username = 'system'
password = 'abc123'
dsn = cx_Oracle.makedsn('localhost', 1521, sid='orcl')
connection = cx_Oracle.connect(username, password, dsn)
cursor = connection.cursor()

app = Flask(__name__)

def get_next_transaction_id():
    cursor.execute("SELECT NVL(MAX(transaction_id), 0) + 1 FROM transaction")
    return cursor.fetchone()[0]

def get_last_transaction_for_customer(name):
    cursor.execute("""
        SELECT * FROM transaction
        WHERE name = :1
        ORDER BY purchased_date DESC
        FETCH FIRST 1 ROWS ONLY
    """, (name,))
    return cursor.fetchone()

def get_last_stock_id():
    cursor.execute("SELECT NVL(MAX(stock_id), 0) FROM stockadding")
    return cursor.fetchone()[0]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/add_stock', methods=['GET', 'POST'])
def add_stock():
    if request.method == 'POST':
        stock_name = request.form['stock_name']
        stock_type = request.form['stock_type']
        stock_price = request.form['stock_price']
        stock_quantity = request.form['stock_quantity']  # New line

        last_stock_id = get_last_stock_id()
        stock_id = last_stock_id + 1

        try:
            cursor.execute("""
                INSERT INTO stockadding (stock_id, stock_name, stock_type, stock_price, stock_quantity)
                VALUES (:1, :2, :3, :4, :5)
            """, (stock_id, stock_name, stock_type, stock_price, stock_quantity))
            connection.commit()
            return redirect(url_for('home'))
        except cx_Oracle.IntegrityError:
            return "❌ Error in adding stock."

    return render_template('add_stock.html')

@app.route('/sell_product', methods=['GET', 'POST'])
@app.route('/sell_product', methods=['GET', 'POST'])
def sell_product():
    if request.method == 'POST':
        name = request.form['name']
        number = request.form['number']
        email = request.form['email']
        location = request.form['location']
        stock_id = request.form['stock_id']
        quantity = int(request.form['quantity'])

        # Get stock price and name
        cursor.execute("SELECT stock_name, stock_price FROM stockadding WHERE stock_id = :1", (stock_id,))
        result = cursor.fetchone()

        if result:
            stock_name, stock_price = result
            total_cost = stock_price * quantity
            purchased_date = datetime.now().date()
            transaction_id = get_next_transaction_id()

            # Insert into transaction table
            cursor.execute("""
                INSERT INTO transaction (transaction_id, name, contact_number, email, location, purchased_date, cost_purchased)
                VALUES (:1, :2, :3, :4, :5, :6, :7)
            """, (transaction_id, name, number, email, location, purchased_date, total_cost))
            connection.commit()

            # 👇 Pass bill details to template
            bill = {
                'stock_name': stock_name,
                'stock_id': stock_id,
                'stock_price': stock_price,
                'quantity': quantity,
                'total_cost': total_cost
            }

            return render_template('sell_product.html', bill=bill)

        else:
            return render_template('sell_product.html', bill=None, error="❌ Invalid stock ID")

    return render_template('sell_product.html')


@app.route('/view_transactions')
def view_transactions():
    cursor.execute("SELECT * FROM transaction")
    transactions = cursor.fetchall()
    return render_template('view_transactions.html', transactions=transactions)

if __name__ == '__main__':
    app.run(debug=True)
