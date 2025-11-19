import resend
from flask import Flask, render_template, session, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

with app.app_context():
    db.create_all()

resend.api_key = "re_YGDPs2cA_KRxZ6e8dFs8qaFWDFtLHkbsz"

products = {
    '1': {'name': 'Solitaire Diamond Ring', 'price': 2500, 'image': 'images/img1.avif'},
    '2': {'name': 'Princess Cut Necklace', 'price': 5000, 'image': 'images/bn1.webp'},
    '3': {'name': 'Diamond Stud Earrings', 'price': 1800, 'image': 'images/e1.webp'},
    '4': {'name': 'Tennis Bracelet', 'price': 7500, 'image': 'images/b1.jpg'},
    '5': {'name': 'Halo Engagement Ring', 'price': 3200, 'image': 'images/img2.avif'},
    '6': {'name': 'Pendant Necklace', 'price': 4200, 'image': 'images/bn2.jpg'},
    '7': {'name': 'Hoop Earrings', 'price': 2100, 'image': 'images/e1.webp'},
    '8': {'name': 'Bangle Bracelet', 'price': 6300, 'image': 'images/b2.jpg'},
    '9': {'name': 'Vintage Style Ring', 'price': 2800, 'image': 'images/img3.jpg'},
    '10': {'name': 'Choker Necklace', 'price': 4800, 'image': 'images/bn3.jpg'},
}

@app.route('/')
def home():
    return render_template('index.html', products=products)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        params = {
            "from": "onboarding@resend.dev",
            "to": "iqbalaqsa955@gmail.com",
            "subject": "New Contact Form Submission",
            "html": f"<strong>Name:</strong> {name}<br><strong>Email:</strong> {email}<br><strong>Message:</strong> {message}",
        }

        email = resend.Emails.send(params)
        print(email)

        return redirect(url_for('contact_thank_you'))
    return render_template('contact.html')

@app.route('/contact_thank_you')
def contact_thank_you():
    return render_template('contact_thank_you.html')

@app.route('/add_to_cart/<product_id>')
@login_required
def add_to_cart(product_id):
    if 'cart' not in session:
        session['cart'] = {}
    
    cart = session['cart']
    cart[product_id] = cart.get(product_id, 0) + 1
    session.modified = True
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    cart_products = {}
    total_price = 0
    if 'cart' in session:
        for product_id, quantity in session['cart'].items():
            product = products.get(product_id)
            if product:
                cart_products[product_id] = {
                    'name': product['name'],
                    'price': product['price'],
                    'quantity': quantity,
                    'image': product['image']
                }
                total_price += product['price'] * quantity
    return render_template('cart.html', cart_products=cart_products, total_price=total_price)

@app.route('/remove_from_cart/<product_id>')
def remove_from_cart(product_id):
    if 'cart' in session and product_id in session['cart']:
        del session['cart'][product_id]
        session.modified = True
    return redirect(url_for('cart'))

@app.route('/update_cart/<product_id>', methods=['POST'])
def update_cart(product_id):
    if 'cart' in session and product_id in session['cart']:
        cart = session['cart']
        action = request.form.get('action')
        if action == 'increase':
            cart[product_id] += 1
        elif action == 'decrease':
            if cart[product_id] > 1:
                cart[product_id] -= 1
            else:
                del cart[product_id]
        session.modified = True
    return redirect(url_for('cart'))

@app.route('/checkout')
def checkout():
    return render_template('checkout.html')

@app.route('/process_payment', methods=['POST'])
def process_payment():
    # In a real application, you would process the payment here.
    # For this demo, we'll just clear the cart.
    session.pop('cart', None)
    return redirect(url_for('thank_you'))

@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        if user:
            flash('That username is already taken. Please choose a different one.', 'danger')
            return redirect(url_for('signup'))
        hashed_password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print(f"Attempting to log in with username: {username}")
        user = User.query.filter_by(username=username).first()
        print(f"User found in database: {user}")
        if user:
            password_match = bcrypt.check_password_hash(user.password, password)
            print(f"Password match result: {password_match}")
            if password_match:
                login_user(user, remember=True)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('home'))
    
        flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
