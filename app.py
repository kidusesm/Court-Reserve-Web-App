from flask import Flask, render_template

app = Flask(__name__)

@app.route("/") # / means default route
def home():
    return render_template("index.html") # render_template linked to index.html file
    

@app.route("/reservations")
def reservations():
    return render_template("reservations.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/profile")
def profile():
    return render_template("profile.html")

if __name__ == "__main__":
    app.run(debug=True)
