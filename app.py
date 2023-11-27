from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc 
from jinja2 import Environment, FileSystemLoader, select_autoescape
import datetime
from datetime import datetime

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
    OrderDate = db.Column(db.DateTime, default=datetime.utcnow)
    DueDate = db.Column(db.DateTime)
    ShipDate = db.Column(db.DateTime)

@app.route('/')
def index():
    limit = request.args.get('limit', default=10, type=int)  # Odczytaj limit z parametrów zapytania, domyślnie 10
    orders = SalesOrderHeader.query.order_by(desc(SalesOrderHeader.SalesOrderID)).limit(limit).all()
    return render_template('index.html', orders=orders, limit=limit)
    

@app.route('/add', methods=['GET', 'POST'])
def add_order():
    if request.method == 'POST':
        # Pobierz dane z formularza i stwórz nowe zamówienie
        new_order = SalesOrderHeader(...)
        db.session.add(new_order)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_order.html')

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