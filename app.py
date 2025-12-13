from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    render_template_string,
    jsonify,
)
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Needed for sessions (login state)
# Secret key from supabase is found in project settings -> API
app.secret_key = "[YOUR SECRET KEY - (can't leak mine in a public repo)]"  # Secret key

# --- Database connection helper ---
def get_db_connection():
    return psycopg2.connect(
        host="aws-1-us-east-1.pooler.supabase.com",
        port=6543,
        dbname="postgres",
        user="postgres.favdctbtaoiisxjmlmcd",
        password="webappspasswor",   # <-- put your actual DB password
        sslmode="require"
    )


    # postgresql://postgres:[YOUR_PASSWORD]@db.favdctbtaoiisxjmlmcd.supabase.co:5432/postgres
    return conn


@app.route("/")  # default route
def home():
    return render_template("index.html")


# ------------ AUTH ROUTES ------------

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        return render_template("signup.html", error="Email and password are required.")

    password_hash = generate_password_hash(password)

    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute(
            """
            INSERT INTO public.users (email, full_name, password_hash)
            VALUES (%s, %s, %s)
            RETURNING id;
            """,
            (email, full_name, password_hash),
        )

        user = cur.fetchone()
        conn.commit()

        # log in after successful DB write
        session["user_id"] = str(user["id"])
        session["user_name"] = full_name
        session["user_email"] = email

        return redirect(url_for("profile"))

    except psycopg2.errors.UniqueViolation:
        if conn:
            conn.rollback()
        return render_template("signup.html", error="That email is already registered. Try logging in.")

    except Exception as e:
        if conn:
            conn.rollback()
        print("❌ Signup error:", repr(e))
        return render_template("signup.html", error=f"Signup failed: {e}")

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        # For this project, we're not checking against a real DB.
        # Any email/password will "log in" a user.
        name_guess = email.split("@")[0].replace(".", " ").title() or "Guest"

        session["user_id"] = email
        session["user_name"] = name_guess
        session["user_email"] = email

        return redirect(url_for("profile"))

    # GET
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ------------ APP ROUTES ------------

@app.route("/reservations")
def reservations():
    reservations = []

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Try to load from the real database
        cur.execute(
            """
            SELECT
                r.id,
                r.start_time,
                r.end_time,
                r.status,
                r.price_total,
                'Demo User'       AS full_name,
                'demo@example.com' AS email,
                ('Court #' || r.court_id::text) AS court_name,
                'Sample Venue'    AS venue_name
            FROM reservations r
            ORDER BY r.start_time;
            """
        )

        reservations = cur.fetchall()
        print("Loaded reservations from DB:", len(reservations))

    except Exception as e:
        print("\n=== ERROR loading reservations from DB ===")
        print(e)
        print("=========================================\n")

    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass

    # If DB returned nothing, fall back to hard-coded sample data
    if not reservations:
        reservations = [
            {
                "id": 1,
                "full_name": "Demo User",
                "court_name": "Downtown Main Court",
                "venue_name": "Downtown Sports Center",
                "start_time": "2025-12-12 15:00",
                "end_time": "2025-12-12 16:00",
                "status": "confirmed",
                "price_total": 25.00,
            },
            {
                "id": 2,
                "full_name": "Demo User",
                "court_name": "East Side Court 1",
                "venue_name": "East Side Courts",
                "start_time": "2025-12-13 18:00",
                "end_time": "2025-12-13 19:00",
                "status": "pending",
                "price_total": 20.00,
            },
        ]

    return render_template("reservations.html", reservations=reservations)


@app.route("/reservations/<int:reservation_id>/edit", methods=["GET", "POST"])
def edit_reservation(reservation_id):
    # POST: update reservation
    if request.method == "POST":
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")
        status = request.form.get("status")
        price_total = request.form.get("price_total")

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute(
                """
                UPDATE reservations
                SET start_time = %s,
                    end_time = %s,
                    status = %s,
                    price_total = %s
                WHERE id = %s;
                """,
                (start_time, end_time, status, price_total, reservation_id),
            )
            conn.commit()

        except Exception as e:
            print("ERROR updating reservation:", e)

        finally:
            try:
                cur.close()
                conn.close()
            except Exception:
                pass

        return redirect(url_for("reservations"))

    # GET: load reservation and show edit form
    reservation = None

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("SELECT * FROM reservations WHERE id = %s;", (reservation_id,))
        reservation = cur.fetchone()

    except Exception as e:
        print("ERROR loading reservation for edit:", e)

    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass

    if not reservation:
        return redirect(url_for("reservations"))

    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
      <title>Edit Reservation • Court Reserve</title>
      <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
      <style>
        .edit-wrap { max-width: 720px; margin: 40px auto; padding: 0 16px; }
        .edit-card { background: #fff; border-radius: 14px; padding: 18px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); }
        label { display:block; margin-top: 12px; font-weight: 600; }
        input, select { width: 100%; padding: 10px; margin-top: 6px; border-radius: 10px; border: 1px solid #ddd; }
        .row { display:flex; gap: 12px; }
        .row > div { flex: 1; }
        .actions { margin-top: 16px; display:flex; gap: 10px; }
        .btnlike { display:inline-block; text-decoration:none; padding:10px 14px; border-radius:10px; background:#111; color:#fff; border:none; cursor:pointer; }
        .btnlike.secondary { background:#555; }
      </style>
    </head>
    <body>
      <header class="navbar">
        <div class="logo">Court Reserve</div>
        <nav>
          <ul>
            <li><a href="{{ url_for('home') }}">Home</a></li>
            <li><a href="{{ url_for('reservations') }}">Reservations</a></li>
            <li><a href="{{ url_for('about') }}">About</a></li>
            <li><a href="{{ url_for('profile') }}">Profile</a></li>
          </ul>
        </nav>
      </header>

      <div class="edit-wrap">
        <h1 style="margin-bottom:14px;">Edit Reservation #{{ r.id }}</h1>

        <div class="edit-card">
          <form method="POST">
            <div class="row">
              <div>
                <label>Start Time</label>
                <input name="start_time" value="{{ r.start_time }}" required />
              </div>
              <div>
                <label>End Time</label>
                <input name="end_time" value="{{ r.end_time }}" required />
              </div>
            </div>

            <label>Status</label>
            <select name="status" required>
              {% for s in ['pending','confirmed','canceled','completed'] %}
                <option value="{{ s }}" {% if r.status == s %}selected{% endif %}>{{ s }}</option>
              {% endfor %}
            </select>

            <label>Price Total</label>
            <input name="price_total" value="{{ r.price_total }}" required />

            <div class="actions">
              <button type="submit" class="btnlike">Save</button>
              <a class="btnlike secondary" href="{{ url_for('reservations') }}">Cancel</a>
            </div>
          </form>
        </div>
      </div>

      <footer>
        <p style="text-align:center; margin: 30px 0;">&copy; 2025 Court Reserve - Kidus Assefa. All rights reserved.</p>
      </footer>
    </body>
    </html>
    """
    return render_template_string(html, r=reservation)


@app.route("/reservations/<int:reservation_id>/delete", methods=["POST"])
def delete_reservation(reservation_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("DELETE FROM reservations WHERE id = %s;", (reservation_id,))
        conn.commit()

    except Exception as e:
        print("ERROR deleting reservation:", e)

    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass

    return redirect(url_for("reservations"))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/profile")
def profile():
    # template can use session["user_id"], etc.
    return render_template("profile.html")


@app.route("/availability")
@app.route("/availability")
def availability():
    conn = None
    cur = None
    venues = []

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT id, name, address, city, state, zip
            FROM public.venues
            ORDER BY id;
        """)
        venues = cur.fetchall()

    except Exception as e:
        # IMPORTANT: print the real error so you can fix the real cause
        print(" DB ERROR in /availability:", repr(e))
        venues = []  # show "No venues found" instead of fake sample data

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    return render_template("availability.html", venues=venues)

@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if request.method == "POST":
        name = request.form["name"]
        comment = request.form["comment"]
        return f"Thanks, {name}! Your feedback: '{comment}' was received."
    return '''
        <form method="post">
            Name: <input name="name"><br>
            Comment: <input name="comment"><br>
            <button type="submit">Submit</button>
        </form>
    '''


if __name__ == "__main__":
    app.run(debug=True)
