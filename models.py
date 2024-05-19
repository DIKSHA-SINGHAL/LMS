from flask_sqlalchemy import SQLAlchemy
from app import app
from werkzeug.security import generate_password_hash
from datetime import datetime

db=SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=True)
    username = db.Column(db.String(32), unique=True)
    passhash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(64), nullable=True)
    feedbacks = db.relationship('Feedback', backref='user', lazy=True)

class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True)
    date_created = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    description = db.Column(db.Text, nullable=False)

    books = db.relationship('Book', backref='section', lazy=True)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), unique=True)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(64), nullable=False)
    price = db.Column(db.Float, nullable=False)
    rating = db.Column(db.Float, nullable=True)

    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    accesses = db.relationship('Access', backref='book', lazy=True)
    feedbacks = db.relationship('Feedback', backref='book', lazy=True)
    carts = db.relationship('Cart', backref='book', lazy=True)
    orders = db.relationship('Order', backref='book', lazy=True)

class Access(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    duration = db.Column(db.Integer, nullable=False, default=7)
    status = db.Column(db.String(25), nullable=False)
    borror_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    return_date = db.Column(db.Date, nullable=True)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    orders = db.relationship('Order', backref='transaction', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    


with app.app_context():
    db.create_all()

    admin = User.query.filter_by(role='admin').first()
    if not admin:
        password_hash = generate_password_hash('admin')
        admin = User(name='Admin', username='admin', passhash=password_hash, role='admin')
        db.session.add(admin)
        db.session.commit()