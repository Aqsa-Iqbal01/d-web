import os
import resend
from flask import Flask, render_template, session, redirect, url_for, request

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'

resend.api_key = os.environ.get('RESEND_API_KEY')

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

if __name__ == '__main__':
    app.run(debug=True)