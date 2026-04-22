from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'wts_solutions_2026_pro_deploy'

# --- RENDER PERSISTENT STORAGE LOGIC ---
if os.path.exists('/data'):
    db_path = '/data/wts_erp.db'
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'wts_erp.db')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# --- DATABASE MODELS ---
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    barcode = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    stock = db.Column(db.Integer, default=0)
    min_limit = db.Column(db.Integer, default=5)
    acquisition_type = db.Column(db.String(20))  # Bought or Donated
    source_name = db.Column(db.String(100))  # Supplier or Donor
    cost_price = db.Column(db.Float, default=0.0)
    date_added = db.Column(db.DateTime, default=datetime.now)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100))
    dept = db.Column(db.String(100))
    trans_type = db.Column(db.String(20))  # IN or OUT
    qty = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.now)


with app.app_context():
    db.create_all()


# --- ROUTES ---
@app.route('/')
def login():
    return render_template('login.html')


@app.route('/auth', methods=['POST'])
def auth():
    username = request.form.get('username')
    password = request.form.get('password')
    if username == 'admin' and password == 'password123':
        session['user'] = 'Administrator'
        return redirect(url_for('dashboard'))
    flash('Invalid Credentials', 'error')
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('login'))
    inventory = Product.query.all()
    alerts = Product.query.filter(Product.stock <= Product.min_limit).all()
    logs = Transaction.query.order_by(Transaction.timestamp.desc()).limit(8).all()
    return render_template('dashboard.html', inventory=inventory, alerts=alerts,
                           low_stock_count=len(alerts), total_items=len(inventory), transactions=logs)


@app.route('/dispatch')
def dispatch_page():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('dispatch.html')


@app.route('/api/products')
def get_products():
    products = Product.query.all()
    return jsonify([{"id": p.id, "name": p.name, "barcode": p.barcode} for p in products])


@app.route('/register_product', methods=['POST'])
def register_product():
    barcode = request.form.get('barcode')
    if Product.query.filter_by(barcode=barcode).first():
        flash(f"Error: Barcode {barcode} already exists.", "error")
        return redirect(url_for('dashboard'))

    new_p = Product(
        barcode=barcode,
        name=request.form.get('name'),
        stock=int(request.form.get('stock') or 0),
        min_limit=int(request.form.get('min_limit') or 5),
        acquisition_type=request.form.get('acquisition_type'),
        source_name=request.form.get('source_name'),
        cost_price=float(request.form.get('cost_price') or 0.0)
    )
    db.session.add(new_p)
    db.session.commit()
    flash("Product Registered Successfully!", "success")
    return redirect(url_for('dashboard'))


@app.route('/update_stock', methods=['POST'])
def update_stock():
    product = Product.query.get(int(request.form.get('item_id')))
    trans_type = request.form.get('type')
    qty = int(request.form.get('qty'))
    dept = request.form.get('dept')

    if trans_type == 'out':
        if product.stock < qty:
            flash(f"Insufficient stock for {product.name}", "error")
            return redirect(url_for('dashboard'))
        product.stock -= qty
    else:
        product.stock += qty

    log = Transaction(item_name=product.name, dept=dept, trans_type=trans_type.upper(), qty=qty)
    db.session.add(log)
    db.session.commit()
    flash("Stock Update Complete!", "success")
    return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)