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
    props_in_cart = session.get('properties',[])
    print session, "*************************"

    # Our output cart will be a dictionary (so we can easily see if we
    # already have that melon type in there)

    properties = {}

    # Loop over the ZPIDs in the session cart and add each one to
    # the output cart

    for zpid in props_in_cart:

        # Get the existing property from our output cart, setting to an
        # empty dictionary if not there already
        house = properties.setdefault(zpid, {})
        house_data = Property.query.get(zpid) ####THIS QUERY IS NOT WORKING

        print house, "***************************************"
        print house_data, "***************************************"

        #TO DO: pass property from url this page
        if house_data is not None and house is {}:
            # Check this property hasn't already been searched in the session and display data
            house['street'] = house_data.street
            house['city'] = house_data.city
            house['state'] = house_data.state
            house['zipcode'] = house_data.zipcode
            house['bedrooms'] = house_data.bedrooms
            house['bathrooms'] = house_data.bathrooms
            house['z_amount'] = house_data.z_amount


    # Now, get a list of the all melons we've put into that dict
    #print type(properties), "***************************************"
    properties = properties.values()

    return render_template("property-table.html", properties=properties)



if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the point
    # that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run()