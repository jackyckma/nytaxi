DROP TABLE IF EXISTS tripdata;

CREATE TABLE tripdata(
trip_id              serial primary key,
medallion            integer,
hack_license         integer,
vendor_id            char(3),
rate_code            smallint,
store_and_fwd_flag   char(1),
pickup_datetime      timestamp,
dropoff_datetime     timestamp ,
passenger_count      smallint,
trip_distance        real,
pickup_longitude     double precision,
pickup_latitude      double precision,
dropoff_longitude    double precision,
dropoff_latitude     double precision,
payment_type         char(3),
fare_amount          numeric(10, 3),
surcharge            numeric(10, 3),
mta_tax              numeric(10, 3),
tip_amount           numeric(10, 3),
tolls_amount         numeric(10, 3),
total_amount         numeric(10, 3)
);

\echo 'CREATE GEOMETRY COLUMNS'
SELECT AddGeometryColumn('tripdata','geom_pickup',4326,'POINT',2);
SELECT AddGeometryColumn('tripdata','geom_dropoff',4326,'POINT',2);

\echo 'INSERT 2013 SAMPLE DATA'
\COPY tripdata (medallion, hack_license, vendor_id, rate_code, store_and_fwd_flag, pickup_datetime, dropoff_datetime, passenger_count, trip_distance, pickup_longitude, pickup_latitude, dropoff_longitude, dropoff_latitude, payment_type, fare_amount, surcharge, mta_tax, tip_amount, tolls_amount, total_amount) FROM 'D:\jacky\Research\GitHub\nytaxi\data\nytaxi2013sample.csv' DELIMITER ',' CSV HEADER;
\echo 'INSERT 2014 SAMPLE DATA'
\COPY tripdata (medallion, hack_license, vendor_id, rate_code, store_and_fwd_flag, pickup_datetime, dropoff_datetime, passenger_count, trip_distance, pickup_longitude, pickup_latitude, dropoff_longitude, dropoff_latitude, payment_type, fare_amount, surcharge, mta_tax, tip_amount, tolls_amount, total_amount) FROM 'D:\jacky\Research\GitHub\nytaxi\data\nytaxi2014sample.csv' DELIMITER ',' CSV HEADER;


\echo 'UPDATE GEOMETRY COLUMNS'
UPDATE tripdata SET geom_pickup = ST_SetSRID(ST_MakePoint(pickup_longitude, pickup_latitude), 4326);
UPDATE tripdata SET geom_dropoff = ST_SetSRID(ST_MakePoint(dropoff_longitude, dropoff_latitude), 4326);