from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
import datetime
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://@localhost/AdventureWorks2022?driver=ODBC+Driver+17+for+SQL+Server'
app.config['SECRET_KEY'] = 'bardzotajnyklucz123'
db = SQLAlchemy(app)

# Funkcje pomocnicze
def format_date(value, format_string='%Y-%m-%d'):
    return "" if value is None else value.strftime(format_string)

app.jinja_env.filters['format_date'] = format_date

class SalesOrderHeader(db.Model):

    __tablename__ = 'SalesOrderHeader'
    __table_args__ = {'schema': 'Sales'}
    SalesOrderID = db.Column(db.Integer, primary_key=True)
    CustomerID = db.Column(db.Integer, nullable=False)
    OrderDate = db.Column(db.DateTime, nullable=False)
    DueDate = db.Column(db.DateTime, nullable=False)
    ShipDate = db.Column(db.DateTime)

    # Zmiana nazwy kolumny na AddressID i dodanie relacji do tabeli Address
    BillToAddressID = db.Column(db.Integer, db.ForeignKey('Person.Address.AddressID'), nullable=True)
    ShipToAddressID = db.Column(db.Integer, db.ForeignKey('Person.Address.AddressID'), nullable=True)
    ShipMethodID = db.Column(db.Integer, nullable=False)

     # Relacje (opcjonalnie, jeśli potrzebujesz odwoływać się do powiązanych obiektów Address)
    bill_to_address = db.relationship('Address', foreign_keys=[BillToAddressID])
    ship_to_address = db.relationship('Address', foreign_keys=[ShipToAddressID])

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

@app.route('/')
def index():
    limit = request.args.get('limit', default=10, type=int)  # Odczytaj limit z parametrów zapytania, domyślnie 10
    orders = SalesOrderHeader.query.order_by(desc(SalesOrderHeader.SalesOrderID)).limit(limit).all()
    return render_template('index.html', orders=orders, limit=limit)

@app.route('/add', methods=['GET', 'POST'])
def add_order():

    ship_methods = db.session.query(ShipMethod).all()
    if request.method == 'POST':

        customer_id = request.form.get('customer_id', type=int)

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
    
        ship_method_id = request.form.get('ship_method_id', type=int)
        order_date = request.form.get('order_date')
        due_date = request.form.get('due_date')
        ship_date = request.form.get('ship_date')

        # Utworzenie nowego obiektu SalesOrderHeader
        new_order = SalesOrderHeader(
            CustomerID=customer_id,
            BillToAddressID=bill_to_address_id,
            ShipToAddressID=ship_to_address_id,
            OrderDate=datetime.strptime(order_date, '%Y-%m-%d') if order_date else datetime.utcnow(),
            DueDate=datetime.strptime(due_date, '%Y-%m-%d') if due_date else None,
            ShipDate=datetime.strptime(ship_date, '%Y-%m-%d') if ship_date else None,
            ShipMethodID=ship_method_id
            # Uzupełnij inne wymagane pola...
        )

        # Dodaj zamówienie do sesji i zapisz w bazie danych
        db.session.add(new_order)
        try:
            db.session.commit()
            flash('Zamówienie zostało dodane.', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            error_message = f'Nie udało się dodać zamówienia: {str(e)}'
            flash(error_message, 'error')
            return render_template('add_order.html', ship_methods=ship_methods)


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