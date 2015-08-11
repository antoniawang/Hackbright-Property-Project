"""Prop Shop"""

from jinja2 import StrictUndefined

from flask import Flask, render_template, request, flash, redirect, session
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db, User, Property, UserProperty

import model

from datetime import datetime

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

    if session['properties']:
        del session['properties']

    flash("Logged Out.")
    return redirect("/")


######################################################
@app.route('/search', methods=['GET'])
def parse_address_search():
    """Parses the address for API call"""
    if request.args:
        raw_address_text = request.args.get("address_search")
    raw_address_parsed = usaddress.tag(raw_address_text)
    address_ordered_dict = raw_address_parsed[0]
    
    address_keys = ['AddressNumber','StreetName','StreetNamePostType','OccupancyType','OccupancyIdentifier']
    address_string_list=[]
    for key in address_keys:
        if address_ordered_dict.get(key) is not None:
            address_string_list.append(address_ordered_dict[key])
    address_string = ' '.join(address_string_list)
    address_url_encode = address_string.replace(' ','+').strip()

    
    citystatezip_string = address_ordered_dict.get('PlaceName','')
    citystatezip_string += '%2C ' + address_ordered_dict.get('StateName','')
    citystatezip_string += ' ' + address_ordered_dict.get('ZipCode','')
    citystatezip_url_encode = citystatezip_string.strip().replace(' ','+')

    property_from_url = Property.generate_from_address(address=address_url_encode,
                        citystatezip=citystatezip_url_encode)

    #instantiate a session
    if 'properties' not in session.keys():
        session['properties'] = []

    if property_from_url.zpid not in session['properties']:
        session['properties'].append(property_from_url.zpid)
    
    this_property = Property.query.filter(Property.zpid == property_from_url.zpid).first()

    if this_property is None:
        db.session.add(property_from_url)
        db.session.commit()
    else:
        this_property = property_from_url      


    return render_template("address-confirmation.html", raw_address_text=str(property_from_url))

# USE THIS TO CREATE THE MY PROFILE PAGE
# @app.route("/users/<int:user_id>")
# def user_detail(user_id):
#     """Show info about user."""

#     user = User.query.get(user_id)
#     return render_template("user.html", user=user)


@app.route("/property-table")
def get_propeties_list():
    """Show list of properties stored in the session."""

    #Get the properties stored in session or create an empty session
    props_in_cart = set(session.get('properties',[]))
    print props_in_cart, "*************************"

    # Our output cart will be a dictionary (so we can easily see if we
    # already have the property in there)

    properties = []

    # Loop over the ZPIDs in the session cart and add each one to
    # the output cart

    for zpid in props_in_cart:
        house_data = Property.query.get(zpid)
        if house_data is not None:
            properties.append(house_data)
        # else:
        #     pass # what can you do if it's not found?

    print properties, "********************************"
    return render_template("property-table.html", properties=properties)


@app.route('/search-form', methods=['GET'])
def search_form():
    """Show search form"""

    return render_template("search-form.html")


@app.route('/search-from-form', methods=['GET'])
def search_from_form():
    """Process search from the search form"""
    street = request.args.get('street') 
    unit = request.args.get('unit') 
    city = request.args.get('city')
    state = request.args.get('state')
    zipcode = request.args.get('zipcode')

    raw_address_text = street + " " + unit + " " + city + " " + state + " " + zipcode

    return redirect("/search", raw_address_text=raw_address_text)


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the point
    # that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run()