from flask import Flask, render_template, request, redirect, render_template_string, url_for, send_from_directory, jsonify
import flask.json
from sqlalchemy import create_engine, MetaData
from flask.ext.login import UserMixin, LoginManager, login_user, logout_user
from flask.ext.blogging import SQLAStorage, BloggingEngine
import pandas as pd
import geojson

print 'starting...'
app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"  # for WTF-forms and login
app.config["BLOGGING_SITENAME"] = "NY Taxi"
app.config["BLOGGING_URL_PREFIX"] = "/blog"
app.config["BLOGGING_SITEURL"] = "http://localhost:8000"
#app.config["BLOGGING_GOOGLE_ANALYTICS"] = ""

# extensions
engine = create_engine('sqlite:///blog.db')
meta = MetaData()
sql_storage = SQLAStorage(engine, metadata=meta)
blog_engine = BloggingEngine(app, sql_storage)
login_manager = LoginManager(app)
meta.create_all(bind=engine)

# static variables
"""
fields in taxi_df
=================
medallion
hack_license
vendor_id
rate_code
store_and_fwd_flag
pickup_datetime
dropoff_datetime
passenger_count
trip_time_in_secs
trip_distance
pickup_longitude
pickup_latitude
dropoff_longitude
dropoff_latitude
fare_amount
surcharge
mta_tax
tip_amount
tolls_amount
total_amount
"""
appdata={}
appdata['taxi_df'] = pd.read_csv('data/nytaxi2013_sample_clean.csv', index_col=None, parse_dates=['pickup_datetime', 'dropoff_datetime'], date_parser = (lambda x: pd.datetime.strptime(x, '%Y-%m-%d %H:%M:%S'))) 
#DEBUG
#sliced to [:1000] to reduce load time
appdata['pickup_location']= geojson.MultiPoint([(x,y) for x,y in zip(appdata['taxi_df']['pickup_longitude'][:1000], appdata['taxi_df']['pickup_latitude'][:1000])])
appdata['dropoff_location']= geojson.MultiPoint([(x,y) for x,y in zip(appdata['taxi_df']['dropoff_longitude'][:1000], appdata['taxi_df']['dropoff_latitude'][:1000])])

print 'appdata loaded...'

# user class for providing authentication
class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

    def get_name(self):
        return "Jacky Ma"  # typically the user's name

@login_manager.user_loader
@blog_engine.user_loader
def load_user(user_id):
    return User(user_id)

blog_index_template = """
<!DOCTYPE html>
<html>
    <head> </head>
    <body>
        {% if current_user.is_authenticated() %}
            <a href="/logout/">Logout</a>
        {% else %}
            <a href="/login/">Login</a>
        {% endif %}
        &nbsp&nbsp<a href="/blog/">Blog</a>
        &nbsp&nbsp<a href="/blog/sitemap.xml">Sitemap</a>
        &nbsp&nbsp<a href="/blog/feeds/all.atom.xml">ATOM</a>
    </body>
</html>
"""
@app.route("/blogmeta")
def blogmeta():
    return render_template_string(blog_index_template)
    
@app.route("/login/")
def login():
    user = User("testuser")
    login_user(user)
    return redirect("/blog")

@app.route("/logout/")
def logout():
    logout_user()
    return redirect("/")

@app.route('/blogfile/<filename>')
def blogfile(filename):
    # show the user profile for that user
    return send_from_directory('static/blogfiles', filename, as_attachment=True)
    


#Regular Navigations
@app.route("/")
def index():
    return redirect("/nytaxi")

@app.route("/nytaxi/")
def nytaxi_page():
    return render_template('nytaxi.html')
            
@app.route("/blogpage/")
def blog_page():
    return redirect("/blog")

@app.route("/references/")
def references_page():
    return render_template('references.html')
    
@app.route("/about/")
def about_page():
    return render_template('about.html')

@app.route("/loaddata", methods=["GET", "POST"])
def load_taxi_data():
	print 'AJAX load data'
	return geojson.dumps(appdata['pickup_location'])


if __name__ == "__main__":
    app.run(debug=True, port=8000, use_reloader=True)


