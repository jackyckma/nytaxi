from sqlalchemy import create_engine, MetaData
from sklearn.cross_validation import train_test_split
from sklearn import svm
import pandas as pd
import random
import settings

##initializing the server
print 'Initializing'

config=settings.DevelopmentConfig

engine = create_engine(config.DATABASE_URI)
meta = MetaData()
meta.create_all(bind=engine)

taxi_df = pd.read_sql_query('SELECT * FROM tripdata WHERE random() < 0.03', engine)
hackfare_df = pd.read_sql_query('SELECT * FROM hack_fare_all where trips > 100 order by avg_total', engine)
uber_df = pd.read_sql_query('SELECT * FROM uber_trip WHERE random() < 0.01', engine)


# total 43191 hack_license
low_earner = set(hackfare_df[:10000]['hack_license'])
high_earner = set(hackfare_df[-10000:]['hack_license'])
average_earner = set(hackfare_df['hack_license']) - low_earner - high_earner


low_data=taxi_df[taxi_df.hack_license.isin(low_earner)][['pickup_datetime', 'pickup_longitude', 'pickup_latitude']].copy()
high_data=taxi_df[taxi_df.hack_license.isin(high_earner)][['pickup_datetime', 'pickup_longitude', 'pickup_latitude']].copy()
average_data=taxi_df[taxi_df.hack_license.isin(average_earner)][['pickup_datetime', 'pickup_longitude', 'pickup_latitude']].copy()
uber_data=uber_df[['datetime', 'longitude', 'latitude']].copy()

taxi_df = None
uber_df = None

low_data['class']='low'
low_data.columns=['datetime', 'lng', 'lat', 'class']
high_data['class']='high'
high_data.columns=['datetime', 'lng', 'lat', 'class']
average_data['class']='avg'
average_data.columns=['datetime', 'lng', 'lat', 'class']
uber_data['class']='uber'
uber_data.columns=['datetime', 'lng', 'lat', 'class']

data_set = pd.concat([low_data, high_data, average_data, uber_data])

data_set['dayofweek']=data_set.datetime.dt.weekday
data_set['hourofday']=data_set.datetime.dt.hour

X = data_set[['dayofweek', 'hourofday', 'lng', 'lat']]
Y = data_set['class']


x_train, x_test, y_train, y_test = train_test_split(X, Y, test_size=0.33, random_state=42)


clf = svm.SVC()
clf.fit(x_train, y_train)
score_1 = clf.score(x_test, y_test)
'''
Default: score = 0.484749834065552
original hourofday
{'kernel': 'rbf', 'C': 1.0, 'verbose': False, 'probability': False, 'degree': 3, 'shrinking': True, 'max_iter': -1, 'random_state': None, 'tol': 0.001, 'cache_size': 200, 'coef0': 0.0, 'gamma': 0.0, 'class_weight': None}
'''

# shift the break of hours to '6am' as this is the most likely boundary (instead of 12mn)
# i.e. 6am -> 00; 11pm ->17; 5am -> 23
data_set['transformedhour']= data_set['hourofday'].map(lambda x: (x-6)%24)
X = data_set[['dayofweek', 'transformedhour', 'lng', 'lat']]
Y = data_set['class']
x_train, x_test, y_train, y_test = train_test_split(X, Y, test_size=0.33, random_state=42)
clf = svm.SVC()
clf.fit(x_train, y_train)
score_2 = clf.score(x_test, y_test)

# 0.48345396504314297

#using probability model
clf = svm.SVC(probability=True)
clf.fit(x_train, y_train)
score_3 = clf.score(x_test, y_test)

# Clustering methods:
# Mean-shift
# DBSCAN
# Birch
