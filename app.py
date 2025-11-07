from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")  # default route
def home():
    return render_template("index.html")

@app.route("/reservations")
def reservations():
    reservations = [ # Fake data for demonstration
        {"name": "Kidus", "court": "A", "time": "10:00 AM"},
        {"name": "Sara", "court": "B", "time": "11:00 AM"},
        {"name": "Mike", "court": "C", "time": "12:00 PM"}
    ]
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
