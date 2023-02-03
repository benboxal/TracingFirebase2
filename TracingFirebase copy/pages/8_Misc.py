import streamlit as st
from google.cloud import firestore
import pandas as pd
import json
from google.oauth2 import service_account
from datetime import datetime, timedelta

st.set_page_config(page_title="Inventory", page_icon="📈")

key_dict = json.loads(st.secrets['textkey'])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds)

loc_df = pd.read_csv('Lists/AspenLocations.csv')
location = st.selectbox("Choose office", (loc_df), index=0)

on_pressed = st.button("Click me")

if on_pressed:

    col_ref = db.collection(location + '/Survey Results/Printers')

    # Get all the documents in the collection
    docs = col_ref.get()

    # Iterate through the documents
    for doc in docs:
        doc_data = doc.to_dict()
        date_str = doc_data['AA_ Date']
        # Convert the date string to a datetime object
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        # Create a new field called "Timestamp" with the converted date
        doc.reference.update({'Timestamp': date_obj})

        st.markdown(date_obj)


on_pressed2 = st.button ("Update time")

if on_pressed2:
    col_ref = db.collection(location + '/Survey Results/Printers')

    # Get all the documents in the collection
    docs = col_ref.get()

    # Iterate through the documents
    for doc in docs:
        doc_data = doc.to_dict()
        timestamp = doc_data['Timestamp']
        # Add six hours to the timestamp
        new_timestamp = timestamp + timedelta(hours=6)
        # Update the document with the new timestamp
        doc.reference.update({'Timestamp': new_timestamp})
