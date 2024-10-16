import psycopg2
import os
import streamlit as st
import pandas as pd
from fub_chat import fetch_chat_data
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
api_key = os.environ["GOOGLE_API_KEY"]
genai.configure(api_key=api_key)

def get_sent_properties():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # SQL query to fetch bld_id, client_id, map_link where sent is true
        # and join with building and building_info tables to get additional details
        query = """
        SELECT 
            cpm.client_id, 
            cpm.bld_id,
            b.name as building_name,
            b.address,
            b.city,
            b.state,
            bi.company,
            bi.cooperation_percentage
        FROM client_prop_matching cpm
        JOIN building b ON cpm.bld_id = b.id
        JOIN building_info bi ON cpm.bld_id = bi.id
        WHERE cpm.sent = 'true';
        """
        cur.execute(query)
        result = cur.fetchall()

        cur.close()
        conn.close()

        return result
    
    except Exception as e:
        st.error(f"Error: {e}")
        return None
def get_not_sent_properties():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # SQL query to fetch bld_id, client_id, map_link where sent is false
        # and join with building and building_info tables to get additional details
        query = """
        SELECT 
            cpm.client_id, 
            cpm.bld_id,
            b.name as building_name,
            b.address,
            b.city,
            b.state,
            bi.company,
            bi.cooperation_percentage
        FROM client_prop_matching cpm
        JOIN building b ON cpm.bld_id = b.id
        JOIN building_info bi ON cpm.bld_id = bi.id
        WHERE cpm.sent = 'false';
        """
        cur.execute(query)
        result = cur.fetchall()

        cur.close()
        conn.close()

        return result
    
    except Exception as e:
        st.error(f"Error: {e}")
        return None
    
def get_client_info(chat_transcript,client_name,assigned_employee_name):
    model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")
    response = model.generate_content([f"""
        Read this Chat Transcript and tell me how many buildings we sent to the client and which building client is interested in and has he gone to tour the building even if it was virtual tour ? if yes what was his remark on that toured building
        Has the application is signed? If yes, what is the status of the application?
        If No whats is the reason for not signing the application?
        What is the status of the application?
        Has application is been approved ? 
        Did Sales Rep has followed up with the client for Application?
        What is the name of Sales Rep Dealing with the client?
        
        Here is the chat transcript:
        {chat_transcript}
        
        You need to give me a response for all of these and return me answer like that No other comments should be return at all 
        return me response is this pattern always.
        Client Name: {client_name}
        Sales Rep Name: {assigned_employee_name}
        Number of Buildings sent to the client: 2
        Building Client is interested in: (Building name address etc)
        Client toured the building: Yes/No
        Client's remark on toured building: (Client's remark)
        Application Signed: Yes/No
        Application Status: (Status)
        Reason for not signing the application: (Reason)
        Application Approval Status: (Status) Yes/No
        Sales Rep Followed up with the client for Application: Yes/No
        
            """,])

    print(response.text)
    return response.text

def main():

    st.header('Sent Buildings with Additional Building Info')
    sent_properties = get_sent_properties()
    if sent_properties:
        df = pd.DataFrame(sent_properties, columns=['Client ID', 'Building ID', 'Building Name', 'Address', 'City', 'State', 'Company', 'Cooperation Percentage'])
        total_clients = df['Client ID'].nunique()  
        total_buildings = df['Building ID'].nunique() 
        st.write(f"Total clients: {total_clients}")
        st.write(f"Total buildings: {total_buildings}")
        
        st.dataframe(df)
    
    st.header('Building Options Received But Not Sent, which can be sent with Additional Building Info')
    not_send_properties = get_not_sent_properties()
    if not_send_properties:
        df = pd.DataFrame(not_send_properties, columns=['Client ID', 'Building ID', 'Building Name', 'Address', 'City', 'State', 'Company', 'Cooperation Percentage'])
        total_clients = df['Client ID'].nunique()  
        total_buildings = df['Building ID'].nunique() 
        st.write(f"Total clients: {total_clients}")
        st.write(f"Total buildings: {total_buildings}")
        
        st.dataframe(df)

    else:
        st.warning("No data found or unable to connect to the database.")
    

    st.header('Get Client Related Info:')
    client_id_input = st.text_input("Enter Client ID:")
    
    if st.button("Fetch Chat"):
        if client_id_input:

            chat_transcript, client_name, client_url, assigned_employee_name = fetch_chat_data(DATABASE_URL, client_id_input)

            if chat_transcript:
                ai_response = get_client_info(chat_transcript, client_name, assigned_employee_name)
                
                # Display the AI response
                st.subheader("Client Information Summary")
                st.text(ai_response)
            else:
                st.warning(f"No chat data found for Client ID: {client_id_input}")
        else:
            st.warning("Please enter a valid Client ID.")

if __name__ == "__main__":
    main()
