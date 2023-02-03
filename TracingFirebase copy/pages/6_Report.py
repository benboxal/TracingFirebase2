from google.cloud import firestore
import pandas as pd
from datetime import datetime, timedelta
import datetime as dt
import streamlit as st
from dateutil.rrule import rrule, DAILY
import json
from google.oauth2 import service_account
import pytz

#Credentials
key_dict = json.loads(st.secrets['textkey'])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds)

#Location selection from csv list of officers
loc_df = pd.read_csv('Lists/AspenLocations.csv')
location = st.selectbox("Choose office", (loc_df))

# Reference to the collection, location chosen by user
col_ref = db.collection(location + '/Survey Results/Printers')
#Set timezone
timezone = pytz.timezone("America/Chicago")

# Get the start and end dates from the user for report generation then apply timezones
s_date = st.date_input("Select the start date")
start_date = timezone.localize(datetime.combine(s_date, datetime.min.time()))
e_date = st.date_input("Select the end date")
end_date = timezone.localize(datetime.combine(e_date, datetime.min.time()))

#Call collection from Firestore
docs = col_ref.get()

#Create dict
data = {}

#Parse through documents to pull surveys
for doc in docs:
    #Convert Firestore document to dict
    doc_data = doc.to_dict()

    #Collect timestamp values from documents and apply timezone
    timestamp = doc_data['Timestamp'].astimezone(timezone)
    

    # Check if the timestamp is between the specified dates and on weekdays
    if start_date.date() <= timestamp.date() <= end_date.date() and timestamp.weekday() < 5:

        #Identifies the serial from each document
        serial = doc_data['AB_ Serial']

        #If theres no serial (document) then creaty empty array to be appointed
        if serial not in data:
            data[serial] = []

        #Appends document data to dictionary
        data[serial].append(doc_data)


# Create a dataframe for each serial number
dfs = {}
for serial, serial_data in data.items():

    #Create dataframe using serial data
    df = pd.DataFrame(serial_data)


#-----
#This correctly displays the existing data that should exist in the new dataframe, but it is inconsistent.
    st.markdown(serial)
    st.dataframe(df) #WORKING
#-----

    #Range of dates for dataframe index
    date_range = pd.date_range(start=start_date, end=end_date, freq='B')

    #ISSUE HERE - something is wrong with timestamps although they appear consistent throughout code and Firestore
    df = df.set_index('Timestamp').fillna("None")
    df = df.reindex(date_range, method = None)#.reset_index() #, method='bfill').reset_index()



    #Fill blank values
    df['AB_ Serial'] = df['AB_ Serial'].fillna('None')
    df['AA_ Date'] = df['AA_ Date'].fillna("None")
    
    #Clean up dataframe
    sdf = df.reindex(sorted(df.columns), axis=1)
    #sdf = sdf.drop("AB_ Serial", axis = 1)
    sdf = sdf.drop("AC_ Location", axis = 1)
    sdf = sdf.drop("P_ Clean printer", axis = 1)
    sdf = sdf.drop("P_ Clean up resin", axis = 1)
    sdf = sdf.drop("P_ Inspect glass", axis = 1)
    
    sdf = sdf.rename(columns={"AA_ Date":"Date"})
    sdf = sdf.rename(columns={"index":"Timestamp"})
    sdf = sdf.rename(columns={"AD_ Printer Status":"Completion"})

    #Displaying dataframes on Streamlit site
    st.markdown(serial)
    st.dataframe(sdf)


    print(sdf)








#NOTES
    #df1 = df.reindex(date_range)#, method='ffill')
    #df1.update(df)

    #new_df = pd.DataFrame(index = date_range, columns = df.columns)  
    #new_df.index.name = 'Time'
    #new_df.update(df)
    #new_df = new_df.rename(columns={0: 'Time'})
    #df = new_df.combine_first(df)
    #df["Timestamp"].fillna(df.index, inplace=True)
    #df = df.rename_axis("Timestamp", axis=1)
    # Fill in any missing values in the "AD_ Printer Status" column
    #df['AD_ Printer Status'] = df['AD_ Printer Status'].fillna(False)

    #dfs[serial] = df

