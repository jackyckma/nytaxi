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

# for testing
# taxi_df = pd.read_sql_query('SELECT * FROM tripdata WHERE random() < 0.1', engine)
# for production
taxi_df = pd.read_sql_query('SELECT * FROM tripdata', engine)

taxi_data=taxi_df[['pickup_datetime', 'pickup_longitude', 'pickup_latitude']].copy()
taxi_data.columns=['datetime', 'lng', 'lat']
taxi_df = None


data_set = taxi_data
data_set['dayofweek']=data_set.datetime.dt.weekday
data_set['hourofday']=data_set.datetime.dt.hour
data_set['weekdays']=(data_set.dayofweek < 5)*1


from sklearn.cluster import MeanShift
ms=MeanShift(bandwidth=0.003, cluster_all=False, min_bin_freq=5)

all_clusters=None


# loop through weekdays and weekends, and each 2-hours time duration
# train the data with MeanShift
# get the cluster_centers
# and packed with 'items' equals to the number of items belongs to the center
# which will be used as a weighting in display
for d in [0, 1]:
    for h in [[0,1],[2,3],[4,5],[6,7],[8,9],[10,11],[12,13],[14,15],[16,17],[18,19],[20,21],[22,23]]:
        print 'Clusters for weekdays=', d, '; hour=', h
        # train only on lng and lat
        X = data_set[(data_set.weekdays==d) & (data_set.hourofday.isin(h))][['lng', 'lat']]
        ms.fit(X)
        print 'Number of clusters:', len(ms.cluster_centers_)
        cluster_center = pd.DataFrame(ms.cluster_centers_, columns=['lng', 'lat'])
        cluster_center['items'] = cluster_center.index.map(lambda x: sum(ms.labels_==x))
        cluster_center['hour']=h[0]
        cluster_center['weekdays']=d
        if all_clusters is None:
            all_clusters = cluster_center.copy()
        else:
            all_clusters = all_clusters.append(cluster_center)

# output to csv file
all_clusters.to_csv('clusters.csv', index=False)
