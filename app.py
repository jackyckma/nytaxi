from flask import Flask, flash, render_template, request, redirect, render_template_string, url_for, send_from_directory, jsonify
from flask.ext.login import UserMixin, LoginManager, login_user, logout_user
from flask.ext.blogging import SQLAStorage, BloggingEngine
import flask.json
import geojson
from geoalchemy2 import Geometry
from sqlalchemy import create_engine, MetaData
import pandas as pd
import random

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
appdata['taxi_df'] = pd.read_sql_query('SELECT * FROM tripdata WHERE random() <' + app.config['SAMPLESIZE'], engine)
appdata['hack_fare_df'] = pd.read_sql_query('SELECT * FROM hack_fare_all where trips > 100 order by avg_total', engine)
appdata['uber_df'] = pd.read_sql_query('SELECT * FROM uber_trip WHERE random() <' + app.config['SAMPLESIZE'], engine)
print 'ok'
print '{0} trip samples loaded'.format(len(appdata['taxi_df']))
print '{0} hack_driver records loaded'.format(len(appdata['hack_fare_df']))

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

@app.route("/loaddata/<querystr>", methods=["GET", "POST"])
def load_taxi_data(querystr):
    print 'AJAX load data: {0}'.format(querystr)
    data=None
    taxi_df=appdata['taxi_df']
    uber_df=appdata['uber_df']
    queryitems={}

    print 'Query Str:', querystr

    for p_pair in querystr.split('&'):
        p_key, p_value = p_pair.split('=')
        queryitems[p_key] = p_value

    print 'Query Items:', queryitems

    # slice on long vs short trip

    sample_scale=1
    if (queryitems['hour']!='all'): sample_scale = 24
    if (queryitems['weekday']=='weekend'): sample_scale *= 2.5

    uberslice = uber_df.sample(n=1250 * sample_scale)
    dataslice = taxi_df.sample(n=4500 * sample_scale)

    dataslice={
        'all': dataslice,
        'long': dataslice[dataslice.trip_distance>1.90],
        'short': dataslice[dataslice.trip_distance<=1.90]
    }[queryitems['tripdist']]

    # slice on driver income
    # set top 10000 and bottom 10000 income drivers
    df_hf=appdata['hack_fare_df']
    hacks={
        'all':set(df_hf['hack_license']),
        'low':set(df_hf[:10000]['hack_license']),
        'high':set(df_hf[-10000:]['hack_license'])
    }[queryitems['income']]
    print '{0} drivers selected'.format(len(hacks))
    dataslice=dataslice[dataslice.hack_license.isin(hacks)]

    # slice on day and time
    # l=k[k.pickup_datetime.dt.dayofweek ==3]
    # l=k[k.pickup_datetime.dt.hour ==3]
    if ((queryitems['weekday']!='all') or (queryitems['hour']!='all')):
        weekday_filter={
            'weekday':[0,1,2,3,4], # 0 - Monday, 6 - Sunday
            'weekend': [5,6],
            'all': range(7)
        }[queryitems['weekday']]
        time_filter={
            '0000': [0, 1],
            '0200': [2, 3],
            '0400': [4, 5],
            '0600': [6, 7],
            '0800': [8, 9],
            '1000': [10, 11],
            '1200': [12, 13],
            '1400': [14, 15],
            '1600': [16, 17],
            '1800': [18, 19],
            '2000': [20 ,21],
            '2200': [22, 23],
            'peak': [8, 9, 17, 18],
            'night': [19, 20, 21, 22],
            'late': [1, 2, 3, 4],
            'all': range(24)
        }[queryitems['hour']]
        dataslice=dataslice[dataslice.pickup_datetime.dt.dayofweek.isin(weekday_filter) &\
            dataslice.pickup_datetime.dt.hour.isin(time_filter)]
        uberslice=uberslice[uberslice['datetime'].dt.dayofweek.isin(weekday_filter) &\
            uberslice['datetime'].dt.hour.isin(time_filter)]


    print dataslice.describe()
    print uberslice.describe()


    # valid value for queryitems['location'] = 'pickup' or 'dropoff'
    pickup_points = geojson.MultiPoint([(x,y) for x,y in zip(
        dataslice['pickup_longitude'], dataslice['pickup_latitude'])])
    dropoff_points = geojson.MultiPoint([(x,y) for x,y in zip(
        dataslice['dropoff_longitude'], dataslice['dropoff_latitude'])])
    uber_points = geojson.MultiPoint([(x,y) for x,y in zip(
        uberslice['longitude'], uberslice['latitude'])])

    pickup_feature = geojson.Feature(geometry=pickup_points,properties={\
        'status':'pickup',
        'color': '#ff7800'})
    dropoff_feature = geojson.Feature(geometry=dropoff_points, properties={\
        'status':'dropoff',
        'color': '#006799'})
    uber_feature = geojson.Feature(geometry=uber_points, properties={\
        'status':'uber',
        'color': '#449933'})
    data = geojson.FeatureCollection([pickup_feature, dropoff_feature, uber_feature])
    return geojson.dumps(data)


if __name__ == "__main__":
	if nytaxi_config == 'OD_DEBUG':
		app.run(host=app.config['HOST'], port=app.config['PORT'], use_reloader=True)
	else:
    	app.run(port=app.config['PORT'], use_reloader=True)
