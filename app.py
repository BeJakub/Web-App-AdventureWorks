from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc 
from jinja2 import select_autoescape
import datetime
from datetime import datetime

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
    OrderDate = db.Column(db.DateTime, default=datetime.utcnow)
    DueDate = db.Column(db.DateTime)
    ShipDate = db.Column(db.DateTime)
    CustomerID = db.Column(db.Integer, nullable=False)
    BillToAddressID = db.Column(db.Integer, nullable=False)
    ShipToAddressID = db.Column(db.Integer, nullable=False)
    ShipMethodID = db.Column(db.Integer)

class Customer(db.Model):
    __tablename__ = 'Customer'
    __table_args__ = {'schema': 'Sales'}
    CustomerID = db.Column(db.Integer, primary_key=True)
    
class Person(db.Model):
    __tablename__ = 'Person'
    __table_args__ = {'schema': 'Person'}
    BusinessEntityID = db.Column(db.Integer, primary_key=True)

class Address(db.Model):
    __tablename__ = 'Address'
    __table_args__ = {'schema': 'Person'}
    AddressID = db.Column(db.Integer, primary_key=True)
    AddressLine1 = db.Column(db.String(128))
    AddressLine2 = db.Column(db.String(128))
    City = db.Column(db.String(128))
    PostalCode = db.Column(db.Integer)
    StateProvinceID = db.Column(db.Integer)

class ShipMethod(db.Model):
    __tablename__ = 'ShipMethod'
    __table_args__ = {'schema': 'Purchasing'}
    ShipMethodID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(50))


@app.route('/')
def index():
    limit = request.args.get('limit', default=10, type=int)  # Odczytaj limit z parametrów zapytania, domyślnie 10
    orders = SalesOrderHeader.query.order_by(desc(SalesOrderHeader.SalesOrderID)).limit(limit).all()
    return render_template('index.html', orders=orders, limit=limit)
    

@app.route('/add', methods=['GET', 'POST'])
def add_order():
    ship_methods = ShipMethod.query.all()

    if request.method == 'POST':
        # Pobierz dane z formularza
        customer_id = request.form.get('customer_id', type=int)
        ship_method_id = request.form.get('ship_method_id', type=int)
        address_id = request.form.get('address_id', type=int)
        order_date = request.form.get('order_date')
        due_date = request.form.get('due_date')
        ship_date = request.form.get('ship_date')

        # Checkbox dla nowego klienta
        create_new_customer = 'new_customer_checkbox' in request.form
        if create_new_customer:
            # Tworzenie nowego klienta (pomijamy inne pola dla uproszczenia)
            new_customer = Customer()
            db.session.add(new_customer)
            db.session.flush()
            customer_id = new_customer.CustomerID
            
            new_address = Address(
                AddressLine1=request.form.get('new_address_line1'),
                AddressLine2=request.form.get('new_address_line2'),
                City=request.form.get('new_city'),
                StateProvinceID=request.form.get('new_state_province_id'),
                PostalCode=request.form.get('new_postal_code')
            )
            db.session.add(new_address)
            db.session.flush()
            address_id = new_address.AddressID

            bill_to_address_id = address_id
            ship_to_address_id = address_id
            
        else:
            bill_to_address_id = db.session.query(SalesOrderHeader.BillToAddressID).filter_by(CustomerID=customer_id).first()
            ship_to_address_id = db.session.query(SalesOrderHeader.ShipToAddressID).filter_by(CustomerID=customer_id).first()

            if bill_to_address_id:
                bill_to_address_id = bill_to_address_id[0]
            else:
                bill_to_address_id = None  

            if ship_to_address_id:
                ship_to_address_id = ship_to_address_id[0]
            else:
                ship_to_address_id = None
            


        # Tworzenie nowego obiektu SalesOrderHeader
        new_order = SalesOrderHeader(
            CustomerID=customer_id,
            BillToAddressID=bill_to_address_id,
            ShipToAddressID=ship_to_address_id,
            OrderDate=datetime.strptime(order_date, '%Y-%m-%d') if order_date else None,
            DueDate=datetime.strptime(due_date, '%Y-%m-%d') if due_date else None,
            ShipDate=datetime.strptime(ship_date, '%Y-%m-%d') if ship_date else None,
            ShipMethodID=ship_method_id,
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

    return render_template('add_order.html', ship_methods=ship_methods)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_order(id):
    order = SalesOrderHeader.query.get_or_404(id)

    if request.method == 'POST':
        # Pobieranie danych z formularza
        new_order_date = request.form.get('order_date')
        new_due_date = request.form.get('due_date')
        new_ship_date = request.form.get('ship_date')

        try:
            # Aktualizacja danych zamówienia
            if new_order_date:
                order.OrderDate = datetime.strptime(new_order_date, '%Y-%m-%d')
            if new_due_date:
                order.DueDate = datetime.strptime(new_due_date, '%Y-%m-%d')
            if new_ship_date:
                order.ShipDate = datetime.strptime(new_ship_date, '%Y-%m-%d')

            db.session.commit()
            flash('Dane zamówienia zaktualizowane.', 'success')
            return redirect(url_for('index'))  # Przekierowanie do głównego widoku
        except Exception as e:
            db.session.rollback()
            flash('Błąd podczas aktualizacji zamówienia: {}'.format(e), 'error')

    return render_template('edit_order.html', order=order)


@app.route('/delete/<int:id>')
def delete_order(id):
    order = SalesOrderHeader.query.get_or_404(id)
    db.session.delete(order)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True) 