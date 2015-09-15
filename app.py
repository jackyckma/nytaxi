from flask import Flask, flash, render_template, request, redirect, render_template_string, url_for, send_from_directory, jsonify
import flask.json
from sqlalchemy import create_engine, MetaData
from flask.ext.login import UserMixin, LoginManager, login_user, logout_user
from flask.ext.blogging import SQLAStorage, BloggingEngine
import pandas as pd
import geojson
from geoalchemy2 import Geometry
import os
import settings

##initializing the server
print 'Initializing',

#Set environment variable nytaxi_config to change the config
nytaxi_config=os.getenv('nytaxi_config', 'DEBUG')
print '[MODE={0}]...'.format(nytaxi_config),

app = Flask(__name__)
if nytaxi_config == 'DEBUG':
    app.config.from_object(settings.DevelopmentConfig)
elif nytaxi_config == 'OD_DEBUG':
	app.config.from_object(settings.OD_DevelopmentConfig)
elif nytaxi_config == 'TEST':
    app.config.from_object(settings.TestingConfig)
else:
    app.config.from_object(settings.ProductionConfig)
    
# extensions
engine = create_engine(app.config['DATABASE_URI']) 
meta = MetaData()
sql_storage = SQLAStorage(engine, metadata=meta)
blog_engine = BloggingEngine(app, sql_storage)
login_manager = LoginManager(app)
meta.create_all(bind=engine)

print 'ok'


# data fields
'''
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
'''

#Load Data
appdata={}
print 'Loading from database...',
appdata['taxi_df'] = pd.read_sql_query('SELECT * FROM tripdata LIMIT ' + app.config['SAMPLESIZE'], engine)
print 'ok'

#create geojson Multipoint
print 'Creating geometry objects...',
appdata['pickup_location']= geojson.MultiPoint([(x,y) for x,y in zip(appdata['taxi_df']['pickup_longitude'], appdata['taxi_df']['pickup_latitude'])])
appdata['dropoff_location']= geojson.MultiPoint([(x,y) for x,y in zip(appdata['taxi_df']['dropoff_longitude'], appdata['taxi_df']['dropoff_latitude'])])
print 'ok'


# user class for providing authentication
class UserNotFoundError(Exception):
    pass

class User(UserMixin):
    USERS = {
        # username: password
        'jackyma': 'password',
        'vagrant': 'vagrant'
    }
    
    def __init__(self, user_id):
        if not user_id in self.USERS:
            raise UserNotFoundError()
        self.id = user_id
        self.password = self.USERS[user_id]

    def get_name(self):
        return "Jacky Ma"  # typically the user's name

    @classmethod
    def get(self_class, id):
        '''Return user instance of id, return None if not exist'''
        try:
            return self_class(id)
        except UserNotFoundError:
            return None
            
@login_manager.user_loader
@blog_engine.user_loader
def load_user(user_id):
    return User.get(user_id)

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
    return '''
        <form action="/login/check" method="post">
            <p>Username: <input name="username" type="text"></p>
            <p>Password: <input name="password" type="password"></p>
            <input type="submit">
        </form>
    '''

@app.route('/login/check', methods=['post'])
def login_check():
    # validate username and password
    user = User.get(request.form['username'])
    if (user and user.password == request.form['password']):
        login_user(user)
    else:
        flash('Username or password incorrect')

    return redirect(url_for('index'))
    
@app.route("/logout/")
def logout():
    logout_user()
    return redirect(url_for('index'))

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
    app.run(port=app.config['PORT'], use_reloader=True)


