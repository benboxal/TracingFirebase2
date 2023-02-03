import streamlit as st
from google.cloud import firestore
import pandas as pd
import json
from google.oauth2 import service_account

st.set_page_config(page_title="Inventory", page_icon="📈")

key_dict = json.loads(st.secrets['textkey'])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds)

st.title('3D Printing Inventory')


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
            "Enter password to view printing inventory", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Enter password to view printing inventory", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

if check_password():
	st.subheader('Check Location Inventory')
	
	with st.form(key = 'QR Form', clear_on_submit=False):
		
		loc_df = pd.read_csv('Lists/AspenLocations.csv')
		address = st.selectbox("Choose office", (loc_df))
		choice = st.selectbox('Choose item',('Printing Items','Machines','All Current Inventory','All Discarded Inventory'))
		qr_submitted = st.form_submit_button()

	item = "test"



	if qr_submitted:
		if choice == "Machines":
			item = "Machines"
		elif choice == "Printing Items":
			item = "Printing Items"
		elif choice == "All Current Inventory" or choice == "All Discarded Inventory":
			item = "NA"



	if qr_submitted and item == "Machines":

		#Displays whatever user chooses
		col_printer = list(db.collection(address + "/Machines/Printers").stream())
		col_wu = list(db.collection(address + "/Machines/Wash Units").stream())
		col_pc = list(db.collection(address + "/Machines/ProCures").stream())
		#Converts list to dictionary
		printer_dict = list(map(lambda x: x.to_dict(), col_printer))
		wu_dict = list(map(lambda x: x.to_dict(), col_wu))
		pc_dict = list(map(lambda x: x.to_dict(), col_pc))
		#Converts dictionaries to dataframes
		printer_df = pd.DataFrame(printer_dict)
		wu_df = pd.DataFrame(wu_dict)
		pc_df = pd.DataFrame(pc_dict)
		#Displays dataframes with titles
		st.header('Printers at Location')
		st.dataframe(printer_df)
		st.header("Wash Units at Location")
		st.dataframe(wu_df)
		st.header("ProCures at Location")
		st.dataframe(pc_df)

	elif qr_submitted and item == "Printing Items":

			col_resin = list(db.collection(address + "/Printing Items/Resin").stream())
			col_tray = list(db.collection(address + "/Printing Items/Resin Trays").stream())
			col_ipa = list(db.collection(address + "/Printing Items/IPA").stream())
			tray_dict = list(map(lambda x: x.to_dict(), col_tray))
			resin_dict = list(map(lambda x: x.to_dict(), col_resin))
			ipa_dict = list(map(lambda x: x.to_dict(), col_ipa))
			tray_df = pd.DataFrame(tray_dict)
			resin_df = pd.DataFrame(resin_dict)
			ipa_df = pd.DataFrame(ipa_dict)
			st.header('Resin Tray Inventory')
			st.dataframe(tray_df)
			st.header('Resin Inventory')
			st.dataframe(resin_df)
			st.header('IPA Inventory')
			st.dataframe(ipa_df)


	elif qr_submitted and choice == 'All Current Inventory':
			
			st.header("Inventory at "+address)
			st.header(" ")
			
			#Gather current inventory from firebase
			col_printer = list(db.collection(address + "/Machines/Printers").stream())
			col_wu = list(db.collection(address + "/Machines/Wash Units").stream())
			col_pc = list(db.collection(address + "/Machines/ProCures").stream())

			col_resin = list(db.collection(address + "/Printing Items/Resin").stream())
			col_tray = list(db.collection(address + "/Printing Items/Resin Trays").stream())
			col_ipa = list(db.collection(address + "/Printing Items/IPA").stream())

			#Converts list to dictionary
			printer_dict = list(map(lambda x: x.to_dict(), col_printer))
			wu_dict = list(map(lambda x: x.to_dict(), col_wu))
			pc_dict = list(map(lambda x: x.to_dict(), col_pc))

			tray_dict = list(map(lambda x: x.to_dict(), col_tray))
			resin_dict = list(map(lambda x: x.to_dict(), col_resin))
			ipa_dict = list(map(lambda x: x.to_dict(), col_ipa))

			#Converts dictionaries to dataframes
			printer_df = pd.DataFrame(printer_dict)
			wu_df = pd.DataFrame(wu_dict)
			pc_df = pd.DataFrame(pc_dict)

			tray_df = pd.DataFrame(tray_dict)
			resin_df = pd.DataFrame(resin_dict)
			ipa_df = pd.DataFrame(ipa_dict)

			#Displays dataframes with titles
			st.header('Printers at Location')
			st.dataframe(printer_df)

			st.header("Wash Units at Location")
			st.dataframe(wu_df)

			st.header("ProCures at Location")
			st.dataframe(pc_df)

			st.header('Resin Tray Inventory')
			st.dataframe(tray_df)

			st.header('Resin Inventory')
			st.dataframe(resin_df)

			st.header('IPA Inventory')
			st.dataframe(ipa_df)


	elif qr_submitted and choice == 'All Discarded Inventory':

			st.header("Inventory at "+address)
			st.header(" ")
			
			#Gather current inventory from firebase

			col_resin = list(db.collection(address + "/Discarded Printing Items/Discarded Resin").stream())
			col_tray = list(db.collection(address + "/Discarded Printing Items/Discarded Resin Trays").stream())
			col_ipa = list(db.collection(address + "/Discarded Printing Items/Discarded IPA").stream())

			tray_dict = list(map(lambda x: x.to_dict(), col_tray))
			resin_dict = list(map(lambda x: x.to_dict(), col_resin))
			ipa_dict = list(map(lambda x: x.to_dict(), col_ipa))

			tray_df = pd.DataFrame(tray_dict)
			resin_df = pd.DataFrame(resin_dict)
			ipa_df = pd.DataFrame(ipa_dict)

			#Displays dataframes with titles
			st.header('Resin Tray Inventory')
			st.dataframe(tray_df)

			st.header('Resin Inventory')
			st.dataframe(resin_df)

			st.header('IPA Inventory')
			st.dataframe(ipa_df)
			
	elif qr_submitted and choice == "Survey Results":
			
			survey_results = list(db.collection("Streamlit/"+address+"/Survey Results").stream())
			surv_dict = list(map(lambda x: x.to_dict(), survey_results))		      
			df1 = pd.DataFrame(surv_dict)
			df1.sort_index(axis=1, inplace=True)
			st.dataframe(df1)
			
			users = list(db.collection("Streamlit/"+address+"/"+choice).stream())

			
			
			
			
			
			
			
			
			
			
