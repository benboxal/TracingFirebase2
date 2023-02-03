import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
import json
import pandas as pd
from fastapi import FastAPI
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

key_dict = json.loads(st.secrets['textkey'])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds)

app = FastAPI()


@app.post("/submit-survey-results")
async def submit_survey_results(data: dict):
    # Process the survey results here
    ...

service = build('firestore', 'v1', credentials=creds)

# Define the document to be created
document = service.documents().create(
    parent='projects/your-project-id/databases/(default)/documents/surveys',
    body=data
).execute()
print(F'Created document with ID: {document.get("name")}')





# def upload_survey():

