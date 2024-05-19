from app import app
from flask import render_template, request, redirect, url_for, flash, session
from models import db, User, Section, Book, Access, Cart, Transaction, Order, Feedback
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta


# ----------------------HOME----------------------------------------------------------
# DEFINES ROLE:USER/ADMIN
@app.route('/')
def index():
	if 'user_id' in session:
		session.pop('user_id')
	return render_template('index.html')

@app.route('/', methods=['POST'])
def select_role():
	if 'user' in request.form:
		return redirect(url_for('user_login'))
	elif 'admin' in request.form:
		return redirect(url_for('admin_login'))
#---------------------END-------------------------------------------------------------


#---------------------REGISTER---------------------------------------------------------
# ONLY USER CAN REGISTER
@app.route('/user/register')
def user_register():
	return render_template('user/register.html')

@app.route('/user/register', methods=['POST'])
def user_register_post():
	name = request.form.get('name')
	username = request.form.get('username')
	password = request.form.get('password')
	confirm_password = request.form.get('confirm_password')

	if not name or not username or not password or not confirm_password:
		flash('Please fill out all necessary details.')
		return redirect(url_for('user_register'))
	
	if password != confirm_password:
		flash('Passwords do not match. Please try again')
		return redirect(url_for('user_register'))
	
	user = User.query.filter_by(username=username).first()

	if user:
		flash('Username already exists. Please login')
		return redirect(url_for('user_login'))
	
	password_hash = generate_password_hash(password)

	new_user = User(name=name, username=username, passhash=password_hash, role='user')
	db.session.add(new_user)
	db.session.commit()
	
	flash('User registered successfully')
	return redirect(url_for('user_login'))
#---------------------------END-----------------------------------------------------------------


#--------------------------LOGIN-----------------------------------------------------------------
# ADMIN LOGIN
@app.route('/admin/login')
def admin_login():
	return render_template('admin/login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
	username = request.form.get('username')
	password = request.form.get('password')

	if not username or not password:
		flash('Please fill out all necessary details')
	
	user = User.query.filter_by(username=username).first()

	if not user:
		flash('Username does not exist. Are you a user?')
		return redirect(url_for('/'))
	
	if not check_password_hash(user.passhash, password):
		flash('Incorrect password. Please try again')
		return redirect(url_for('admin_login'))
	
	session['user_id'] = user.id
	flash('Login Successful')
	return redirect(url_for('admin_dashboard'))

# USER LOGIN
@app.route('/user/login')
def user_login():
	return render_template('user/login.html')

@app.route('/user/login', methods=['POST'])
def user_login_post():
	username = request.form.get('username')
	password = request.form.get('password')

	if not username or not password:
		flash('Please fill out all necessary details')
	
	user = User.query.filter_by(username=username).first()

	if not user:
		flash('Username does not exist. Please register')
		return redirect(url_for('user_register'))
	
	if not check_password_hash(user.passhash, password):
		flash('Incorrect password. Please try again')
		return redirect(url_for('user_login'))
	
	session['user_id'] = user.id
	flash('Login Successful')
	return redirect(url_for('user_dashboard'))
#----------------------------------END----------------------------------------------------

#----------------------------------AUTH---------------------------------------------------
def auth_required(func):
	@wraps(func)
	def inner(*args, **kwargs):
		if 'user_id' not in session:
			flash('Please login to continue')
			return redirect(url_for('user_login'))
		user = User.query.get(session['user_id'])
		if user.role != 'user':
			flash('You are not authorized to access this page')
			return redirect(url_for('index'))
		return func(*args, **kwargs)
	return inner

def admin_required(func):
	@wraps(func)
	def inner(*args, **kwargs):
		if 'user_id' not in session:
			flash('Please login to continue')
			return redirect(url_for('admin_login'))
		user = User.query.get(session['user_id'])
		if user.role != 'admin':
			flash('You are not authorized to access this page')
			return redirect(url_for('index'))
		return func(*args, **kwargs)
	return inner
#-------------------------------------END------------------------------------------------------


#--------------------------------------------------PROFILE----------------------------------------------------------------------
@app.route('/user/profile')
@auth_required
def profile():
    user = User.query.get(session['user_id'])
    return render_template('/user/profile.html', user=user)

@app.route('/user/profile', methods=['POST'])
@auth_required
def profile_post():
    username = request.form.get('username')
    cpassword = request.form.get('cpassword')
    password = request.form.get('password')
    name = request.form.get('name')

    if not username or not cpassword or not password:
        flash('Please fill out all the required fields')
        return redirect(url_for('profile'))
    
    user = User.query.get(session['user_id'])
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
#--------------------------------------------------END--------------------------------------------------------------------------


#-------------------------------------LOGOUT---------------------------------------------------
@app.route('/logout')
def logout():
	session.pop('user_id')
	return redirect(url_for('index'))
#--------------------------------------	END----------------------------------------------------


#--------------------------------------ADMIN DASHBOARD----------------------------------------------------
@app.route('/admin')
@admin_required
def admin_dashboard():
	user = User.query.get(session['user_id'])
	sections = Section.query.all()

	name = request.args.get('name') or ''
	if name:
		sections = Section.query.filter(Section.name.ilike(f'%{name}%')).all()

	return render_template('admin/dashboard.html', user=user, sections=sections)
#----------------------------------------END----------------------------------------------------------------


#-------------------------------------SECTION------------------------------------------------------------------
# CREATE SECTION
@app.route('/section/add')
@admin_required
def add_section():
	user = User.query.get(session['user_id'])
	return render_template('/section/add.html', user=user)

@app.route('/section/add', methods=['POST'])
@admin_required
def add_section_post():
	name = request.form.get('name')
	description = request.form.get('description')

	if not name or not description:
		flash('Please fill out all fields')
		return redirect(url_for('add_section'))
	
	duplicate_section = Section.query.filter_by(name=name).first()
	if duplicate_section:
		flash('Section already exists')
		return redirect(url_for('admin_dashboard'))
	
	section = Section(name=name, description=description)
	db.session.add(section)
	db.session.commit()

	flash('Section added successfully')
	return redirect(url_for('admin_dashboard'))


# DELETE SECTION
@app.route('/section/<int:id>/delete', methods=['POST'])
@admin_required
def delete_section(id):
	section = Section.query.get(id)

	db.session.delete(section)
	db.session.commit()

	flash('Section deleted successfully')
	return redirect(url_for('admin_dashboard'))

# EXPLORE SECTION
@app.route('/section/<int:id>')
@admin_required
def explore_section(id):
	user = User.query.get(session['user_id'])
	section = Section.query.get(id)

	name = request.args.get('name') or ''
	
	return render_template('section/explore.html', user=user, section=section, name=name)

#UPDATE SECTION
@app.route('/section/<int:id>/update')
@admin_required
def update_section(id):
	user = User.query.get(session['user_id'])
	section = Section.query.get(id)
	return render_template('/section/update.html', user=user, section=section)

@app.route('/section/<int:id>/update', methods=['POST'])
@admin_required
def update_section_post(id):
	name = request.form.get('name')
	description = request.form.get('description')

	duplicate_section = Section.query.filter_by(name=name).first()
	if duplicate_section and duplicate_section.id != id:
		flash('Section already exists. Use a different name')
		return redirect(url_for('update_section', id=id))

	section = Section.query.get(id)
	section.name = name
	section.date_created = datetime.utcnow()
	section.description = description
	db.session.commit()
	flash('Section updated successfully')
	return redirect(url_for('admin_dashboard'))
#----------------------------------------------END-----------------------------------------------------


#---------------------------------------------BOOK------------------------------------------------------
# ADD BOOK
@app.route('/book/<int:id>/add')
@admin_required
def add_book(id):
	user = User.query.get(session['user_id'])
	section = Section.query.get(id)
	return render_template('book/add.html', user=user, section=section)

@app.route('/book/<int:id>/add', methods=['POST'])
@admin_required
def add_book_post(id):
	title = request.form.get('title')
	content = request.form.get('content')
	author = request.form.get('author')
	price = request.form.get('price')

	if not title or not content or not author or not price:
		flash('Please fill out all necessary details')
		return redirect(url_for('add_book', id=id))

	book = Book.query.filter_by(section_id = id, title=title).first()
	if book:
		flash('Book already exists')
		return redirect(url_for('explore_section', id=id))
	
	try:
		price = float(price)
	except ValueError:
		flash('Invalid price')
		return redirect(url_for('add_book', id=id))
	
	if price < 50:
		flash(f'Price must be greater than or equal to {chr(0x20B9)} 50')
		return redirect(url_for('add_book', id=id))
	
	section = Section.query.get(id)
	book = Book(title=title, content=content, author=author, price=price, section=section)
	db.session.add(book)
	db.session.commit()

	flash('Book added successfully')
	return redirect(url_for('explore_section', id=id))

# DELETE BOOK
@app.route('/book/<int:id>/delete', methods=['POST'])
@admin_required
def delete_book(id):
	book = Book.query.get(id)
	section_id = book.section_id

	db.session.delete(book)
	db.session.commit()

	flash('Book deleted successfully')
	return redirect(url_for('explore_section', id=section_id))

# UPDATE BOOK
@app.route('/book/<int:id>/update')
@admin_required
def update_book(id):
	user = User.query.get(session['user_id'])
	book = Book.query.get(id)
	sections = Section.query.all()
	return render_template('/book/update.html', user=user, book=book, sections=sections)

@app.route('/book/<int:id>/update', methods=['POST'])
@admin_required
def update_book_post(id):
	title = request.form.get('title')
	section_id = request.form.get('section_id')
	content = request.form.get('content')
	author = request.form.get('author')
	price = request.form.get('price')

	if not title or not section_id or not content or not author or not price:
		flash('Please fill out all necessary details')
		return redirect(url_for('update_book', id=id))

	duplicate_book = Book.query.filter_by(title=title).first()
	if duplicate_book and duplicate_book.id != id:
		flash('Book already exists. Use a different name')
		return redirect(url_for('update_section', id=id))
	
	try:
		price = float(price)
	except ValueError:
		flash('Invalid price')
		return redirect(url_for('update_book', id=id))
	
	if price < 50:
		flash(f'Price must be greater than or equal to {chr(0x20B9)} 50')
		return redirect(url_for('update_book', id=id))

	book = Book.query.get(id)
	book.title = title
	book.content = content
	book.author = author
	book.price = price
	book.section_id = section_id
	db.session.commit()
	flash('Book updated successfully')
	return redirect(url_for('admin_dashboard'))	 
#-----------------------------------END-------------------------------------------------------------

#---------------------------------------REQUESTS----------------------------------------------------------
@app.route('/requests')
@admin_required
def requests():
	user = User.query.get(session['user_id'])
	accesses = Access.query.all()

	name = request.args.get('name') or ''

	return render_template('admin/requests.html', user=user, accesses=accesses, name=name)
#------------------------------------END---------------------------------------------------------------


#---------------------------------------STATS----------------------------------------------------------
@app.route('/admin/stats')
@admin_required
def admin_stats():
	user = User.query.get(session['user_id'])

	sections = Section.query.all()
	section_names = [section.name for section in sections]
	section_sizes = [len(section.books) for section in sections]

	books = Book.query.all()
	book_names = [book.title for book in books]
	book_sizes = [len(book.accesses) for book in books]
	
	return render_template('admin/stats.html', user=user, sections=sections,
						section_names=section_names, section_sizes=section_sizes,
						book_names=book_names, book_sizes=book_sizes)
#------------------------------------END---------------------------------------------------------------


#--------------------------------------USER DASHBOARD-----------------------------------------------------------
@app.route('/user/dashboard')
@auth_required
def user_dashboard():
	user = User.query.get(session['user_id'])
	books = Book.query.all()

	sname = request.args.get('sname') or ''
	bname = request.args.get('bname') or ''
	aname = request.args.get('aname') or ''
	price = request.args.get('price')

	if price:
		try:
			price = float(price)
		except:
			price = 0

	if bname:
		books = Book.query.filter(Book.title.ilike(f'%{bname}%')).all()

	return render_template('user/dashboard.html', user=user, books=books, sname=sname, bname=bname, aname=aname, price=price)
#--------------------------------------------------END--------------------------------------------------------------------------


#---------------------------------REQUEST ACCESS--------------------------------------------------------------------------------
@app.route('/book/<int:id>/request', methods=['POST'])
@auth_required
def request_access_post(id):
	duration = request.form.get('duration')

	if not duration:
		flash('Please fill out the request duration')
		return redirect(url_for('user_dashboard'))
	
	try:
		duration = int(duration)
	except ValueError:
		flash('Duration must be an integer')
		return redirect(url_for('user_dashboard'))
	
	if duration > 7:
		flash('Duration must be less than or equal to 7.')
		return redirect(url_for('user_dashboard'))
	
	duplicate_request = Access.query.filter_by(user_id=session['user_id'], book_id=id, status="granted").first()
	if duplicate_request:
		flash('Access already exists')
		return redirect(url_for('user_dashboard'))
	
	requests = Access.query.filter_by(user_id=session['user_id'], status="granted").count()
	if requests >= 5:
		flash('A user can request maximum of 5 books. Return books to continue reading')
		return redirect(url_for('user_dashboard'))

	revoke_request = Access.query.filter_by(user_id=session['user_id'], book_id=id, status="returned").first()
	return_date = datetime.utcnow() + timedelta(days=duration)
	if revoke_request:
		flash('Access revoked successfully')
		revoke_request.duration=duration
		revoke_request.status = "revoked"
		revoke_request.return_date = return_date
		db.session.commit()
		return redirect(url_for('my_books'))
	
	flash('Access granted successfully')
	access = Access(user_id=session['user_id'], book_id=id, duration=duration, status="granted", return_date=return_date)
	
	db.session.add(access)
	db.session.commit()
	return redirect(url_for('my_books'))
#-----------------------------------------END-------------------------------------------------------------


#------------------------------------MY BOOKS---------------------------------------------------------------
@app.route('/my_books')
@auth_required
def my_books():
	user = User.query.get(session['user_id'])
	accesses = Access.query.filter_by(user_id=session['user_id']).all()

	if accesses:
		for access in accesses:
			if datetime.utcnow().date() > access.return_date:
				access.status = "returned"
		db.session.commit()

	return render_template('user/mybooks.html', user=user, accesses=accesses)
#-----------------------------------------END-----------------------------------------------------------------


#-----------------------------------READ BOOK-----------------------------------------------------------------------
@app.route('/my_books/<int:id>/read')
@auth_required
def read_book(id):
	user = User.query.get(session['user_id'])
	book = Book.query.get(id)
	
	return render_template('book/read.html', user=user, book=book)
#-----------------------------------------END------------------------------------------------------------------------


#---------------------------------RETURN BOOK------------------------------------------------------------------
@app.route('/my_books/<int:id>/return')
@auth_required
def return_book(id):
	access = Access.query.filter_by(id=id).first()
	access.status = "returned"
	db.session.commit()
	flash('Book returned successfully')
	return redirect(url_for('my_books'))
#----------------------------------------END-------------------------------------------------------------------


#------------------------------------------ADD TO CART-----------------------------------------------------------------
@app.route('/add_to_cart/<int:id>')
@auth_required
def add_to_cart(id):
    cart = Cart.query.filter_by(user_id=session['user_id'], book_id=id).first()

    if cart:
        flash('Book already exists in cart')
        return redirect(url_for('my_books'))
    else:
        cart = Cart(user_id=session['user_id'], book_id=id)
        db.session.add(cart)
    db.session.commit()

    flash('Book added to cart successfully')
    return redirect(url_for('my_books'))
#------------------------------------------END----------------------------------------------------------------------


#-----------------------------------------CART-----------------------------------------------------------------------
@app.route('/cart')
@auth_required
def cart():
	user = User.query.get(session['user_id'])
	
	carts = Cart.query.filter_by(user_id=session['user_id']).all()
	total = sum([cart.book.price for cart in carts])
	
	return render_template('user/cart.html', user=user, carts=carts, total=total)
#-----------------------------------------END------------------------------------------------------------------------


#--------------------------------------DELETE CART-------------------------------------------------------------------
@app.route('/cart/<int:id>/delete', methods=['POST'])
@auth_required
def delete_cart(id):
    cart = Cart.query.get(id)
    db.session.delete(cart)
    db.session.commit()
    flash('Cart deleted successfully')
    return redirect(url_for('cart'))
#--------------------------------------END----------------------------------------------------------------------------


#----------------------------------------CHECKOUT----------------------------------------------------------------------
@app.route('/checkout', methods=['POST'])
@auth_required
def checkout():
    carts = Cart.query.filter_by(user_id=session['user_id']).all()

    transaction = Transaction(user_id=session['user_id'], datetime=datetime.now())
    for cart in carts:
        order = Order(transaction=transaction, book=cart.book, price=cart.book.price)
        db.session.add(order)
        db.session.delete(cart)

    db.session.add(transaction)
    db.session.commit()

    flash('Order placed successfully')
    return redirect(url_for('orders'))
#------------------------------------------END-------------------------------------------------------------------------


#--------------------------------------------------ORDER---------------------------------------------------------------
@app.route('/orders')
@auth_required
def orders():
	user = User.query.get(session['user_id'])
	
	transactions = Transaction.query.filter_by(user_id=session['user_id']).order_by(Transaction.datetime.desc()).all()
	return render_template('user/orders.html', user=user, transactions=transactions)
#---------------------------------------------------END----------------------------------------------------------------


#-----------------------------------------FEEDBACK-----------------------------------------------------------------------
@app.route('/feedback/<int:id>')
@auth_required
def feedback(id):
	user = User.query.get(session['user_id'])
	book = Book.query.get(id)
	
	return render_template('user/feedback.html', user=user, book=book)

@app.route('/feedback/<int:id>', methods=['POST'])
@auth_required
def feedback_post(id):
	user = User.query.get(session['user_id'])
	book = Book.query.get(id)

	rating = int(request.form.get('rating'))
	content = request.form.get('content')

	feedback = Feedback.query.filter_by(user_id=user.id, book_id=id).first()
	if feedback:
		flash('You have already reviewed this book')
		return redirect(url_for('my_books'))

	if book.rating is None:
		book.rating = int(rating)
	else:
		book.rating = (book.rating + int(rating))/2

	feedback = Feedback(rating=rating, content=content, user=user, book=book)
	db.session.add(feedback)
	db.session.commit()

	flash('Your feedback is recoreded successfully')
	return redirect(url_for('my_books'))
#-----------------------------------------END------------------------------------------------------------------------


#---------------------------------------STATS----------------------------------------------------------
@app.route('/user/stats')
@auth_required
def user_stats():
	user = User.query.get(session['user_id'])

	accesses = Access.query.filter_by(user_id=user.id).order_by(Access.borror_date)

	borrow_dates, borrow_counts = [], []
	for access in accesses:
		if access.borror_date.strftime('%Y-%m-%d') not in borrow_dates:
			borrow_dates.append(access.borror_date.strftime('%Y-%m-%d'))
			borrow_counts.append(0)
		borrow_counts[-1] += 1
	
	return render_template('user/stats.html', user=user, borrow_dates=borrow_dates, borrow_counts=borrow_counts)
#------------------------------------END---------------------------------------------------------------