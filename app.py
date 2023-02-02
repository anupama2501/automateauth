from flask import Flask, render_template, request, jsonify
import os
import requests
import httplib2
import urllib
import json
import subprocess
import urllib3

app = Flask(__name__, template_folder='templates', static_folder='staticFiles')
global AUTH
AUTHENTICATE_PAGE = "{RANCHER_URL}/v3/{Auth}/{Auth_lower}"

@app.route("/")
def homepage():
    return render_template("index.html")


@app.route("/ldap", methods=["GET"])
def ldap_route():
    return render_template("ldap.html")

@app.route("/saml", methods=["GET"])
def saml_route():
    return render_template("saml.html")

@app.route("/oauth", methods=["GET"])
def oauth_route():
    return render_template("oauth.html")


@app.route("/rancherform",  methods=["GET"])
def rancherform():
    global AUTH
    AUTH = request.args['authprovider']
    if AUTH == "activeDirectory":
        return "We are sorry, AD server is currently not working."
    return render_template("rancher_form.html", value=AUTH)


@app.route("/authenticate", methods=["GET", "POST"])
def authenticate_provider():
  if request.method == "POST":
    rancher_url = request.form.get("url")
    print(rancher_url)
    access_token = request.form.get("accesskey")
    secret_token = request.form.get("secretkey")

    auth_setup_data = \
    os.path.join(os.path.dirname(os.path.realpath(__file__)) + "/resource",
                 AUTH.lower() + ".json")
    auth_setup_file = open(auth_setup_data)
    auth_setup_str = auth_setup_file.read()
    auth_setup_data = json.loads(auth_setup_str)
    cattle_auth_url = AUTHENTICATE_PAGE.format(RANCHER_URL=rancher_url, Auth=AUTH+"Configs", Auth_lower=AUTH.lower())

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    params = (
        ('action', 'testAndApply'),
    )

    response = connect_to_rancher(cattle_auth_url, headers, auth_setup_data, access_token, secret_token, params)

    if response.status_code == 200:
        return "Successfully enabled auth"
    else:
        return "Auth was not enabled due to the reason: " + response.reason


def connect_to_rancher(url, headers, data, access_key, secret_key, params):

    response = requests.post(url, headers=headers, params=params,
                             json=data, verify=False,
                             auth=(access_key, secret_key))
    return response


if __name__ == "__main__":
  app.run()
