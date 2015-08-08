"""Prop Shop"""

from jinja2 import StrictUndefined

from flask import Flask, render_template, request, flash, redirect, session
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db, User, Property, UserProperty

#import subprocess

import usaddress

from collections import OrderedDict

app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails silently.
# This is horrible. Fix this so that, instead, it raises an error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""

    return render_template("homepage.html")


@app.route('/register', methods=['GET'])
def register_form():
    """Show form for user signup."""

    return render_template('registration-form.html')


@app.route('/register', methods=['POST'])
def register_process():
    """Process registration."""

    user_email = request.form['email']
    user = User.query.filter(User.email == user_email).first()
    print user, "**********************************************"

    if user is None:
        # Get form variables
        fname = request.form["fname"]
        lname = request.form["lname"]
        email = request.form["email"]
        password = request.form["password"]
        zipcode = request.form["zipcode"]

        new_user = User(fname=fname, lname=lname, email=email, password=password, zipcode=zipcode)

        db.session.add(new_user)
        db.session.commit()

        flash("User %s added." % email)
        return redirect("/")

    else:
        flash("This email has already been registered.\nPlease use a different email.") 
        return redirect("/register")


@app.route('/login', methods=['GET'])
def login_form():
    """Show login form."""

    return render_template("login-form.html")


@app.route('/login', methods=['POST'])
def login_process():
    """Process login."""

    # Get form variables
    email = request.form["email"]
    password = request.form["password"]

    user = User.query.filter_by(email=email).first()

    if not user:
        flash("No such user")
        return redirect("/login")

    if user.password != password:
        flash("Incorrect password")
        return redirect("/login")

    session["user_id"] = user.user_id

    flash("Hello, %s!" % user.fname)
    return redirect("/") #Change redirect path later


@app.route('/logout')
def logout():
    """Log out."""

    del session["user_id"]
    flash("Logged Out.")
    return redirect("/")


######################################################
@app.route('/search', methods=['GET'])
def parse_address_search():
    """Parses the address for API call"""
    raw_address_text = request.args.get("address_search")
    raw_address_parsed = usaddress.tag(raw_address_text)
    print raw_address_parsed,"*************************"
    print type(raw_address_parsed), "**************************"
    address_dict = dict(raw_address_parsed) #THE RETURNED OBJECT IS NOT AN ORDERED DICT BUT TUPLE. NEED TO FIX

    return render_template("address-confirmation.html", raw_address_text=raw_address_text)

# USE THIS TO CREATE THE MY PROFILE PAGE
# @app.route("/users/<int:user_id>")
# def user_detail(user_id):
#     """Show info about user."""

#     user = User.query.get(user_id)
#     return render_template("user.html", user=user)


@app.route("/property-table")
def get_propeties_list():
    """Show list of movies."""

    #movies = Movie.query.order_by('title').all()
    return render_template("property-table.html")



if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the point
    # that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run()