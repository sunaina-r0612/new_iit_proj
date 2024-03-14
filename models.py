from app import app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime 
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable = False)
    passhash = db.Column(db.String(512), nullable = False)
    name = db.Column(db.String(64), nullable=True)
    is_admin = db.Column(db.Boolean, nullable = False, default = False)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.passhash = generate_password_hash(self.passhash, password)


    def check_password(self, password):
        return self.passhash == check_password_hash(self.passhash,password)

class Book(db.Model):
    __tablename__ = 'book'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    content = db.Column(db.String(512), unique=True, nullable = False)
    author = db.Column(db.String(64), nullable = False)
    dateissue = db.Column(DateTime, nullable = True)
    status = db.Column(db.String(64), nullable = True)

class Section(db.Model):
    __tablename__ = 'section'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=True)
    datecreated = db.Column(DateTime, nullable = False)
    description = db.Column(db.String(512), unique=True, nullable = False)

    #relationships
    bookname = db.relationship('Book', backref='section', lazy=True)

class Issues(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    status = db.Column(db.String(64), default='Pending')  # Add a status column

    user = db.relationship('User', backref='issues')
    book = db.relationship('Book', backref='issues')

class Issued(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)

    user = db.relationship('User', backref='issued')
    book = db.relationship('Book', backref='issued')
 
#craete db if doesn't exist
with app.app_context():
    db.create_all()
    # if admin exists, else create admin
    admin = User.query.filter_by(is_admin=True).first()
    if not admin:
        password_hash = generate_password_hash('admin')
        admin = User(username='admin', passhash=password_hash, name='admin', is_admin=True)
        db.session.add(admin)
        db.session.commit()