from flask import Flask, flash, render_template, request, redirect,\
    render_template_string, url_for, send_from_directory
from flask.ext.login import UserMixin, LoginManager, login_user, logout_user
from flask.ext.blogging import SQLAStorage, BloggingEngine
import flask.json
import geojson
from sqlalchemy import create_engine, MetaData
from geoalchemy2 import Geometry
import pandas as pd
import random
import os

# settings is a package which stores the configrations for the server
import settings

# initializing the server
print 'Initializing',

# allow users to use environment variable $nytaxi_config to change the config
nytaxi_config = os.getenv('nytaxi_config', 'DEBUG')
print '[MODE={0}]...'.format(nytaxi_config),

# initialize the configurations accorund to $nytaxi_config
app = Flask(__name__)
if nytaxi_config == 'DEBUG':
    app.config.from_object(settings.DevelopmentConfig)
elif nytaxi_config == 'OD_DEBUG':
    app.config.from_object(settings.OD_DevelopmentConfig)
elif nytaxi_config == 'TEST':
    app.config.from_object(settings.TestingConfig)
else:
    app.config.from_object(settings.ProductionConfig)

# extensions required by flask-blog / sqlalchemy
engine = create_engine(app.config['DATABASE_URI'])
meta = MetaData()
sql_storage = SQLAStorage(engine, metadata=meta)
blog_engine = BloggingEngine(app, sql_storage)
login_manager = LoginManager(app)
meta.create_all(bind=engine)

print 'ok'

# data fields of taxi_df for references
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

# load Data
appdata = {}
print 'Loading from database...',
appdata['taxi_df'] = pd.read_sql_query('SELECT * FROM tripdata WHERE random() <' + app.config['SAMPLESIZE'], engine)
appdata['hack_fare_df'] = pd.read_sql_query('SELECT * FROM hack_fare_all where trips > 100 order by avg_total', engine)
appdata['uber_df'] = pd.read_sql_query('SELECT * FROM uber_trip WHERE random() <' + app.config['SAMPLESIZE'], engine)
print 'ok'

# load CSV Data
print 'Loading from CSv...',
appdata['hotspots_df'] = pd.read_csv('./data/clusters.csv')
print 'ok'

# description of the data
print '{0} taxi trip samples'.format(len(appdata['taxi_df']))
print '{0} hack driver records'.format(len(appdata['hack_fare_df']))
print '{0} uber trip records'.format(len(appdata['uber_df']))
print '{0} hotspots records'.format(len(appdata['hotspots_df']))



# class for blog user authentication
class UserNotFoundError(Exception):
    pass

class User(UserMixin):
    USERS = {
        app.config['BLOGGING_USER']: app.config['BLOGGING_PASSWORD'],
    }

    def __init__(self, user_id):
        if not user_id in self.USERS:
            raise UserNotFoundError()
        self.id = user_id
        self.password = self.USERS[user_id]

    def get_name(self):
        return app.config['BLOGGING_UNAME'] 

    @classmethod
    def get(self_class, uid):
        '''Return user instance of id, return None if not exist'''
        try:
            return self_class(uid)
        except UserNotFoundError:
            return None


# flask modules
@login_manager.user_loader
@blog_engine.user_loader
def load_user(user_id):
    return User.get(user_id)


# login page
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
    user = User.get(request.form['username'])
    if (user and user.password == request.form['password']):
        login_user(user)
    else:
        flash('Username or password incorrect')

    return redirect(url_for('index'))

# logout user and redirect to front page
@app.route("/logout/")
def logout():
    logout_user()
    return redirect(url_for('index'))

# to retrieve static files for blog
@app.route('/blogfile/<filename>')
def blogfile(filename):
    # show the user profile for that user
    return send_from_directory('static/blogfiles', filename, as_attachment=True)


# regular navigation pages
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


# url used by nytaxi.html to retrieve data
# core of the whole program
@app.route("/loaddata/<querystr>", methods=["GET", "POST"])
def load_taxi_data(querystr):
    print 'AJAX load data: {0}'.format(querystr)
    data = None
    taxi_df = appdata['taxi_df']
    uber_df = appdata['uber_df']
    hotspots_df = appdata['hotspots_df']
    queryitems = {}

    for p_pair in querystr.split('&'):
        p_key, p_value = p_pair.split('=')
        queryitems[p_key] = p_value


	# fix sampling rate for varius time duration
    sample_scale = 1
    if (queryitems['hour'] != 'all'): sample_scale = 24
    if (queryitems['weekday'] == 'weekday'): sample_scale *= (7/5.0)
    if (queryitems['weekday'] == 'weekend'): sample_scale *= (7/2.0)

	# sample the data
    uberslice = uber_df.sample(n=1250 * sample_scale)
    dataslice = taxi_df.sample(n=4500 * sample_scale)
    
    # slice the hotspots according to the density
	# used when day and time = all
    hotspotsslice_1 = hotspots_df[800 < hotspots_df['items']]
    hotspotsslice_2 = hotspots_df[400 < hotspots_df['items']]
    hotspotsslice_3 = hotspots_df[200 < hotspots_df['items']]
    hotspotsslice_4 = hotspots_df[100 < hotspots_df['items']]

	# slice the trip data according to distance selected
    dataslice = {
        'all': dataslice,
        'long': dataslice[dataslice.trip_distance > 1.90],
        'short': dataslice[dataslice.trip_distance <= 1.90]
    }[queryitems['tripdist']]

    # slice on driver income
    df_hf = appdata['hack_fare_df']
    hacks = {
        'all':set(df_hf['hack_license']),
        'low':set(df_hf[:10000]['hack_license']),
        'high':set(df_hf[-10000:]['hack_license'])
    }[queryitems['income']]
    print '{0} drivers selected'.format(len(hacks))
    dataslice = dataslice[dataslice.hack_license.isin(hacks)]

    # slice on day and time
    if ((queryitems['weekday'] != 'all') or (queryitems['hour'] != 'all')):
    	# set filter values
        weekday_filter = {
            'weekday':[0, 1, 2, 3, 4], # 0 - Monday, 6 - Sunday
            'weekend': [5, 6],
            'all': range(7)
        }[queryitems['weekday']]
        hotspot_dow_filter = {
            'weekday':[1],
            'weekend': [0],
            'all': [0,1]
        }[queryitems['weekday']]
        time_filter = {
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
            '2000': [20, 21],
            '2200': [22, 23],
            'peak': [8, 9, 16, 17],
            'night': [20, 21, 22, 23],
            'late': [1, 2, 3, 4],
            'all': range(24)
        }[queryitems['hour']]
        # do the slicing for trip data
        dataslice = dataslice[dataslice.pickup_datetime.dt.dayofweek.isin(weekday_filter) &\
            dataslice.pickup_datetime.dt.hour.isin(time_filter)]
        uberslice = uberslice[uberslice['datetime'].dt.dayofweek.isin(weekday_filter) &\
            uberslice['datetime'].dt.hour.isin(time_filter)]
        # slicing for hotspot data
        hotspotsslice_1 = hotspots_df[hotspots_df['weekdays'].isin(hotspot_dow_filter) &\
            hotspots_df['hour'].isin(time_filter) & (300 <= hotspots_df['items'])]
        hotspotsslice_2 = hotspots_df[hotspots_df['weekdays'].isin(hotspot_dow_filter) &\
            hotspots_df['hour'].isin(time_filter) & (100 <= hotspots_df['items']) & (hotspots_df['items'] < 300)]
        hotspotsslice_3 = hotspots_df[hotspots_df['weekdays'].isin(hotspot_dow_filter) &\
            hotspots_df['hour'].isin(time_filter) & (30 <= hotspots_df['items']) & (hotspots_df['items'] < 100)]
        hotspotsslice_4 = hotspots_df[hotspots_df['weekdays'].isin(hotspot_dow_filter) &\
            hotspots_df['hour'].isin(time_filter) & (10 <= hotspots_df['items']) & (hotspots_df['items'] < 30)]

	# debug uses - print the statistics on server side
    print dataslice.describe()
    print uberslice.describe()
    print hotspotsslice_1.describe()
    print hotspotsslice_2.describe()
    print hotspotsslice_3.describe()
    print hotspotsslice_4.describe()

    # prepare geojson data
    pickup_points = geojson.MultiPoint([(x, y) for x, y in zip(
        dataslice['pickup_longitude'], dataslice['pickup_latitude'])])
    dropoff_points = geojson.MultiPoint([(x, y) for x, y in zip(
        dataslice['dropoff_longitude'], dataslice['dropoff_latitude'])])
    uber_points = geojson.MultiPoint([(x, y) for x, y in zip(
        uberslice['longitude'], uberslice['latitude'])])
    hotspots_1_points = geojson.MultiPoint([(x, y) for x, y in zip(
        hotspotsslice_1['lng'], hotspotsslice_1['lat'])])
    hotspots_2_points = geojson.MultiPoint([(x, y) for x, y in zip(
        hotspotsslice_2['lng'], hotspotsslice_2['lat'])])
    hotspots_3_points = geojson.MultiPoint([(x, y) for x, y in zip(
        hotspotsslice_3['lng'], hotspotsslice_3['lat'])])
    hotspots_4_points = geojson.MultiPoint([(x, y) for x, y in zip(
        hotspotsslice_4['lng'], hotspotsslice_4['lat'])])

	# pack geojson data as features
    pickup_feature = geojson.Feature(geometry=pickup_points, properties={\
        'status':'pickup',
        'radius':2.5,
        'color': '#ff7800'})
    dropoff_feature = geojson.Feature(geometry=dropoff_points, properties={\
        'status':'dropoff',
        'radius':2.5,
        'color': '#006799'})
    uber_feature = geojson.Feature(geometry=uber_points, properties={\
        'status':'uber',
        'radius':2.5,
        'color': '#449933'})
    hotspots_1_feature = geojson.Feature(geometry=hotspots_1_points, properties={\
        'status':'hotspots',
        'hotspots':1,
        'radius':25,
        'color': '#dc143c'})
    hotspots_2_feature = geojson.Feature(geometry=hotspots_2_points, properties={\
        'status':'hotspots',
        'hotspots':1,
        'radius':15,
        'color': '#dc143c'})
    hotspots_3_feature = geojson.Feature(geometry=hotspots_3_points, properties={\
        'status':'hotspots',
        'hotspots':1,
        'radius':8.5,
        'color': '#dc143c'})
    hotspots_4_feature = geojson.Feature(geometry=hotspots_4_points, properties={\
        'status':'hotspots',
        'hotspots':1,
        'radius':5,
        'color': '#dc143c'})
        
    # pack into geojson FeatureCollection and send to webpage
    data = geojson.FeatureCollection([pickup_feature, dropoff_feature, uber_feature,\
        hotspots_1_feature, hotspots_2_feature, hotspots_3_feature, hotspots_4_feature])
    return geojson.dumps(data)


# main procedure
if __name__ == "__main__":
    if nytaxi_config == 'OD_DEBUG':
        app.run(host=app.config['HOST'], port=app.config['PORT'], use_reloader=True)
    else:
        app.run(port=app.config['PORT'], use_reloader=True)
