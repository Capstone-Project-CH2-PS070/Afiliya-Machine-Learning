from flask import Flask, request, render_template, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)


# Fungsi untuk membuat dan menginisialisasi tabel pelacakan afiliasi
def create_affiliate_tracking_table():
    conn = sqlite3.connect("affiliate_tracking.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS affiliate_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            affiliate_id TEXT,
            user_id TEXT,
            action_type TEXT,
            product_id TEXT,
            order_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    conn.commit()
    conn.close()


# Fungsi untuk membuat dan menginisialisasi tabel pengguna
def create_users_table():
    conn = sqlite3.connect("affiliate_tracking.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            affiliate_id TEXT
        )
    """
    )
    conn.commit()
    conn.close()


# Fungsi untuk membuat dan menginisialisasi tabel komisi
def create_commissions_table():
    conn = sqlite3.connect("affiliate_tracking.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS commissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            affiliate_id TEXT,
            commission_amount REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    conn.commit()
    conn.close()


# Fungsi untuk melacak klik pada tautan afiliasi
def track_click(affiliate_id, product_id):
    conn = sqlite3.connect("affiliate_tracking.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO affiliate_tracking (affiliate_id, action_type, product_id)
        VALUES (?, 'click', ?)
    """,
        (affiliate_id, product_id),
    )
    conn.commit()
    conn.close()


# Fungsi untuk melacak tindakan pengguna
def track_user_action(affiliate_id, user_id, action_type, product_id):
    conn = sqlite3.connect("affiliate_tracking.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO affiliate_tracking (affiliate_id, user_id, action_type, product_id)
        VALUES (?, ?, ?, ?)
    """,
        (affiliate_id, user_id, action_type, product_id),
    )
    conn.commit()
    conn.close()


# Fungsi untuk melacak penjualan melalui tautan afiliasi dan menghitung komisi
def track_sale(affiliate_id, user_id, product_id, order_id, commission_rate):
    conn = sqlite3.connect("affiliate_tracking.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO affiliate_tracking (affiliate_id, user_id, action_type, product_id, order_id)
        VALUES (?, ?, 'sale', ?, ?)
    """,
        (affiliate_id, user_id, product_id, order_id),
    )

    # Hitung komisi dan masukkan ke dalam tabel komisi
    commission_amount = (
        commission_rate * 100
    )  # Misalnya, komisi adalah 10% dari penjualan
    cursor.execute(
        """
        INSERT INTO commissions (affiliate_id, commission_amount)
        VALUES (?, ?)
    """,
        (affiliate_id, commission_amount),
    )

    conn.commit()
    conn.close()


# Fungsi untuk mendapatkan total komisi untuk seorang afiliasi
def get_total_commission(affiliate_id):
    conn = sqlite3.connect("affiliate_tracking.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT SUM(commission_amount) FROM commissions WHERE affiliate_id = ?
    """,
        (affiliate_id,),
    )
    total_commission = cursor.fetchone()[0]
    conn.close()
    return total_commission


# Fungsi untuk mendaftar pengguna baru
def register_user(username, password, affiliate_id):
    conn = sqlite3.connect("affiliate_tracking.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO users (username, password, affiliate_id)
        VALUES (?, ?, ?)
    """,
        (username, password, affiliate_id),
    )
    conn.commit()
    conn.close()


# Fungsi untuk otentikasi pengguna
def authenticate_user(username, password):
    conn = sqlite3.connect("affiliate_tracking.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT affiliate_id FROM users WHERE username = ? AND password = ?
    """,
        (username, password),
    )
    affiliate_id = cursor.fetchone()
    conn.close()
    return affiliate_id[0] if affiliate_id else None


# Fungsi untuk membuat link afiliasi dari produk
def generate_affiliate_link(product_id, affiliate_id):
    base_url = "https://example.com/product"

    # Membangun URL dengan menambahkan parameter afiliasi
    affiliate_link = f"{base_url}/{product_id}?affiliate_id={affiliate_id}"

    return affiliate_link


# Route untuk halaman utama
@app.route("/")
def index():
    return render_template("index.html")


# Route untuk halaman pendaftaran pengguna
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        affiliate_id = request.form["affiliate_id"]
        register_user(username, password, affiliate_id)
        return redirect(url_for("login"))
    return render_template("register.html")


# Route untuk halaman login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        affiliate_id = authenticate_user(username, password)
        if affiliate_id:
            return redirect(url_for("dashboard", affiliate_id=affiliate_id))
        else:
            return render_template("login.html", error="Invalid username or password")
    return render_template("login.html", error=None)


# Route untuk dashboard afiliasi
@app.route("/dashboard/<affiliate_id>")
def dashboard(affiliate_id):
    total_commission = get_total_commission(affiliate_id)
    return render_template(
        "dashboard.html", affiliate_id=affiliate_id, total_commission=total_commission
    )


# Route untuk melacak klik
@app.route("/track_click/<affiliate_id>/<product_id>")
def track_click_route(affiliate_id, product_id):
    track_click(affiliate_id, product_id)
    return redirect(url_for("index"))


# Route untuk melacak tindakan pengguna
@app.route("/track_action/<affiliate_id>/<user_id>/<action_type>/<product_id>")
def track_action_route(affiliate_id, user_id, action_type, product_id):
    track_user_action(affiliate_id, user_id, action_type, product_id)
    return redirect(url_for("index"))


# Route untuk melacak penjualan
@app.route(
    "/track_sale/<affiliate_id>/<user_id>/<product_id>/<order_id>/<commission_rate>"
)
def track_sale_route(affiliate_id, user_id, product_id, order_id, commission_rate):
    commission_rate = float(commission_rate)
    track_sale(affiliate_id, user_id, product_id, order_id, commission_rate)
    return redirect(url_for("index"))


# Route untuk halaman pembuatan link afiliasi
@app.route("/generate_affiliate_link", methods=["GET", "POST"])
def generate_affiliate_link_page():
    if request.method == "POST":
        product_id = request.form["product_id"]
        affiliate_id = request.form["affiliate_id"]
        affiliate_link = generate_affiliate_link(product_id, affiliate_id)
        return render_template(
            "generate_affiliate_link_result.html", affiliate_link=affiliate_link
        )
    return render_template("generate_affiliate_link.html")


# Menjalankan aplikasi Flask
if __name__ == "__main__":
    create_affiliate_tracking_table()
    create_users_table()
    create_commissions_table()
    app.run(debug=True)
