from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc 
import datetime
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://@localhost/AdventureWorks2022?driver=ODBC+Driver+17+for+SQL+Server'
db = SQLAlchemy(app)

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
    orders = SalesOrderHeader.query.order_by(desc(SalesOrderHeader.OrderDate)).limit(limit).all()
    return render_template('index.html', orders=orders, limit=limit)
    

@app.route('/add', methods=['GET', 'POST'])
def add_order():
    # Logika dodawania zamówienia
    return render_template('add_order.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_order(id):
    # Logika edycji zamówienia
    return render_template('edit_order.html')

@app.route('/delete/<int:id>')
def delete_order(id):
    # Logika usuwania zamówienia
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)