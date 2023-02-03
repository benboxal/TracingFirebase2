import qrcode
import streamlit as st
from PIL import Image
from google.cloud import firestore
import pandas as pd
from google.oauth2 import service_account
import json
from datetime import datetime

#---------------------------------------------------------------------------------------------------------------------------------------------

st.set_page_config(
    page_title="Aspen 3D Printing Inventory",
    page_icon="🦷", initial_sidebar_state = "expanded")

#Firestore credentials
key_dict = json.loads(st.secrets['textkey'])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds)

st.title('Printer Maintenance Form')
st.markdown("Select a registered printer and fill out this maintenance form. Select a Wash Unit or ProCure if applicable.")

#---------------------------------------------------------------------------------------------------------------------------------------------

#Password for access to site
def check_password():

    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Enter password to access website", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Enter password to access website", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

#List of all Aspen offices for select box
location_df = pd.read_csv('Lists/AspenLocations.csv')
location = st.selectbox(label="Choose office", options=location_df, key = "LocPSW")

#---------------------------------------------------------------------------------------------------------------------------------------------

if check_password():

    #Check to see if documents exist. These documents mark if certain machines have been registered to an office
    status = db.collection(location+"/Machines/Registration Status").document("Printer Registration")
    users_ref = status.get()
    wu_status = db.collection(location+"/Machines/Registration Status").document("WU Registration")
    wu_users_ref = wu_status.get()
    pc_status = db.collection(location+"/Machines/Registration Status").document("PC Registration")
    pc_users_ref = pc_status.get()

    #If user has previously registered a PRINTER(s) to a location they will appear in a select box
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
    #If no wash units have been registered to a location, a message appears
    else:
        st.text_input("Enter Wash Unit Serial:", value = "Register a Wash Unit on the \"Register Printer\" page", disabled=True, key = "WUSERIAL")
        wu_serial = "None"

    #If user has previously registered a PROCURE(s) to a location they will appear in a select box
    if pc_users_ref.exists:
        pc_users = db.collection(location+"/Machines/ProCures").get()
        pc_users_dict = list(map(lambda x: x.to_dict(), pc_users))
        pc_df = pd.DataFrame(pc_users_dict)
        pc_serials = pc_df['Serial'].tolist()
        pc_serials.insert(0, "None")
        pc_serial = st.selectbox('Select ProCure', (pc_serials), key = "procureserials")
    #If no ProCures have been registered to a location, a message appears
    else:
        st.text_input("Enter serial:", value = "Register a ProCure on the \"Register Printer\" page", disabled=True, key = "PCSERIAl")
        pc_serial = "None"

#---------------------------------------------------------------------------------------------------------------------------------------------
    
    #Form for survey, begins once a printer serial is selected
    if serial != "None":
        with st.form(key = 'maintenanceform', clear_on_submit=True):
            #Date select box, makes date string for Firestore
            date_form = st.date_input('Today\'s date')
            date = str(date_form)

            #Printer maintenance questions
            st.header('Printer ' + serial)
            a1 = st.checkbox('Wipe down hood', key = '1a')
            a2 = st.checkbox('Inspect glass surfaces', key = '1b')
            a3 = st.checkbox('Wipe/clean residual resin (printer base, resin tanks, etc.)', key = '1c')

            #If a wash unit is registered and selected, user can answer questions. Otherwise questions don't appear
            if wu_serial != "None":

                st.header('Wash Unit ' + wu_serial)
                b1 = st.checkbox('Hydrometer check', key = '2a')
                b2 = st.checkbox('Fill level check', key = '2b')
                b3 = st.checkbox('Wash tank inspection', key = '2c')
                b4 = st.checkbox('Wash filter inspection', key = '2d')
                b5 = st.checkbox('External wipedown', key = '2e')

            #Same process as for wash units
            if pc_serial != "None":
                st.header('ProCure ' + pc_serial)
                c1 = st.checkbox('Clean surrounding area and beneath', key = '3a')
                c2 = st.checkbox('Verify bulb function', key = '3b')
                c3 = st.checkbox('Glycerin container assesment', key = '3c')
                c4 = st.checkbox('External wipe down', key = '3d')

            st.header('Feedback or comments')
            comments = st.text_input('(If none leave blank)', key = 'com1')

            survey_submitted = st.form_submit_button()
    else:
        #If office has nothing registered, survey doesn't exist
        survey_submitted = False

#---------------------------------------------------------------------------------------------------------------------------------------------
    
    #Submits survey results to Firestore
    if survey_submitted:
        doc_ref = db.collection(location+"/Survey Results/Printers").document(serial+' '+date)
        doc_ref2 = db.collection(location+"/Survey Results/Wash Units").document(wu_serial+' '+date)
        doc_ref3 = db.collection(location+"/Survey Results/ProCures").document(pc_serial+' '+date)
        
        #Checks if all parameters for PRINTER survey are met
        if a1 and a2 and a3:
            st.success("Survey submiited")
            p_survey_status = True

        #If all parameters aren't met then that printer survey is flagged
        else:
            st.warning("Survey submitted")
            p_survey_status = False

        timestamp = datetime.today()
        #PRINTER SURVEY RESULTS
        doc_ref.set({"AA_ Date": date,
        "AC_ Location": location,
        "AB_ Serial": serial,
        "P_ Clean printer": a1,
        "P_ Inspect glass": a2,
        "P_ Clean up resin": a3,
        "AD_ Printer Status": p_survey_status,
        "Timestamp": timestamp
            })

#---------------------------------------------------------------------------------------------------------------------------------------------            

        #WASH UNIT SURVEY RESULTS
        if wu_serial != "None":
            #If WU questions are being asked, checks to see if all steps completed. If not, WU survey is flagged
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

#---------------------------------------------------------------------------------------------------------------------------------------------

        if pc_serial != "None":
            #If PC questions are being asked, checks to see if all steps completed. If not, PC survey is flagged
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

        #Back up notification if office wasn't chosen
        if location == "Select office":
            st.error("You did not select an office. Please redo the form.")