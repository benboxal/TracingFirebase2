import qrcode
import streamlit as st
from PIL import Image
from google.cloud import firestore
import pandas as pd
import json
from google.oauth2 import service_account

#---------------------------------------------------------------------------------------------------------------------------------------------

st.set_page_config(page_title="Machine Registration", page_icon="🪥")
key_dict = json.loads(st.secrets['textkey'])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds)

st.title('SprintRay Registration')
loc_df = pd.read_csv('Lists/AspenLocations.csv')
location = st.selectbox("Choose office", (loc_df), index=0)

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
            "Enter password to register a printer", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Enter password to view register a printer", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

#---------------------------------------------------------------------------------------------------------------------------------------------

if check_password():
    #Three tabs for registering different machines
    tab1, tab2, tab3 = st.tabs(['Register a Printer', 'Register a Wash Unit', 'Register a ProCure'])

#---------------------------------------------------------------------------------------------------------------------------------------------

    with tab1:
        st.subheader('Register a Printer')
        st.markdown('Enter printer serial register a printer and create QR code to easily return to this site')

        with st.form(key = 'QR Form', clear_on_submit=True):
            #Defines fields for Firestore
            serial = st.text_input('Printer Serial:', 'P95-')
            model = st.radio('Printer model', [("Pro 95"),("Pro 95s"),("Pro 55"), ("Pro 55s")], index=0, horizontal=True)
            date = str(st.date_input('Today\'s date: '))
            make_qr = st.checkbox("Generate QR", key = "Make_QR")
            printer_submitted = st.form_submit_button()

            data = ('https://aspenone.streamlit.app//?address=' + location)


        if printer_submitted:
            if make_qr:
                #Creates QR code if prompted. Brings user to site and uses query params for autofilling location
                img = qrcode.make(data)
                newcode = img.save("qr.png")
                st.image("qr.png")
                st.text('QR Code generated for printer ' + serial + ' at ' + location)
                st.subheader('Print this QR code and attach it to 3D printer')

            #Firestore document
            doc_ref = db.collection(location+"/Machines/Printers").document(serial)
            doc_ref.set({
                    "Serial": serial,
                    "Model": model,
                    "Date registered": date,
                })

            #Firestore document, marks that Printers exist at a location
            doc2_ref = db.collection(location+"/Machines/Registration Status").document("Printer Registration")
            doc2_ref.set({"Status": True})

            st.success("Printer Registrated!")

#---------------------------------------------------------------------------------------------------------------------------------------------

    with tab2:
        st.subheader('Register a Wash Unit')

        #Form for wash unit registration
        with st.form(key = 'WU_reg', clear_on_submit=True):
            date = str(st.date_input('Today\'s date: '))
            wu_serial = st.text_input('Enter serial number','PWD-', key = 'WU_serial')
            wu_form_submitted = st.form_submit_button()

        #Firestore document
        if wu_form_submitted:
            wu_ref = db.collection(location+"/Machines/Wash Units").document('Wash Unit ' + wu_serial)
            wu_ref.set({
                    "Serial": wu_serial,
                    "Date registered": date,
                })
            #Firestore document that marks WU exists at location
            wu2_ref = db.collection(location+"/Machines/Registration Status").document("WU Registration")
            wu2_ref.set({"Status": True})

            st.success('Pro Wash/Dry Registered')

#---------------------------------------------------------------------------------------------------------------------------------------------

    with tab3:
        st.subheader('Register a ProCure')

        #Form for ProCure registration
        with st.form(key = 'PC_reg', clear_on_submit=True):
            date = str(st.date_input('Today\'s date: '))
            pc_version = st.radio('Model', ('ProCure 2', 'ProCure 1'))
            pc_serial = st.text_input('Enter serial number', 'PC', key = 'PC_serial')
            pc_form_submitted = st.form_submit_button()

        #Firestore document for ProCure
        if pc_form_submitted:
            pc_ref = db.collection(location+"/Machines/ProCures").document(pc_version + ' ' + pc_serial)
            pc_ref.set({
                    "Serial": pc_serial,
                    "Model": pc_version,
                    "Date registered": date,
                })

            #Firestore document that marks PC exists at location
            pc2_ref = db.collection(location+"/Machines/Registration Status").document("PC Registration")
            pc2_ref.set({"Status": True})
            st.success(pc_version + ' Registered')

#---------------------------------------------------------------------------------------------------------------------------------------------

