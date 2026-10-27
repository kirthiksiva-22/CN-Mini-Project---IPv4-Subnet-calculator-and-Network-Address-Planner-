from flask import Flask, render_template, request
import subnet

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    ctx = {"calc": None, "plan": None, "free": None, "error": None, "form": request.form}
    if request.method == "POST":
        try:
            if request.form.get("action") == "calc":
                ctx["calc"] = subnet.calculate(request.form["ip"], request.form["prefix"])
            else:
                reqs = subnet.parse_requirements(request.form["reqs"])
                ctx["plan"], ctx["free"] = subnet.plan(request.form["parent"], reqs)
        except ValueError as e:
            ctx["error"] = str(e)
    return render_template("index.html", **ctx)


if __name__ == "__main__":
    app.run(debug=True)
