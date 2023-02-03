import streamlit as st
from google.cloud import firestore
import pandas as pd
from google.oauth2 import service_account
import json

location_df = pd.read_csv('AspenLocations.csv')
int_location = st.selectbox(label="Choose office", options=location_df, key = "LocPSW")

key_dict = json.loads(st.secrets['textkey'])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds)

st.title('Printer Maintenance Form')
st.markdown("Select a registered printer and fill out this maintenance form. Select a Wash Unit or ProCure if applicable.")
if int_location:
    location = int_location
else:
    location = st.selectbox("Choose location", location_df)

status = db.collection(location+"/Machines/Registration Status").document("Printer Registration")
users_ref = status.get()
wu_status = db.collection(location+"/Machines/Registration Status").document("WU Registration")
wu_users_ref = wu_status.get()
pc_status = db.collection(location+"/Machines/Registration Status").document("PC Registration")
pc_users_ref = pc_status.get()

#If user has previously registered a printer(s) to a location they will appear in a select box
if users_ref.exists:
    users = db.collection(location+"/Machines/Printers").get()
    users_dict = list(map(lambda x: x.to_dict(), users))
    df = pd.DataFrame(users_dict)
    serials = df['Serial'].tolist()
    serial = st.selectbox('Select Printer', serials)
#If no printers have been registered to a location, a message appears
else:
    st.text_input("Enter serial:", value = "Register a Printer on the \"Register Printer\" page", disabled=True, key = "printer_serial")
    serial = "None"

#If user has previously registered a WASH UNIT(s) to a location they will appear in a select box
if wu_users_ref.exists:
    wu_users = db.collection(location+"/Machines/Wash Units").get()
    wu_users_dict = list(map(lambda x: x.to_dict(), wu_users))
    wu_df = pd.DataFrame(wu_users_dict)
    wu_serials = wu_df['Serial'].tolist()
    wu_serials.insert(0, "None")
    wu_serial = st.selectbox('Select Wash Unit', (wu_serials), key = "washserials")

else:
    st.text_input("Enter Wash Unit Serial:", value = "Register a Wash Unit on the \"Register Printer\" page", disabled=True, key = "WUSERIAL")
    wu_serial = "None"

#If user has previously registered a PROCURE(s) to a location they will appear in a select box
if pc_users_ref.exists:
    pc_users = db.collection(location+"/Machines/ProCures").get()
    pc_users_dict = list(map(lambda x: x.to_dict(), pc_users))
    pc_df = pd.DataFrame(pc_users_dict)
    pc_serials = pc_df['Serial'].tolist()
    pc_serial = st.selectbox('Select ProCure', (pc_serials), key = "procureserials")

else:
    st.text_input("Enter serial:", value = "Register a ProCure on the \"Register Printer\" page", disabled=True, key = "PCSERIAl")
    pc_serial = "None"

if serial != "None":
  with st.form(key = 'maintenanceform', clear_on_submit=True):

    date_form = st.date_input('Today\'s date')
    date = str(date_form)

    st.header('Printer')
    a1 = st.checkbox( label = 'Wipe down hood', key = '1a')
    a2 = st.checkbox( label = 'Inspect glass surfaces', key = '1b')
    a3 = st.checkbox( label = 'Wipe/clean residual resin (printer base, resin tanks, etc.', key = '1c')

    if wu_serial != "None":

      st.header('Wash Unit')
      b1 = st.checkbox('Hydrometer check', key = '2a')
      b2 = st.checkbox('Fill level check', key = '2b')
      b3 = st.checkbox('Wash tank inspection', key = '2c')
      b4 = st.checkbox('Wash filter inspection', key = '2d')
      b5 = st.checkbox('External wipedown', key = '2e')

    if pc_serial != "None":
      st.header('ProCure')
      c1 = st.checkbox('Clean surrounding area and beneath', key = '3a')
      c2 = st.checkbox('Verify bulb function', key = '3b')
      c3 = st.checkbox('Glycerin container assesment', key = '3c')
      c4 = st.checkbox('External wipe down', key = '3d')

    st.header('Feedback or comments (If not leave blank)')
    comments = st.text_input(' ', key = 'com1')

    survey_submitted = st.form_submit_button()

  #Submits survey results to Firestore
  if survey_submitted:
    doc_ref = db.collection(location+"/Survey Results/Printers").document(serial+' '+date)
    doc_ref2 = db.collection(location+"/Survey Results/Wash Units").document(wu_serial+' '+date)
    doc_ref3 = db.collection(location+"/Survey Results/ProCures").document(pc_serial+' '+date)
    
    #Checks if all parameters for survey are met
    if a1 and a2 and a3:
        st.success("Survey submiited")
        p_survey_status = True

    #If all parameters aren't met then the survey is flagged
    else:
        st.warning("Survey submitted")
        p_survey_status = False

    #PRINTER SURVEY RESULTS
    doc_ref.set({"AA_ Date": date,
    "AC_ Location": location,
    "AB_ Serial": serial,
    "P_ Clean printer": a1,
    "P_ Inspect glass": a2,
    "P_ Clean up resin": a3,
    "AD_ Printer Status": p_survey_status
        })

    #WASH UNIT SURVEY RESULTS
    if wu_serial != "None":
        if b1 and b2 and b3 and b4 and b5:
            wu_survey_status = True
        else:
            wu_survey_status = False

        doc_ref2.set({"AA_ Date": date,
        "AC_ Location": location,
        "AB_ Serial": serial,
        "WU_ Hyrdometer": b1,
        "WU_ IPA Level": b2,
        "WU_ Tank Inspection": b3,
        "WU_ Filter Inspection": b4,
        "WU_ Wipe Down": b5,
        "AE_ WU Status": wu_survey_status,
            })

    if pc_serial != "None":
        if c1 and c2 and c3 and c4:
            pc_survey_status = True
        else:
            pc_survey_status = False

        #PROCURE SURVEY RESULTS
        doc_ref3.set({"AA_ Date": date,
        "AC_ Location": location,
        "AB_ Serial": serial,
        "PC_ Clean Inside": c1,
        "PC_ Check bulbs": c2,
        "PC_ Glycerin": c3,
        "PC_ External Wipe Down": c4,
        "AF_ PC Status": pc_survey_status
            })

    if location == "Select office":
        st.error("You did not select an office. Please redo the form.")