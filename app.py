from flask import Flask, render_template, request, redirect, url_for, jsonify
import os, json, uuid, stripe

app = Flask(__name__)
app.secret_key = "dev-key"   # change for production

# Stripe test keys (replace with your own from dashboard)
stripe.api_key = "sk_test_xxxxx"    # SECRET KEY
PUBLISHABLE_KEY = "pk_test_xxxxx"   # PUBLISHABLE KEY
DOMAIN = "http://127.0.0.1:5000"    # local domain

DATA_FILE = "data.json"

# ---------------- Data Helpers ----------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"artisans": [], "products": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ---------------- Routes ----------------
@app.route("/")
def index():
    data = load_data()
    return render_template("index.html", artisans=data["artisans"], products=data["products"])

@app.route("/register", methods=["POST"])
def register():
    data = load_data()
    artisan = {"id": str(uuid.uuid4()), "name": request.form["name"]}
    data["artisans"].append(artisan)
    save_data(data)
    return redirect(url_for("index"))

@app.route("/artisan/<aid>")
def artisan(aid):
    data = load_data()
    artisan = next((a for a in data["artisans"] if a["id"] == aid), None)
    products = [p for p in data["products"] if p["artisan_id"] == aid]
    return render_template("artisan.html", artisan=artisan, products=products)

@app.route("/add/<aid>", methods=["POST"])
def add(aid):
    data = load_data()
    product = {
        "id": str(uuid.uuid4()),
        "title": request.form["title"],
        "desc": request.form["desc"],
        "price": float(request.form["price"]),
        "artisan_id": aid,
    }
    data["products"].append(product)
    save_data(data)
    return redirect(url_for("artisan", aid=aid))

@app.route("/product/<pid>")
def product(pid):
    data = load_data()
    p = next((x for x in data["products"] if x["id"] == pid), None)
    return render_template("product.html", p=p, publishable=PUBLISHABLE_KEY)

# -------- Stripe Checkout --------
@app.route("/create-checkout-session/<pid>", methods=["POST"])
def create_checkout_session(pid):
    data = load_data()
    p = next((x for x in data["products"] if x["id"] == pid), None)
    if not p:
        return jsonify({"error": "not found"}), 404

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "inr",
                "product_data": {"name": p["title"]},
                "unit_amount": int(p["price"] * 100),
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=DOMAIN + "/success",
        cancel_url=DOMAIN + f"/product/{pid}",
    )
    return jsonify({"url": session.url})

@app.route("/success")
def success():
    return render_template("success.html")

if __name__ == "__main__":
    app.run(debug=True)
