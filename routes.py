from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, User, Book, Section, Issues, Issued
from app import app
from sqlalchemy.exc import OperationalError
import time
from functools import wraps
from sqlalchemy import DateTime 
from werkzeug.security import generate_password_hash, check_password_hash

# @app.route('/')
# def index():
#     users = User.query.all()
#     return render_template('index.html', users = users)

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('Please fill out all fields')
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=username).first()
    
    if not user:
        flash('Username does not exist')
        return redirect(url_for('login'))
    
    if not check_password_hash(user.passhash, password):
        flash('Incorrect password')
        return redirect(url_for('login'))
    
    session['user_id'] = user.id
    flash('Login successful')
    return redirect(url_for('index'))


@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_post():
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    name = request.form.get('name')

    if not username or not password or not confirm_password:
        flash('Please fill out all fields')
        return redirect(url_for('register'))
    
    if password != confirm_password:
        flash('Passwords do not match')
        return redirect(url_for('register'))
    
    user = User.query.filter_by(username=username).first()

    if user:
        flash('Username already exists')
        return redirect(url_for('register'))
    
    password_hash = generate_password_hash(password)
    
    new_user = User(username=username, passhash=password_hash, name=name)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('login'))


# decorator for auth_required

def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' in session:
            return func(*args, **kwargs)
        else:
            flash('Please login to continue')
            return redirect(url_for('login'))
    return inner

def admin_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user.is_admin:
            flash('You are not authorized to access this page')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return inner

@app.route('/profile')
@auth_required
def profile():
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)

@app.route('/profile', methods=['POST'])
@auth_required
def profile_post():
    username = request.form.get('username')
    cpassword = request.form.get('cpassword')
    password = request.form.get('password')
    name = request.form.get('name')

    if not username or not cpassword or not password:
        flash('Please fill out all the required fields')
        return redirect(url_for('profile'))

    if 'user_id' not in session:
        flash('User session not found. Please log in again.')
        return redirect(url_for('login'))  # Redirect to login if user session is missing

    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
        flash('User not found.')
        return redirect(url_for('login'))  # Redirect to login if user not found

    if not check_password_hash(user.passhash, cpassword):
        flash('Incorrect password')
        return redirect(url_for('profile'))

    if username != user.username:
        new_username = User.query.filter_by(username=username).first()
        if new_username:
            flash('Username already exists')
            return redirect(url_for('profile'))

    new_password_hash = generate_password_hash(password)
    user.username = username
    user.passhash = new_password_hash
    user.name = name
    db.session.commit()
    flash('Profile updated successfully')
    return redirect(url_for('profile'))

@app.route('/logout')
#@auth_required
def logout():
    session.pop('user_id')
    return redirect(url_for('login'))

    # --- admin pages

@app.route('/admin')
@admin_required
def admin():
    sections = Section.query.all()
    return render_template('admin.html', sections=sections)

@app.route('/dashboard')
@admin_required
def dashboard():
    user = User.query.get(session['user_id'])
    users = User.query.all()
    books = Book.query.all()
    pending = Issues.query.all()
    issued = Issued.query.all()
    sections = Section.query.all()
    return render_template('dashboard.html', sections=sections, user=user, users = users, pending=pending, issued=issued, book = books)

@app.route('/section/add')
@admin_required
def add_section():
    return render_template('section/add.html')

from datetime import datetime
import uuid
@app.route('/section/add', methods=['POST'])
@admin_required
def add_section_post():
    # uid = str(uuid.uuid4())
    name = request.form.get('name')
    date_str = request.form.get('date')  # YYYY-MM-DD format
    description = request.form.get('description')

    if not name or not description:
        flash('Please fill out all fields')
        return redirect(url_for('add_section'))

    try:
        # Parse the date string into a datetime object
        date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        flash('Invalid date format. Please use YYYY-MM-DD format')
        return redirect(url_for('add_section'))

    new_section = Section(name=name, datecreated=date, description=description)
    db.session.add(new_section)
    db.session.commit()

    flash('Section added successfully')
    return redirect(url_for('admin'))


@app.route('/section/<int:id>/')
@admin_required
def show_section(id):
    section = Section.query.get(id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin'))
    return render_template('section/show.html', section=section)


@app.route('/section/<int:id>/edit')
@admin_required
def edit_section(id):
    section = Section.query.get(id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin'))
    return render_template('section/edit.html', section=section)

@app.route('/section/<int:id>/edit', methods=['POST'])
@admin_required
def edit_section_post(id):
    section = Section.query.get(id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin'))
    name = request.form.get('name')
    if not name:
        flash('Please fill out all fields')
        return redirect(url_for('edit_section', id=id))
    section.name = name
    db.session.commit()
    flash('Section updated successfully')
    return redirect(url_for('admin'))

@app.route('/section/<int:id>/delete')
@admin_required
def delete_section(id):
    section = Section.query.get(id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin'))
    return render_template('section/delete.html', section=section)

@app.route('/section/<int:id>/delete', methods=['POST'])
@admin_required
def delete_section_post(id):
    section = Section.query.get(id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin'))

    # Set section_id to NULL for books referencing this section
    books_with_section = Book.query.filter_by(section_id=id).all()
    for book in books_with_section:
        db.session.delete(book)

    # Now, delete the section
    db.session.delete(section)
    db.session.commit()

    flash('Section deleted successfully')
    return redirect(url_for('admin'))

@app.route('/book/add/<int:section_id>')
@admin_required
def add_book(section_id):
    sections = Section.query.all()
    section = Section.query.get(section_id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin'))
    return render_template('book/add.html', section=section, sections=sections)

@app.route('/book/add/', methods=['POST'])
@admin_required
def add_book_post():
    name = request.form.get('name')
    author = request.form.get('author')
    content = request.form.get('content')
    status = 'Available'

    # Retrieve section_id from the URL parameters
    section_id = request.args.get('section_id')

    # Alternatively, retrieve section_id from session if stored there
    # section_id = session.get('section_id')

    if not section_id:
        flash('Section ID is missing')
        return redirect(url_for('admin'))

    section = Section.query.get(section_id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin'))

    if not name or not author or not content:
        flash('Please fill out all fields')
        return redirect(url_for('add_book', section_id=section_id, author=author, content=content))

    book = Book(name=name, status = status, section_id=section_id, author=author, content=content)
    db.session.add(book)
    db.session.commit()

    flash('Book added successfully')
    return redirect(url_for('show_section', id=section_id))

@app.route('/book/<int:id>/edit')
@admin_required
def edit_book(id):
    section = Section.query.all()
    book = Book.query.get(id)
    return render_template('book/edit.html', section=section, book=book)

@app.route('/book/<int:id>/edit', methods=['POST'])
@admin_required
def edit_book_post(id):
    name = request.form.get('name')
    author = request.form.get('author')
    content = request.form.get('content')

    book = Book.query.get(id)
    if not book:
        flash('Book does not exist')
        return redirect(url_for('admin'))

    # Retrieve the section ID associated with the book
    section_id = book.section_id

    # Update the book attributes
    book.name = name
    book.author = author
    book.content = content

    # Commit the changes to the database
    db.session.commit()

    flash('Book edited successfully')
    return redirect(url_for('show_section', id=section_id))

@app.route('/book/<int:id>/delete')
@admin_required
def delete_book(id):
    book = Book.query.get(id)
    if not book:
        flash('Book does not exist')
        return redirect(url_for('admin'))
    return render_template('book/delete.html', book=book)

@app.route('/book/<int:id>/delete', methods=['POST'])
@admin_required
def delete_book_post(id):
    book = Book.query.get(id)
    if not book:
        flash('Book does not exist')
        return redirect(url_for('admin'))
    section_id = book.section.id
    db.session.delete(book)
    db.session.commit()

    flash('Book deleted successfully')
    return redirect(url_for('show_section', id=section_id))


# user pages 
@app.route('/')
@auth_required
def index():
    sections = Section.query.all()
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if not user:
            flash('User does not exist.')
            return redirect(url_for('login'))
        if user.is_admin:
            return render_template('admin.html', user=user, sections=sections)
    return render_template('index.html', user=user, sections=sections)


from sqlalchemy.exc import PendingRollbackError
from sqlalchemy import or_

@app.route('/request_book', methods=['POST'])
def request_book():
    book_id = request.form.get('book_id')
    
    # Check if the book ID is provided
    if not book_id:
        flash('Invalid request. Please provide a book ID.')
        return redirect(url_for('index'))
    
    # Get the book from the database
    book = Book.query.get(book_id)
    user_id = session.get('user_id')
    
    # Check if the user is logged in
    if not user_id:
        flash('User is not logged in.')
        return redirect(url_for('index'))
    
    # Check if the user already has 5 books issued or requested
    total_requested = Issues.query.filter_by(user_id=user_id, status='Requested').count()
    total_issued = Issued.query.filter_by(user_id=user_id).count()

    total_books = total_requested + total_issued

    if total_books >= 5:
        flash('You cannot request more than 5 books. Please return some books before making a new request.')
        return redirect(url_for('index'))
    
    # Check if the book and user exist
    if not book or not user_id:
        flash('Book or user not found.')
        return redirect(url_for('index'))
    
    # Check if the book status is "Requested"
    if book.status == 'Requested':
        flash('Book is already requested.')
        return redirect(url_for('index'))

    # Retry logic to handle database lock issues
    retries = 3  # Number of retries
    for _ in range(retries):
        try:
            # Create a new request for the book
            new_request = Issues(book_id=book_id, user_id=user_id, status='Requested')
            db.session.add(new_request)
            book.status = 'Requested'
            db.session.commit()
            flash('Book request submitted successfully')
            return redirect(url_for('index'))
        except (OperationalError, PendingRollbackError) as e:
            print(f"Database is locked. Retrying in 1 second... Retry count: {_ + 1}")
            time.sleep(1)
            continue
    else:
        # If retries are exhausted, return an error message
        flash('Failed to submit book request due to database lock. Please try again later.')
        return redirect(url_for('index'))

@app.route('/return_book', methods=['POST'])
def return_book():
    # Get the book ID and status from the form
    book_id = request.form.get('book_id')
    status = request.form.get('status')
    
    # Check if the user is logged in
    if 'user_id' not in session:
        flash('User is not logged in.')
        return redirect(url_for('index'))

    user_id = session['user_id']

    # Retrieve the issued book record
    issued_book = Issued.query.filter_by(id=book_id).first()

    if issued_book:
        # Check if the user matches the one who issued the book
        if issued_book.user_id == user_id:
            # Update the book status to Available
            issued_book.book.status = 'Available'
            # Delete the issued book record
            db.session.delete(issued_book)
            db.session.commit()
            flash('Book returned successfully')
        else:
            flash('You are not authorized to return this book.')
    else:
        flash('Book is not issued')

    return redirect(url_for('index'))

# Flask Route for managing requests
@app.route('/manage_request')
@admin_required
def manage_request():
    user = User.query.get(session['user_id'])
    requests = Issues.query.all()
    requests2 = Issued.query.all()
    return render_template('manage_request.html', user = user, issues=requests, issued = requests2)

# Flask Route for approving a request
@app.route('/approve_request', methods=['POST'])
def approve_request():
    request_id = request.form.get('request_id')  # Assuming you have a form field for request_id
    action = request.form.get('action')
    request_item = Issues.query.get(request_id)
    user_id = request_item.user_id

    if request_item:
        book_id = request_item.book_id
        book = Book.query.get(book_id)
        
        if book:
            if action == 'accept' and book.status == 'Requested':
                book.status = 'Issued'  # Update book status
                request_item.status = 'Approved'
                new_issued = Issued(book_id=book_id, user_id=user_id)
                db.session.add(new_issued)
                db.session.delete(request_item)
                db.session.commit()
                flash('Request approved successfully')
            elif action == 'decline':
                book.status = 'Available'  # Update book status
                db.session.delete(request_item)
                db.session.commit()
                flash('Request declined successfully')
            else:
                flash('Invalid action or book is not available for issuance')
    
    return redirect(url_for('manage_request'))

@app.route('/student_books')
def student_books():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            if user.is_admin:
                sections = Section.query.all()
                return render_template('manage_request.html', user=user, sections=sections)
            else:
                sections = Section.query.all()
                requests = Issues.query.all()
                requests2 = Issued.query.all()
                return render_template('student_books.html', user=user, userid = session['user_id'], issues=requests, issued=requests2)
        else:
            # Handle the case where user does not exist in the database
            flash('User does not exist.')
            return redirect(url_for('login'))