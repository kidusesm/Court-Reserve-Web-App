from flask import Flask, render_template, request
import psycopg2
import psycopg2.extras

app = Flask(__name__)

# --- Database connection helper ---
def get_db_connection():
    conn = psycopg2.connect(
        "postgresql://postgres:WebApps123@@db.favdctbtaoiisxjmlmcd.supabase.co:5432/postgres"
    )
    return conn


@app.route("/")  # default route
def home():
    return render_template("index.html")


@app.route("/reservations")
def reservations():
    # Connect to the database
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Query reservations joined with user, court, venue
    cur.execute("""
        select
            r.id,
            r.start_time,
            r.end_time,
            r.status,
            r.price_total,
            u.full_name,
            u.email,
            c.name  as court_name,
            v.name  as venue_name
        from reservations r
        join users   u on u.id = r.user_id
        join courts  c on c.id = r.court_id
        join venues  v on v.id = c.venue_id
        order by r.start_time;
    """)

    reservations = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("reservations.html", reservations=reservations)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/profile")
def profile():
    return render_template("profile.html")


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
