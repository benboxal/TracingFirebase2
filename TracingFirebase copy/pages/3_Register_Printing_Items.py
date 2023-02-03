import qrcode
import streamlit as st
from PIL import Image
from google.cloud import firestore
import pandas as pd
from google.oauth2 import service_account
import json

#---------------------------------------------------------------------------------------------------------------------------------------------

st.set_page_config(
    page_title="Aspen 3D Printing Inventory",
    page_icon="🦷", initial_sidebar_state = "expanded")

#CSV files for location list and resins per brand
loc_df = pd.read_csv('Lists/AspenLocations.csv')
dencta_mat = pd.read_csv('Lists/DENCTA_matlist.csv')
pro3_mat = pd.read_csv('Lists/Pro3Dure_matlist.csv')
sprintray_mat = pd.read_csv('Lists/SprintRay_matlist.csv')
lucitone_mat = pd.read_csv('Lists/Lucitone_matlist.csv')

#Connects to firebase
key_dict = json.loads(st.secrets['textkey'])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds)

st.title('Aspen 3D Printing Inventory')
st.markdown('Register printing items on this page. Use the menu in the top left to register a printer and create a QR code, or to view location inventory.')


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
    
int_location = st.selectbox("Choose office", (loc_df), key = "LocPSW")
location = int_location




#User selects office location and this applies throughout page

if check_password():
    tab2, tab3, tab4 = st.tabs(['Register resin tray', 'Register resin', 'Register IPA'])

#---------------------------------------------------------------------------------------------------------------------------------------------

    query_params = st.experimental_get_query_params()
    serial_qr = "P95-"
    if query_params:      
            test1 = query_params['address']
            try:
                test2 = query_params['serial']
            except:
                test2='Err'

            location_qr = (test1[0])
            serial_qr = (test2[0])

#---------------------------------------------------------------------------------------------------------------------------------------------

    #Resin Tray Registration   
    with tab2:
        
        st.title('Resin Tray Registration')

        st.text(type(location))
        st.text(location == 'Select office')
        st.text(len(location))
        if location == "Select office ":
            st.warning("Choose an office!")
        st.text(location)

        #User chooses if they are registering a tray or throwing one out
        cond = st.radio("Select one", ('Registering a new resin tray','Discarding an old tray'), index = 0)
        if cond == 'Registering a new resin tray':
            new = True
            trash = False
        elif cond == 'Discarding an old tray':
            trash = True
            new = False

        #If tray is new, user registers information
        if new:
            tresin_brand = st.selectbox('Brand of resin in tray', ("Choose brand","SprintRay","DENTCA","Pro3Dure","Lucitone"))
            if tresin_brand == "Choose brand":
                st.error("Choose a resin brand")

            condition = 'In Use'

            with st.form(key = 'Resin Tray Form', clear_on_submit=True):

                tray_address = int_location      
                tray_date = str(st.date_input('Today\'s date: '))
                tray_serial = st.text_input('Resin Tray Serial:', ' ')
                
                #Select resin brand. Updates selectbox inside form to materials from brand
                if tresin_brand == "SprintRay":
                    tray_material = st.selectbox("Resin type in tray", (sprintray_mat), key = "traysprint")
                elif tresin_brand == "DENTCA":
                    tray_material = st.selectbox("Resin type in tray", (dencta_mat), key = "traydentca")
                elif tresin_brand == "Pro3Dure":
                    tray_material = st.selectbox("Resin type in tray", (pro3_mat), key = "traypro3")
                elif tresin_brand == "Lucitone":
                    tray_material = st.selectbox("Resin type in tray", (lucitone_mat), key = "traypro3")
                
                new_tray_form_submitted = st.form_submit_button()

            if new_tray_form_submitted:
                doc_ref = db.collection(tray_address+"/Printing Items/Resin Trays").document(tray_serial)
                doc_ref.set({
                    "Serial": tray_serial,
                    "Date Registered": tray_date,
                    "Condition": condition,
                    "Material": tresin_brand + ' ' + tray_material
                })
                #Creates document in Firebase with tray information
                doc2_ref = db.collection(tray_address+"/Printing Items/Item Status").document("Tray Registration")
                doc2_ref.set({"Status": True})

                st.success("Resin tray " + tray_serial +  " registered")

#---------------------------------------------------------------------------------------------------------------------------------------------
        
        #If user is throwing a tray out, site uses their location to show previously registered trays in a drop box
        elif trash:

            with st.form(key = "Old Resin Tray", clear_on_submit = True):
                status = db.collection("Streamlit/"+location+"/Registration Status").document("Printer Registration")
                users_ref = status.get()
                
                condition = 'Discarded'
                tray_address = int_location
                disp_date = str(st.date_input('Today\'s date: '))

                #Looks for status that trays have been registered and exist in Firestore
                tray_status = db.collection(location+"/Printing Items/Item Status").document("Tray Registration")
                ttray_ref = status.get()
            
                #If trays exist, location is used to display inventory of registered trays in dropbox
                if ttray_ref.exists:
                    try:
                        trays = db.collection(location+"/Printing Items/Resin Trays").get()
                        trays_dict = list(map(lambda x: x.to_dict(), trays))
                        df = pd.DataFrame(trays_dict)
                        tray_serials = df['Serial'].tolist()
                        tray_serial = st.selectbox('Choose tray', tray_serials)
                    except:
                        st.error("No trays are currently registered to this location")

                else:
                    st.error("No trays are currently registered to this location")

                old_tray_form_submitted = st.form_submit_button()

            #Places tray information into discarded inventory. Keeps all information and adds date of disposal
            if old_tray_form_submitted:

                users_ref = db.collection(tray_address+"/Printing Items/Resin Trays").document(tray_serial)
                doc_snapshot = users_ref.get()
                reg_date = doc_snapshot.get("`Date Registered`")
                tray_material = doc_snapshot.get("Material")

                doc_ref2 = db.collection(tray_address+"/Discarded Printing Items/Discarded Resin Trays").document(tray_serial)
                doc_ref2.set({
                    "Serial": tray_serial,
                    "Date Registered": reg_date,
                    "Disposal Date": disp_date,
                    "Material": tray_material,
                    "Condition": condition
                })
                st.warning("This item was discarded!")
                
                #Deletes document from live inventory after it is copied into discarded inventory
                db.collection(tray_address+"/Printing Items/Printer Trays").document(tray_serial).delete()

        pressed = st.button("View current inventory at " + location, key = 'tray inventory')
        if pressed:
            
            users = list(db.collection(location+"/Printing Items/Resin Trays").stream())

            users_dict = list(map(lambda x: x.to_dict(), users))
            df = pd.DataFrame(users_dict)
            dft2 = df.reindex(sorted(df.columns), axis=1)
            st.header("Resin at "+location)
            st.dataframe(dft2)

#---------------------------------------------------------------------------------------------------------------------------------------------

    #Resin bottle registration
    with tab3:
        st.title('Resin Registration')
        resin_disposal = False
        new = False
        cond = st.radio("Select one", ('Registering new resin bottle','Discarding resin bottle','Edit a resin bottle'), index = 0)
        if cond == 'Registering new resin bottle':
            new = True
            resin_disposal = False

            with st.expander("Where to find information"):
                image1 = Image.open('Images/ResinInfo.png')
                image2 = Image.open('Images/ResinInfo2.png')
                image3 = Image.open('Images/ResinInfo3.png')
                st.image(image1)
                st.image(image2)
                st.image(image3)
                #Reference images for finding resin info

        elif cond == 'Discarding resin bottle':
            resin_disposal = True
            new = False

        #New resin registration
        if new:

            #Choose resin  brand
            resin_brand = st.selectbox('Resin Brand', ("Choose brand","SprintRay","DENTCA","Pro3Dure","Lucitone"), key = "Trayresinbox")
            if resin_brand == ("Choose brand"):
                st.error("Select resin brand")

            #Form for new resin
            with st.form("key = 'New_Resin"):
                resin_address = int_location
                resin_condition = "In Use"
                
                resin_date = str(st.date_input('Today\'s Date'))

                #Depending on brand selected, displays resin options
                if resin_brand == "SprintRay":
                    resin_type = st.selectbox(resin_brand + " Resin Type", (sprintray_mat), key = "sprint")
                elif resin_brand == "DENTCA":
                    resin_type = st.selectbox(resin_brand + " Resin Type", (dencta_mat), key = "dentca")
                elif resin_brand == "Pro3Dure":
                    resin_type = st.selectbox(resin_brand + " Resin Type", (pro3_mat), key = "pro3")
                elif resin_brand == "Lucitone":
                    resin_type = st.selectbox(resin_brand + " Resin Type", (lucitone_mat), key = "lucitone")
                

                resin_lot = st.text_input("Enter LOT", key = 'new_resin_lot')
                resin_exp = st.text_input("Enter expiration date (YYYY-MM-DD)")
                resin_quan = (str(st.number_input('Quantity:', min_value=1)))

                new_resin_submitted = st.form_submit_button()

            #When survey submitted information is uploaded to Firestore
            if new_resin_submitted:

                doc_ref = db.collection(resin_address+"/Printing Items/Resin").document(resin_brand+' '+resin_type+' '+resin_lot)
                dr2 = doc_ref.get()
                
                if dr2.exists:
                    quantity = dr2.get('Quantity')
                    #Math
                    int_intial = int(quantity)
                    int_resin_quan = int(resin_quan)
                    updated_quantity = str(int_intial+int_resin_quan)

                    doc_ref.update({"Quantity":updated_quantity})
                    st.success("Resin added")

                else:
                    doc_ref.set({
                        "Exp": resin_exp,
                        "Brand": resin_brand,
                        "Material": resin_type,
                        "LOT": resin_lot,
                        "Date registered": resin_date,
                        "Status": resin_condition,
                        "Quantity": resin_quan
                    })
                    st.success("Resin " + resin_lot + " registered")    

                    #Resin Machines updated to show resins exist in live inventory
                    doc2_ref = db.collection(resin_address+"/Printing Items/Item Status").document("Resin Registration")
                    doc2_ref.set({"Status": True})

        
#---------------------------------------------------------------------------------------------------------------------------------------------

        #Resin disposal form
        if resin_disposal:

            with st.form(key = 'Old_Resin', clear_on_submit = True):

                condition = 'Discarded'
                disp_date = str(st.date_input('Today\'s date: '))

                status = db.collection(location+"/Printing Items/Item Status").document("Resin Registration")
                users_ref = status.get()
                try:
                    if users_ref.exists:
                        users = db.collection(location+"/Printing Items/Resin").get()
                        resin_dict = list(map(lambda x: x.to_dict(), users))
                        df = pd.DataFrame(resin_dict)
                        mat_resin_docs = df['Material'].tolist()
                        lot_resin_docs = df['LOT'].tolist()
                        bra_resin_docs = df['Brand'].tolist()
                        qua_resin_docs = df['Quantity'].tolist()

                        #Creates document IDs
                        doc_id = [x + ' ' + y for x, y in zip(mat_resin_docs, lot_resin_docs)]

                        #Assembles document IDs from live inventory to be selected in drop box
                        result = [z + ' ' + x + ' ' + y for x, y, z in zip(mat_resin_docs, lot_resin_docs, bra_resin_docs)]
                        sorted_result = sorted(result)
                        serial = st.selectbox('Select bottle', sorted_result)

                        quan_trash = str(st.number_input('Quantity being diposed:', min_value=1))
                    else:
                        st.error("There are no resin bottles registered to this location")    
                except:
                    st.error("No resin bottles are currently registered to this location")

                old_resin_submitted = st.form_submit_button()

                #Grabs information from selected resin bottle. Copies this information for the discarded resin collections
                if old_resin_submitted:
                    users_ref = db.collection(location+"/Printing Items/Resin").document(serial)
                    doc_snapshot = users_ref.get()
                    reg_date = doc_snapshot.get("`Date registered`")
                    res_exp = doc_snapshot.get("Exp")
                    res_bra = doc_snapshot.get("Brand")
                    res_mat = doc_snapshot.get("Material")
                    res_lot = doc_snapshot.get("LOT")
                    res_quan = doc_snapshot.get("Quantity")
                    tray_material = doc_snapshot.get("Material")

                    #MATH
                    #This section keeps quanities of live and discarded inventory accurate
                    int_current = int(res_quan)
                    int_trash = int(quan_trash)
                    str_updated = str(int_current - int_trash)

                    disp = db.collection(location+"/Discarded Printing Items/Discarded Resins").document(serial)
                    disp_ref = disp.get()

                    if disp_ref.exists:
                        current_disp = disp_ref.get('Quantity')
                        #int_trash = int(quan_trash)
                        int_trash_intial = int(current_disp)
                        new_amount = str(int_trash + int_trash_intial)

                        disp.update({'Quantity': new_amount})

                    else:
                        #Information uploaded to discarded inventory on Firestore
                        doc_ref2 = db.collection(location+"/Discarded Printing Items/Discarded Resins").document(serial)
                        doc_ref2.set({
                            "Brand": res_bra,
                            "Material": res_mat,
                            "Date Registered": reg_date,
                            "Disposal Date": disp_date,
                            "LOT": res_lot,
                            "EXP": res_exp,
                            "Quantity": quan_trash
                        })
                        st.warning("This item was discarded!")

                    #If there are zero containers of a resin left in the live inventory, the document is delted
                    int_check = int(str_updated)

                    if int_check <= 0:
                        db.collection(location+"/Printing Items/Resin").document(serial).delete()
                    
                    #If there are more than zero containers left, the live quanitity is updated
                    else:
                        users_ref.update({'Quantity':str_updated})
        #Button to view inventory
        pressed = st.button("View current inventory at " + location, key = 'resin inventory')
        if pressed:
        
            users = list(db.collection(location+"/Printing Items/Resin").stream())

            users_dict = list(map(lambda x: x.to_dict(), users))
            df = pd.DataFrame(users_dict)
            dft2 = df.reindex(sorted(df.columns), axis=1)
            st.header("Resin at "+location)
            st.dataframe(dft2)

#---------------------------------------------------------------------------------------------------------------------------------------------

        if cond == "Edit a resin bottle":
            status = db.collection(location+"/Printing Items/Item Status").document("Resin Registration")
            users_ref = status.get()
            try:
                if users_ref.exists:
                    users = db.collection(location+"/Printing Items/Resin").get()
                    resin_dict = list(map(lambda x: x.to_dict(), users))
                    df = pd.DataFrame(resin_dict)
                    mat_resin_docs = df['Material'].tolist()
                    lot_resin_docs = df['LOT'].tolist()
                    bra_resin_docs = df['Brand'].tolist()
                    qua_resin_docs = df['Quantity'].tolist()
                    exp_resin_docs = df['Exp'].tolist()

                    #Creates document IDs
                    doc_id = [x + ' ' + y for x, y in zip(mat_resin_docs, lot_resin_docs)]
                    #lots = [l for l in zip(lot_resin_docs)]
                    #slots = sorted(lots)

                    #Assembles document IDs from live inventory to be selected in drop box
                    #result = [z + ' ' + x + ' ' + y for x, y, z in zip(mat_resin_docs, lot_resin_docs, bra_resin_docs)]
                    for x, y, z in zip(mat_resin_docs, lot_resin_docs, bra_resin_docs):
                        var_x = x
                        var_y = y
                        var_z = z
                        result = [z + ' ' + x + ' ' + y for x, y, z in zip(mat_resin_docs, lot_resin_docs, bra_resin_docs)]

                    
                    sorted_result = sorted(result)
                    #serial = st.selectbox('Select bottle to edit', sorted_result)

                    zipped_values = list(zip(mat_resin_docs, lot_resin_docs, bra_resin_docs, exp_resin_docs, qua_resin_docs))

                    # Create the selectbox
                    selected_value = st.selectbox("Select a bottle to edit", zipped_values)

                    # Unpack the selected tuple
                    var_x, var_y, var_z, var_w, var_a = selected_value

                    # Display the selected values
                    #st.write("Selected value:")
                    #st.write("var_x: mat", var_x)
                    #st.write("var_y: lot", var_y)
                    #st.write("var_z: brand", var_z)
                    #st.write("var_w: exp", var_w)

                    edit_ref = db.collection(location + "/Printing Items/Resin").document(var_z + " " + var_x + " " + var_y)


                else:
                        st.error("There are no resin bottles registered to this location")    
            

                with st.form(key = 'edit_resin', clear_on_submit = True):

                    condition = 'edit'
                    edit_date = str(st.date_input('Today\'s date: '))

                    st.text_input("Resin Brand", var_z, disabled=True, key="editbrand")

                    if var_z == "SprintRay":
                        edit_mat = st.selectbox("Resin Type", (sprintray_mat), key = "sprint")#, index = var_x)
                    elif var_z == "DENTCA":
                        edit_mat = st.selectbox("Resin Type", (dencta_mat), key = "dentca")
                    elif var_z == "Pro3Dure":
                        edit_mat = st.selectbox("Resin Type", (pro3_mat), key = "pro3")
                    elif var_z == "Lucitone":
                        edit_mat = st.selectbox("Resin Type", (lucitone_mat), key = "lucitone")

                    edit_lot = st.text_input("LOT Number", var_y, key="editlot")
                    
                    edit_exp = st.text_input("Expiration date", var_w, key = "editexp")

                    submit_edit = st.form_submit_button()

                if submit_edit:
                    
                    resin_condition = "In use"

                    doc_ref_edit = db.collection(location+"/Printing Items/Resin").document(var_z+' '+edit_mat+' '+edit_lot)
                    doc_ref_edit.set({
                        "Exp": edit_exp,
                        "Brand": var_z,
                        "Material": edit_mat,
                        "LOT": edit_lot,
                        "Date registered": edit_date,
                        "Status": resin_condition,
                        "Quantity": var_a
                    })
                    st.success("Resin " + edit_lot + " edited")  

                    edit_ref = db.collection(location + "/Printing Items/Resin").document(var_z + " " + var_x + " " + var_y).delete()
                    #if edit_ref.exists():
                    #edit_ref.update({"LOT":edit_lot})
                    #edit_ref.update({"Material":edit_mat})
                    #edit_ref.update({"Exp":edit_exp})
            except:
                st.error("No resin bottles are currently registered to this location")




                    






#---------------------------------------------------------------------------------------------------------------------------------------------

#IPA bottle registration
    with tab4:
        st.title('IPA Registration')

        cond = st.radio("Select one", ('Registering new IPA bottle','Discarding IPA bottle'), index = 0)
        if cond == 'Registering new IPA bottle':
            new = True
            ipa_disposal = False

        elif cond == 'Discarding IPA bottle':
            ipa_disposal = True
            new = False

        #New IPA registration
        if new:

            #Form for new IPA
            with st.form("key = 'New_IPA"):
                
                ipa_date = str(st.date_input('Today\'s Date'))
                ipa_brand = st.text_input('IPA Brand', key='ipa_brand')
                ipa_lot = st.text_input("Enter LOT", key = 'new_ipa_lot')
                ipa_exp = st.text_input("Enter expiration date (YYYY-MM-DD)")
                ipa_quan = (str(st.number_input('Quantity:', min_value=1)))

                new_ipa_submitted = st.form_submit_button()

            #When survey submitted information is uploaded to Firestore
            if new_ipa_submitted:
                doc_ref = db.collection(location+"/Printing Items/IPA").document(ipa_brand+' '+ipa_lot)
                doc_ref.set({
                    "Exp": ipa_exp,
                    "Brand": ipa_brand,
                    "LOT": ipa_lot,
                    "Date registered": ipa_date,
                    "Quantity": ipa_quan
                })
                st.success("IPA " + ipa_brand + ' ' + ipa_lot + " registered")    

                #IPA  updated to show IPA bottles exist in live inventory
                doc2_ref = db.collection(location+"/Printing Items/Item Status").document("IPA Registration")
                doc2_ref.set({"Status": True})

#---------------------------------------------------------------------------------------------------------------------------------------------

        #IPA disposal form
        if ipa_disposal:

            with st.form(key = 'old_ipa', clear_on_submit = True):

                disp_date = str(st.date_input('Today\'s date: '))

                status = db.collection(location+"/Printing Items/Item Status").document("IPA Registration")
                users_ref = status.get()
                try:
                    if users_ref.exists:
                        users = db.collection(location+"/Printing Items/IPA").get()
                        ipa_dict = list(map(lambda x: x.to_dict(), users))
                        df = pd.DataFrame(ipa_dict)
                        lot_ipa_docs = df['LOT'].tolist()
                        bra_ipa_docs = df['Brand'].tolist()

                        doc_id = [x + ' ' + y for x, y in zip(bra_ipa_docs, lot_ipa_docs)]
                        sorted_result = sorted(doc_id)
                        serial = st.selectbox('Select bottle', sorted_result)

                        quan_trash = str(st.number_input('Quantity being diposed:', min_value=1))
                    else:
                        st.error("There are no IPA bottles registered to this location")    
                except:
                    st.error("No IPA bottles are currently registered to this location")

                old_ipa_submitted = st.form_submit_button()

                #Grabs information from selected IPA bottle. Copies this information for the discarded IPA collections
                if old_ipa_submitted:
                    users_ref = db.collection(location+"/Printing Items/IPA").document(serial)
                    doc_snapshot = users_ref.get()
                    reg_date = doc_snapshot.get("`Date registered`")
                    ipa_exp = doc_snapshot.get("Exp")
                    ipa_bra = doc_snapshot.get("Brand")
                    ipa_lot = doc_snapshot.get("LOT")
                    live_ipa_quantity = doc_snapshot.get("Quantity")

                    #MATH
                    #This section keeps quanities of live and discarded inventory accurate
                    int_current_quan= int(live_ipa_quantity)
                    int_quantity_disposed = int(quan_trash)
                    new_live_quan = str(int_current_quan - int_quantity_disposed)

                    #Checks if any have already been disposed
                    disp = db.collection(location+"/Discarded Printing Items/Discarded IPA").document(serial)
                    disp_ref = disp.get()

                    if disp_ref.exists:
                        already_disposed = disp_ref.get('Quantity')
                        int_already_disposed = int(already_disposed)
                        quan_trash = str(int_already_disposed + int_quantity_disposed)

                    #Information uploaded to discarded inventory on Firestore
                    doc_ref2 = db.collection(location+"/Discarded Printing Items/Discarded IPA").document(serial)
                    doc_ref2.set({
                        "Brand": ipa_bra,
                        "Date Registered": reg_date,
                        "Disposal Date": disp_date,
                        "LOT": ipa_lot,
                        "EXP": ipa_exp,
                        "Quantity": quan_trash
                    })
                    st.warning("This item was discarded!")

                    #If there are zero containers of a IPA left in the live inventory, the document is delted

                    str_check = int(new_live_quan)
                    if str_check <= 0:
                        db.collection(location+"/Printing Items/IPA").document(serial).delete()
                    
                    #If there are more than zero containers left, the live quanitity is updated
                    else:
                        users_ref.update({'Quantity':new_live_quan})

            pressed = st.button("View current IPA inventory at " + location, key = 'ipa inventory')
            if pressed:
            
                users = list(db.collection(location+"/Printing Items/IPA").stream())

                users_dict = list(map(lambda x: x.to_dict(), users))
                df = pd.DataFrame(users_dict)
                dft2 = df.reindex(sorted(df.columns), axis=1)
                st.header("IPA at "+location)
                st.dataframe(dft2)
