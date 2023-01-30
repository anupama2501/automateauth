from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def homepage():
  return render_template("index.html")


@app.route("/ldap", methods=["GET"])
def ldap_route():
  return render_template("ldap.html")

@app.route("/rancherform",  methods=["GET"])
def rancherform():
  return render_template("rancher_form.html")

if __name__ == "__main__":
  app.run()
