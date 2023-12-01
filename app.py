from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc 
from jinja2 import Environment, FileSystemLoader, select_autoescape
import datetime
from datetime import datetime
import uuid
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://@localhost/AdventureWorks2022?driver=ODBC+Driver+17+for+SQL+Server'
app.config['SECRET_KEY'] = 'bardzotajnyklucz123'  # Statyczny klucz
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
class Person(db.Model):
    __tablename__ = 'Person'
    __table_args__ = {'schema': 'Person'}
    BusinessEntityID = db.Column(db.Integer, primary_key=True)
    # ... inne kolumny ...

class Address(db.Model):
    __tablename__ = 'Address'
    __table_args__ = {'schema': 'Person'}
    AddressID = db.Column(db.Integer, primary_key=True)
    # ... inne kolumny ...
    
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
        person_id = request.form.get('customer_id')
        # Dodaj inne wymagane pola...
        if person_id:
            existing_person = Person.query.get(person_id)
            if not existing_person:
                flash('Osoba o podanym ID nie istnieje.', 'error')
                return redirect(url_for('add_order'))

        # Jeśli nie podano ID klienta, stwórz nową osobę i adres
        else:
            new_person = Person(
                # Ustaw pola dla nowej osoby
            )
            db.session.add(new_person)
            db.session.flush()  # flush, aby uzyskać ID bez commitowania transakcji

            new_address = Address(
                # Ustaw pola dla nowego adresu
            )
            db.session.add(new_address)
            db.session.flush()  # podobnie, uzyskaj ID nowego adresu

            person_id = new_person.BusinessEntityID
            bill_to_address_id = new_address.AddressID
            ship_to_address_id = new_address.AddressID  # Możesz ustawić ten sam lub inny adres

            
            
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
            flash('Zamówienie zostało dodane.', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash('Nie udało się dodać zamówienia: {}'.format(str(e)), 'error')
            # Tu możesz obsłużyć błąd, np. wyświetlić komunikat o błędzie
            print(e)
            return render_template('error.html')  # Przykładowy


    return render_template('add_order.html',ship_methods=ship_methods)

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