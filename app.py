from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc 
from jinja2 import Environment, FileSystemLoader, select_autoescape
import datetime
from datetime import datetime
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://@localhost/AdventureWorks2022?driver=ODBC+Driver+17+for+SQL+Server'
db = SQLAlchemy(app)
app.secret_key = 'byczek123'

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

class Customer(db.Model):
    __tablename__ = 'Customer'
    __table_args__ = {'schema': 'Sales'}
    CustomerID = db.Column(db.Integer, primary_key=True)
    
class Person(db.Model):
    __tablename__ = 'Person'
    __table_args__ = {'schema': 'Person'}
    BusinessEntityID = db.Column(db.Integer, primary_key=True)
    # Include other fields as necessary

class Address(db.Model):
    __tablename__ = 'Address'
    __table_args__ = {'schema': 'Person'}
    AddressID = db.Column(db.Integer, primary_key=True)
    AddressLine1 = db.Column(db.String(128))
    AddressLine2 = db.Column(db.String(128))
    City = db.Column(db.String(128))
    PostalCode = db.Column(db.Integer)
    StateProvinceID = db.Column(db.Integer)
    # Include other fields as necessary

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
    addresses = Address.query.all()
    customers = db.session.query(Customer).all()

    

    if request.method == 'POST':
        # Pobierz dane z formularza
        customer_id = request.form.get('customer_id', type=int)
        address_id = request.form.get('address_id', type=int)
        ship_method_id = request.form.get('ship_method_id', type=int)
        order_date = request.form.get('order_date')
        due_date = request.form.get('due_date')
        ship_date = request.form.get('ship_date')
        existing_address_id = request.form.get('existing_address_id')
        # Jeżeli dodajemy nowy adres
        new_address_line1 = request.form.get('new_address_line1')
        new_address_line2 = request.form.get('new_address_line2')
        new_city = request.form.get('new_city')
        existing_customer_id = request.form.get('existing_customer_id', type=int)
        new_state_province_id = request.form['new_state_province_id']
        new_postal_code = request.form['new_postal_code']
        # Dodaj inne wymagane pola...
        
        # Checkbox dla nowego klienta
        create_new_customer = 'new_customer_checkbox' in request.form
        if create_new_customer:
            new_customer_name = request.form.get('new_customer_name') 
            # Tworzenie nowego klienta
            new_customer = Customer()  # Uzupełnij inne wymagane pola
            db.session.add(new_customer)
            db.session.flush()  # Aby uzyskać ID nowego klienta
            customer_id = new_customer.CustomerID
        else:
            customer_id = request.form.get('existing_customer_id', type=int)

        # Checkbox dla nowego adresu
        create_new_address = 'new_address_checkbox' in request.form
        if create_new_address:
            new_address_line1 = request.form.get('new_address_line1')
            new_address_line2 = request.form.get('new_address_line2')
            new_city = request.form.get('new_city')
            new_state_province_id = request.form.get('new_state_province_id')
            new_postal_code = request.form.get('new_postal_code')
            # Dodajemy nowy adres do bazy danych
            new_address = Address(
                AddressLine1=new_address_line1,
                AddressLine2=new_address_line2,
                City=new_city,
                StateProvinceID=new_state_province_id,
                PostalCode=new_postal_code
            )
            db.session.add(new_address)
            db.session.flush()  # To polecenie jest potrzebne, aby uzyskać ID dla nowo dodanego adresu
            address_id = new_address.AddressID
        else:
            address_id = request.form.get('existing_address_id', type=int)

        # Tworzenie nowego obiektu SalesOrderHeader
        new_order = SalesOrderHeader(
            CustomerID=customer_id,
            BillToAddressID=address_id,
            ShipToAddressID=address_id,
            OrderDate=datetime.strptime(order_date, '%Y-%m-%d') if order_date else None,
            DueDate=datetime.strptime(due_date, '%Y-%m-%d') if due_date else None,
            ShipDate=datetime.strptime(ship_date, '%Y-%m-%d') if ship_date else None,
            ShipMethodID=ship_method_id,
            # Przypisz wartości do innych pól...
        )

        db.session.add(new_order)
        try:
            db.session.commit()
            flash('Zamówienie zostało dodane pomyślnie.', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Wystąpił błąd podczas dodawania zamówienia: {e}', 'error')
            return render_template('error.html', error=str(e))

    # GET request
    return render_template('add_order.html', ship_methods=ship_methods,addresses=addresses, customers=customers)

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