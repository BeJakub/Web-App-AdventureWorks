from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc 
from jinja2 import Environment, FileSystemLoader, select_autoescape
import datetime
from datetime import datetime
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://@localhost/AdventureWorks2022?driver=ODBC+Driver+17+for+SQL+Server'
db = SQLAlchemy(app)

def format_date(value, format_string='%Y-%m-%d'):
    if value is None:
        return ""
    return value.strftime(format_string)

app.jinja_env.filters['format_date'] = format_date

class SalesOrderHeader(db.Model):
    __tablename__ = 'SalesOrderHeader'
    __table_args__ = {'schema': 'Sales'}
    SalesOrderID = db.Column(db.Integer, primary_key=True)
    RevisionNumber = db.Column(db.SmallInteger, default=0)
    OrderDate = db.Column(db.DateTime, default=datetime.utcnow)
    DueDate = db.Column(db.DateTime)
    ShipDate = db.Column(db.DateTime)
    Status = db.Column(db.SmallInteger, default=1)
    OnlineOrderFlag = db.Column(db.Boolean, default=True)
    #SalesOrderNumber = db.Column(db.String(25))  # Computed column
    PurchaseOrderNumber = db.Column(db.String(25))
    AccountNumber = db.Column(db.String(15))
    CustomerID = db.Column(db.Integer, nullable=False)
    SalesPersonID = db.Column(db.Integer)
    TerritoryID = db.Column(db.Integer)
    BillToAddressID = db.Column(db.Integer, nullable=False)
    ShipToAddressID = db.Column(db.Integer, nullable=False)
    ShipMethodID = db.Column(db.Integer)
    CreditCardID = db.Column(db.Integer)
    CreditCardApprovalCode = db.Column(db.String(15))
    CurrencyRateID = db.Column(db.Integer)
    SubTotal = db.Column(db.Numeric, default=0.00)
    TaxAmt = db.Column(db.Numeric, default=0.00)
    Freight = db.Column(db.Numeric, default=0.00)
    #TotalDue = db.Column(db.Numeric)  # Computed column
    Comment = db.Column(db.String(128))
    rowguid = db.Column(db.String(36), default=lambda: str(uuid.uuid4()))
    ModifiedDate = db.Column(db.DateTime, default=datetime.utcnow)


class ShipMethod(db.Model):
    __tablename__ = 'ShipMethod'
    __table_args__ = {'schema': 'Purchasing'}
    ShipMethodID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(50))
    ShipBase = db.Column(db.Numeric(10, 2))
    ShipRate = db.Column(db.Numeric(10, 2))
    # Dodaj więcej pól jeśli są potrzebne

@app.route('/')
def index():
    limit = request.args.get('limit', default=10, type=int)  # Odczytaj limit z parametrów zapytania, domyślnie 10
    orders = SalesOrderHeader.query.order_by(desc(SalesOrderHeader.SalesOrderID)).limit(limit).all()
    return render_template('index.html', orders=orders, limit=limit)
    

@app.route('/add', methods=['GET', 'POST'])
def add_order():
    ship_methods = db.session.query(ShipMethod).all()
    if request.method == 'POST':
        # Pobierz dane z formularza
        customer_id = request.form.get('customer_id')
        bill_to_address_id = request.form.get('bill_to_address_id', type=int)
        ship_to_address_id = request.form.get('ship_to_address_id', type=int)
        ship_method_id = request.form.get('ship_method_id', type=int)
        order_date = request.form.get('order_date')
        due_date = request.form.get('due_date')
        ship_date = request.form.get('ship_date')
        # Dodaj inne wymagane pola...

        # Tworzenie nowego obiektu SalesOrderHeader
        new_order = SalesOrderHeader(
            CustomerID=customer_id,
            BillToAddressID=bill_to_address_id,
            ShipToAddressID=ship_to_address_id,
            OrderDate=datetime.strptime(order_date, '%Y-%m-%d') if order_date else None,
            DueDate=datetime.strptime(due_date, '%Y-%m-%d') if due_date else None,
            ShipDate=datetime.strptime(ship_date, '%Y-%m-%d') if ship_date else None,
            ShipMethodID=ship_method_id,
            # Przypisz wartości do innych pól...
        )

        # Dodaj zamówienie do sesji i zapisz w bazie danych
        db.session.add(new_order)
        try:
            db.session.commit()
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            # Tu możesz obsłużyć błąd, np. wyświetlić komunikat o błędzie
            print(e)
            return render_template('error.html')  # Przykładowy


    return render_template('add_order.html',ship_methods=ship_methods)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_order(id):
    order = SalesOrderHeader.query.get_or_404(id)
    if request.method == 'POST':
        # Aktualizuj zamówienie
        order.OrderDate = request.form['order_date']
        # Aktualizuj inne pola
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('edit_order.html', order=order)

@app.route('/delete/<int:id>')
def delete_order(id):
    order = SalesOrderHeader.query.get_or_404(id)
    db.session.delete(order)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)