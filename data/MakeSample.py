# -*- coding: utf-8 -*-
"""
Created on Mon Sep 14 00:18:27 2015

@author: jacky
"""

import random
import csv
from itertools import izip
import pandas as pd

#config
do_sampling = True
do_cleansing = True

tripdata_2014 = ['yellow_tripdata_2014-12.csv', 'yellow_tripdata_2014-11.csv', 'yellow_tripdata_2014-10.csv', 'yellow_tripdata_2014-09.csv', 'yellow_tripdata_2014-08.csv', 'yellow_tripdata_2014-07.csv', 'yellow_tripdata_2014-06.csv', 'yellow_tripdata_2014-05.csv', 'yellow_tripdata_2014-04.csv', 'yellow_tripdata_2014-03.csv', 'yellow_tripdata_2014-02.csv', 'yellow_tripdata_2014-01.csv']
tripdata_2013 = ['trip_data_2013-01.csv', 'trip_data_2013-02.csv', 'trip_data_2013-03.csv', 'trip_data_2013-04.csv', 'trip_data_2013-05.csv', 'trip_data_2013-06.csv', 'trip_data_2013-07.csv', 'trip_data_2013-08.csv', 'trip_data_2013-09.csv', 'trip_data_2013-10.csv', 'trip_data_2013-11.csv', 'trip_data_2013-12.csv']
tripfare_2013 = ['trip_fare_2013-01.csv', 'trip_fare_2013-02.csv', 'trip_fare_2013-03.csv', 'trip_fare_2013-04.csv', 'trip_fare_2013-05.csv', 'trip_fare_2013-06.csv', 'trip_fare_2013-07.csv', 'trip_fare_2013-08.csv', 'trip_fare_2013-09.csv', 'trip_fare_2013-10.csv', 'trip_fare_2013-11.csv', 'trip_fare_2013-12.csv']
outcsvheader=['medallion', 'hack_license', 'vendor_id', 'rate_code', 'store_and_fwd_flag', 'pickup_datetime', 'dropoff_datetime', 'passenger_count', 'trip_distance', 'pickup_longitude', 'pickup_latitude', 'dropoff_longitude', 'dropoff_latitude', 'payment_type', 'fare_amount', 'surcharge', 'mta_tax', 'tip_amount', 'tolls_amount', 'total_amount']

'''
RAW HEADERS IN THE FILES

trip_data_2013-01.csv
['medallion'
 ' hack_license'
 ' vendor_id'
 ' rate_code'
 ' store_and_fwd_flag'
 ' pickup_datetime'
 ' dropoff_datetime'
 ' passenger_count'
 ' trip_time_in_secs'
 ' trip_distance'
 ' pickup_longitude'
 ' pickup_latitude'
 ' dropoff_longitude'
 ' dropoff_latitude']

trip_fare_2013-01.csv
['medallion'
 ' hack_license'
 ' vendor_id'
 ' pickup_datetime'
 ' payment_type'
 ' fare_amount'
 ' surcharge'
 ' mta_tax'
 ' tip_amount'
 ' tolls_amount'
 ' total_amount']

yellow_tripdata_2014-01.csv
['vendor_id'
 ' pickup_datetime'
 ' dropoff_datetime'
 ' passenger_count'
 ' trip_distance'
 ' pickup_longitude'
 ' pickup_latitude'
 ' rate_code'
 ' store_and_fwd_flag'
 ' dropoff_longitude'
 ' dropoff_latitude'
 ' payment_type'
 ' fare_amount'
 ' surcharge'
 ' mta_tax'
 ' tip_amount'
 ' tolls_amount'
 ' total_amount']

 
DATA CLEANSING ISSUES:
Four repeated fields in trip_fare (compare with trip_data):
- 'medallion'
- ' hack_license'
- ' vendor_id'
- ' pickup_datetime'

Additional fields in 2013 data:
- 'medallion' : create dummy field in 2014 data
- ' hack_license' : create dummy field in 2014 data
- ' trip_time_in_secs' : drop
 
 '''

def filelen(fname):
#Utility function, not in use
#Return the length of file
	with open(fname) as f:
		for i, l in enumerate(f):
			pass
	return i + 1
    
def filelendict(flist, verbose=False):
#Utility function, not in use
#Return the length each files in List flist
	filedict={}
	for fname in flist:
		if verbose: print(fname),
		filedict[fname]=filelen(fname)
		if verbose: print filedict[fname]
	return filedict

def sampling(infilelist, outfilename, pct):
# infilelist - list of infile names
# outfilename - name of outfile
# pct - percentage of sampling
	with open(outfilename, 'wb') as outfile:
		writer = csv.DictWriter(outfile, fieldnames=outcsvheader)
		writer.writeheader()
		for filename in infilelist:
			print filename
			with open(filename, 'rb') as infile:
				reader = csv.DictReader(infile)
				for row in reader:
					if random.random() < pct:
# map old fields from input file into new fields in output file
# created dummy items 'medallion' and 'hack-license'
						datadict={
							'medallion': 2014000000,
							'hack_license': 2014000000,
							'vendor_id': row['vendor_id'],
							'rate_code': row[' rate_code'],
							'store_and_fwd_flag': row[' store_and_fwd_flag'],
							'pickup_datetime': row[' pickup_datetime'],
							'dropoff_datetime': row[' dropoff_datetime'],
							'passenger_count': row[' passenger_count'],
							'trip_distance': row[' trip_distance'],
							'pickup_longitude': row[' pickup_longitude'],
							'pickup_latitude': row[' pickup_latitude'],
							'dropoff_longitude': row[' dropoff_longitude'],
							'dropoff_latitude': row[' dropoff_latitude'],
							'payment_type': row[' payment_type'],
							'fare_amount': row[' fare_amount'],
							'surcharge': row[' surcharge'],
							'mta_tax': row[' mta_tax'],
							'tip_amount': row[' tip_amount'],
							'tolls_amount': row[' tolls_amount'],
							'total_amount': row[' total_amount']}
						writer.writerow(datadict)


def pairedsampling(infiletuplelist, outfilename, pct):
# infilelist - list of infile names in tuples
# outfilename - name of outfile
# pct - percentage of sampling
	with open(outfilename, 'wb') as outfile:
		writer = csv.DictWriter(outfile, fieldnames=outcsvheader)
		writer.writeheader()
		for (fname1, fname2) in infiletuplelist:
			print fname1, fname2
			with open(fname1, 'rb') as infile1, open(fname2, 'rb') as infile2:
				reader1 = csv.DictReader(infile1)
				reader2 = csv.DictReader(infile2)
				for row_f1, row_f2 in izip(reader1, reader2):
					if random.random() < pct:
						datadict={
# map old fields from two files into new fields in output file
							 'medallion': row_f1['medallion'],
							 'hack_license': row_f1[' hack_license'],
							 'vendor_id': row_f1[' vendor_id'],
							 'rate_code': row_f1[' rate_code'],
							 'store_and_fwd_flag': row_f1[' store_and_fwd_flag'],
							 'pickup_datetime': row_f1[' pickup_datetime'],
							 'dropoff_datetime': row_f1[' dropoff_datetime'],
							 'passenger_count': row_f1[' passenger_count'],
							 'trip_distance': row_f1[' trip_distance'],
							 'pickup_longitude': row_f1[' pickup_longitude'],
							 'pickup_latitude': row_f1[' pickup_latitude'],
							 'dropoff_longitude': row_f1[' dropoff_longitude'],
							 'dropoff_latitude': row_f1[' dropoff_latitude'],
							 'payment_type': row_f2[' payment_type'],
							 'fare_amount': row_f2[' fare_amount'],
							 'surcharge': row_f2[' surcharge'],
							 'mta_tax': row_f2[' mta_tax'],
							 'tip_amount': row_f2[' tip_amount'],
							 'tolls_amount': row_f2[' tolls_amount'],
							 'total_amount': row_f2[' total_amount']}
						writer.writerow(datadict)

						
def datacleansing(infname, outfname):
#clean the nytaxi data
	print 'Reading: {0}'.format(infname)
	dfdata=pd.read_csv(infname, index_col=None, parse_dates=['pickup_datetime', 'dropoff_datetime'], date_parser = (lambda x: pd.datetime.strptime(x, '%Y-%m-%d %H:%M:%S')))

	#filter off the Zero-value records
	dflen=len(dfdata)
	print '{0} original records.'.format(dflen)
	dfdata=dfdata[(dfdata.pickup_longitude!=0) & (dfdata.pickup_latitude!=0) & (dfdata.dropoff_longitude!=0) & (dfdata.dropoff_latitude!=0)]
	print '{0} zero-gps-value records filtered.'.format(dflen-len(dfdata))

	#get the subset of records with swapped lat and lon values
	subset=dfdata[(dfdata.pickup_longitude>38) & (dfdata.pickup_longitude<43) & (dfdata.pickup_latitude>-75) & (dfdata.pickup_latitude<-71)]
	#temp dataframe holding a re-swapped lat and lon values
	k=subset[['pickup_longitude', 'pickup_latitude', 'dropoff_longitude', 'dropoff_latitude']].apply(lambda x: pd.Series({'pickup_longitude':x.pickup_latitude, 'pickup_latitude':x.pickup_longitude, 'dropoff_longitude':x.dropoff_latitude, 'dropoff_latitude':x.dropoff_longitude}), axis=1)
	#update the original dataframe with temp dataframe
	dfdata.update(k)
	print '{0} swapped records updated.'.format(len(k))

	#filter remaining invalid position records
	dflen=len(dfdata)
	dfdata=dfdata[(dfdata.pickup_longitude>-75) & (dfdata.pickup_longitude<-71) & (dfdata.pickup_latitude>38) & (dfdata.pickup_latitude<43)]
	dfdata=dfdata[(dfdata.dropoff_longitude>-75) & (dfdata.dropoff_longitude<-71) & (dfdata.dropoff_latitude>38) & (dfdata.dropoff_latitude<43)]
	dfdata=dfdata[dfdata.trip_distance<100000]
	print '{0} invalid records removed.'.format(dflen - len(dfdata))

	print 'Writing: {0}'.format(outfname)
	dfdata.to_csv(outfname, index=False)
	return dfdata

#main

if do_sampling:
    print ('Sampling...')
    #2013 sampling
    #two sets of files [tripdata_2013] and [tripfare_2013] are merge
    tuplelist=[(fname1, fname2) for (fname1, fname2) in zip(tripdata_2013, tripfare_2013)]
    pairedsampling(tuplelist, 'nytaxi2013rawsample.csv', 0.01)
    
    #2014 sampling
    #reminder: there is no 'medallion' and 'hack_license' in 2014 data
    sampling(tripdata_2014, 'nytaxi2014rawsample.csv', 0.01)
else:
    print ('Skip Sampling...')

if do_cleansing:
    print('Cleansing...')
    datacleansing('nytaxi2013rawsample.csv', 'nytaxi2013sample.csv')
    datacleansing('nytaxi2014rawsample.csv', 'nytaxi2014sample.csv')
else:
    print ('Skip Cleansing...')

