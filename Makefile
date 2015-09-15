# MAKEFILE for NYTAXI PROJECT
#
# Prototype only!
# details need to be filled

# We're going to declare the command we use to talk to the database
all: app.py

### Set Environment
config:
	activate 
	conda install

### Get Data files
### Warning: Huge files ~ 60Gb
data2013:
	http://www.andresmh.com/nyctaxitrips/

data2014:
	http://www.nyc.gov/html/tlc/html/about/trip_record_data.shtml

dataweather:
	http://www.ncdc.noaa.gov/orders/qclcd/
	unzip and extract hour data, delete zip files
datauber:
	https://github.com/fivethirtyeight/uber-tlc-foil-response

dataholidays:
	http://www.timeanddate.com/holidays/us/2014#!hol=25
	http://www.timeanddate.com/holidays/us/2013#!hol=25

### Make database
database:
	#drop old table
	#create table
	#import 2013, 2014 sample data
	#need to config password file [~/pdpass.conf] (http://www.postgresql.org/docs/9.4/static/libpq-pgpass.html)

	PATH=%PATH%;c:\PostgreSQL\9.3\bin	
	#need to enable POSTGIS Extension on database
	psql -d nytaxi -U postgres -c "CREATE EXTENSION postgis;"
	psql -d nytaxi -U postgres -f nytaxi.sql
	
	#delete source files?

### Make sampling data from raw data
### Warning: Takes a long time
samplingdata:
	python data/MakeSample.py

### Make html version of ipython notebook
	ipython nbconvert

### Cleanup...
clean:

