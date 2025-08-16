# https://isc.sans.edu/api/

import os
import sys
import requests
import pandas as pd
import csv
import mysql.connector
import ipaddress
from sqlalchemy import create_engine
import numpy as np
from datetime import datetime, date, timedelta



def ip_to_int_vectorized(ip_series):
#    """Convert IP addresses to integers using vectorized operations"""
    def convert_ip(ip_str):
        if pd.isna(ip_str) or ip_str == '' or ip_str is None:
            return None
        try:
            return int(ipaddress.IPv4Address(str(ip_str).strip()))
        except:
            print(f"Warning: Invalid IP address '{ip_str}', setting to NULL")
            return None

    return ip_series.apply(convert_ip)

def validate(date_text):
        try:
            datetime.fromisoformat(date_text)
            return date_text
        except ValueError:
            raise ValueError("Incorrect data format, should be YYYY-MM-DD")



def import_csv_pandas(csv_file_path, connection_string):
#    """Import CSV using pandas - faster for large datasets"""

    try:
        # Read CSV with explicit dtype specification to avoid warnings
        df = pd.read_csv(
            csv_file_path,
            dtype={
                'domainname': 'string',
                'ip': 'string',
                'type': 'string',
                'firstseen': 'string',
                'score': 'Int64',  # Nullable integer
                'scorereason': 'string'
            },
            keep_default_na=False,  # Don't convert empty strings to NaN automatically
            na_values=['']  # Only treat empty strings as NaN
        )

        print(f"Read {len(df)} records from CSV")

        # Data preprocessing
        print("Processing IP addresses...")
        df['ip'] = ip_to_int_vectorized(df['ip'])

        # Handle empty strings and convert to None for SQL NULL
        df['type'] = df['type'].replace('', None)
        df['scorereason'] = df['scorereason'].replace('', None)

        # Convert date column
        print("Processing dates...")
        df['firstseen'] = pd.to_datetime(df['firstseen'], format='%Y-%m-%d', errors='coerce').dt.date

        # Handle score column - ensure it's integer and handle NaN
        df['score'] = df['score'].fillna(0)

        # Remove rows with missing required fields
        initial_count = len(df)
        df = df.dropna(subset=['domainname', 'firstseen'])
        dropped_count = initial_count - len(df)

        if dropped_count > 0:
            print(f"Dropped {dropped_count} rows due to missing required fields")

        print(f"Preparing to insert {len(df)} records...")

        # Create engine and insert
        # engine = create_engine(connection_string)
        engine = create_engine(
		connection_string,
		connect_args={
			'ssl_disabled': True,
			'auth_plugin': 'mysql_native_password'
		}
	)

        # Insert data
        df.to_sql(
            'domains', 
            engine, 
            if_exists='append', 
            index=False, 
            method='multi',
            chunksize=1000
        )

        print(f"Successfully imported {len(df)} records to database")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

# Usage
if __name__ == "__main__":

    if len(sys.argv) == 2:
        print("Args set as " + sys.argv[1])
        dateselected = validate(sys.argv[1])
    elif len(sys.argv) > 2:
        raise ValueError("Unexpected arguments, expecting 0 or 1")
    else:
        print("Not 1 arg, assuming yesterdays date")
        # get time in ymd format
        dateselected = datetime.today().strftime('%Y-%m-%d')
        # convert from string to datetime object
        dateselected = datetime.strptime(dateselected, '%Y-%m-%d')
        # take off 1 day (puts hours back in)
        dateselected = dateselected - timedelta(1)
        # put back into string for use (and make ymd format)
        dateselected = dateselected.strftime('%Y-%m-%d')
        print(dateselected)

    CSV_FILE = "/share/domains/domains"+dateselected+".csv"  # Update with your CSV file path
    # Update with your actual database credentials
    DB_USER = "XXXXXXXXXXXXXXXX"
    DB_PASSWORD = "XXXXXXXXXXXXXXX"
    DB_HOST = "localhost"
    DB_NAME = "XXXXXXXXXXXXXXXXX"

    CONNECTION_STRING = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

    # make pi requeset
    url = "https://isc.sans.edu/api/recentdomains/"+dateselected+"?json"
    print(url)
    headers = {"User-Agent": "example@example.com"}
    response = requests.get(url,headers=headers)
    domains = response.json()

    # convert to csv
    df = pd.DataFrame(domains)
    df.to_csv(CSV_FILE,index=False)

    # check if file has nothing in it (becuase the data from the API was blank?
    if (os.path.getsize(CSV_FILE)) > 1:
        # add to db
        import_csv_pandas(CSV_FILE, CONNECTION_STRING)
    else:
        print("No data to import to DB")


    # gzip the csv file
    try:
        with open(CSV_FILE,'rb') as inputfile:
            with gzip.open('/share/domains/domains'+dateselected+'.gz','wb') as outputfile:
                shutil.copyfileobj(inputfile,outputfile)
        os.remove(CSV_FILE)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

