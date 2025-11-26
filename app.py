from dotenv import load_dotenv
import os
import resend
from flask import Flask, render_template, session, redirect, url_for, request, jsonify

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'

load_dotenv()

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

@app.context_processor
def inject_cart_count():
    return dict(cart_count=len(session.get('cart', {})))

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
            "from": "daimond website owner <onboarding@resend.dev>",
            "to": "iqbalaqsa955@gmail.com",
            "subject": "New Contact Form Submission",
            "html": f"<strong>Name:</strong> {name}<br><strong>Email:</strong> {email}<br><strong>Message:</strong> {message}",
        }

        try:
            email = resend.Emails.send(params)
            print(email)
        except resend.exceptions.ResendError as e:
            print("Failed to send email. Please check your Resend API key and that the 'from' email address is a verified domain in your Resend account.")
            print(f"Error: {e}")
            raise

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

@app.route('/add_to_cart_ajax/<product_id>')
def add_to_cart_ajax(product_id):
    if 'cart' not in session:
        session['cart'] = {}
    
    cart = session['cart']
    cart[product_id] = cart.get(product_id, 0) + 1
    session.modified = True
    return jsonify(success=True, message="Item added to cart successfully", cart_count=len(cart))

@app.route('/cart/count')
def cart_count():
    return jsonify(cart_count=len(session.get('cart', {})))

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

@app.route('/remove_from_cart_ajax/<product_id>')
def remove_from_cart_ajax(product_id):
    if 'cart' in session and product_id in session['cart']:
        del session['cart'][product_id]
        session.modified = True
        total_price = sum(products[pid]['price'] * qty for pid, qty in session['cart'].items())
        return jsonify(success=True, total_price=total_price, cart_count=len(session['cart']))
    return jsonify(success=False, message="Item not in cart")

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

@app.route('/update_cart_ajax/<product_id>', methods=['POST'])
def update_cart_ajax(product_id):
    if 'cart' in session and product_id in session['cart']:
        cart = session['cart']
        action = request.json.get('action')
        if action == 'increase':
            cart[product_id] += 1
        elif action == 'decrease':
            if cart[product_id] > 1:
                cart[product_id] -= 1
            else:
                del cart[product_id]
        session.modified = True

        if product_id in cart:
            item_total = products[product_id]['price'] * cart[product_id]
            quantity = cart[product_id]
        else:
            item_total = 0
            quantity = 0

        total_price = sum(products[pid]['price'] * qty for pid, qty in cart.items())

        return jsonify(
            success=True,
            quantity=quantity,
            item_total=item_total,
            total_price=total_price,
            cart_count=len(cart)
        )
    return jsonify(success=False, message="Item not in cart")

@app.route('/checkout')
def checkout():
    return render_template('checkout.html')

@app.route('/process_payment', methods=['POST'])
def process_payment():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']

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
        
        html_body = f"<h1>New Order</h1><p><strong>Name:</strong> {name}</p><p><strong>Email:</strong> {email}</p><h2>Order Details</h2><ul>"
        for _, item in cart_products.items():
            html_body += f"<li>{item['name']} (x{item['quantity']}) - ${item['price'] * item['quantity']:.2f}</li>"
        html_body += f"</ul><p><strong>Total:</strong> ${total_price:.2f}</p>"

        params = {
            "from": "daimond website owner <onboarding@resend.dev>",
            "to": "iqbalaqsa955@gmail.com",
            "subject": "New Order Received",
            "html": html_body,
        }

        try:
            email_sent = resend.Emails.send(params)
            print(email_sent)
        except resend.exceptions.ResendError as e:
            print("Failed to send order confirmation email.")
            print(f"Error: {e}")
            # Do not raise the exception here to not block the user from seeing the thank you page.
            
    # In a real application, you would process the payment here.
    # For this demo, we'll just clear the cart.
    session.pop('cart', None)
    return redirect(url_for('thank_you'))

@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

if __name__ == '__main__':
    app.run(debug=True)