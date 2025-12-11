from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
)
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Needed for sessions (login state)
app.secret_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhdmRjdGJ0YW9paXN4am1sbWNkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM0OTY2NTMsImV4cCI6MjA3OTA3MjY1M30.H4DAW7NogBI8V0Y79Qjn4e-TurihgvHZ7SnD0GnwnzE"  # Secret key

# --- Database connection helper ---
def get_db_connection():
    conn = psycopg2.connect(
        "postgresql://postgres:WebApps123%40@db.favdctbtaoiisxjmlmcd.supabase.co:5432/postgres"
    )
    return conn


@app.route("/")  # default route
def home():
    return render_template("index.html")


# ------------ AUTH ROUTES ------------

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        full_name = request.form["full_name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        # hash for DB storage
        password_hash = generate_password_hash(password)

        # 1) ALWAYS log them in via session (works even if DB is down)
        session["user_id"] = email
        session["user_name"] = full_name
        session["user_email"] = email

        # 2) TRY to save them in the database, but don't crash if it fails
        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            cur.execute(
                """
                INSERT INTO users (email, full_name, password_hash)
                VALUES (%s, %s, %s);
                """,
                (full_name, email, password_hash),
            )

            conn.commit()
            print("Saved user to DB:", email)

        except Exception as e:
            print("WARNING: could not save user to DB:", e)

        finally:
            try:
                cur.close()
                conn.close()
            except Exception:
                pass

        return redirect(url_for("profile"))

    # GET
    return render_template("signup.html")


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
                "full_name": "Demo User",
                "court_name": "Downtown Main Court",
                "venue_name": "Downtown Sports Center",
                "start_time": "2025-12-12 15:00",
                "end_time": "2025-12-12 16:00",
                "status": "confirmed",
                "price_total": 25.00,
            },
            {
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


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/profile")
def profile():
    # template can use session["user_id"], etc.
    return render_template("profile.html")


@app.route("/availability")
def availability():
    venues = []

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute(
            """
            SELECT id, name, address, city, state, zip
            FROM venues
            ORDER BY name;
            """
        )
        venues = cur.fetchall()

    except Exception as e:
        print("Error loading venues:", e)

    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass

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
