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

def get_assigned_employee_clients(salesRep_name, Days):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # SQL query to fetch only the client IDs, fixing the interval part
        # query = f"""
        #     SELECT c.id
        #     FROM client c
        #     JOIN employee e ON c.assigned_employee = e.id
        #     WHERE e.fullname = %s
        #     AND c.created >= NOW() - INTERVAL '{Days} day';
        # """
        print(f"sales rep and day received {salesRep_name} and {Days}")
        query = f"""
        SELECT c.id 
        FROM client c
        JOIN employee e ON c.assigned_employee = e.id
        WHERE e.fullname = '{salesRep_name}'
        AND c.created >= NOW() - INTERVAL '{Days} day';
        """

        print(f"Executing query: {query}")  # Debugging to print the SQL query
        cur.execute(query)
        result = cur.fetchall()
        
        # Extract client IDs from the result and store them in a list
        client_ids = [row[0] for row in result]
        
        cur.close()
        conn.close()

        return client_ids
    
    except Exception as e:
        st.error(f"Error: {e}")
        return []



def get_client_info(chat_transcript,client_name,assigned_employee_name):
    model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")
    response = model.generate_content([f"""
        You are a Very Expert Sales Person
        Read this Chat Transcript and tell me how many buildings we sent to the client and which building client is interested in and has he gone to tour the building even if it was virtual tour ? if yes what was his remark on that toured building
        Has the application is signed? If yes, what is the status of the application?
        If No whats is the reason for not signing the application?
        What is the status of the application?
        Has application is been approved ? 
        Did Sales Rep has followed up with the client for Application?
        also a little Summary of the chat transcript to understand what went wrong or right where sales rep make mistake or did good job. how can the situtation be improved in future.
        What is the name of Sales Rep Dealing with the client?
        if any of the importion is not given write NO Information Provided infront of that
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
        Summary: (Summary of the chat transcript)
        
            """,])

    print(response.text)
    return response.text

def get_sales_rep_performance(chat_info):
    model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")
    response = model.generate_content([f"""
        You are a Very Expert Sales Person
        These are the chat's report generated for multiple clients of a specific sales rep you have to identify what went wrong here and what is the performance of the sales person 
        first mention his name then tell what you think is he doing good or not 
        is he getting enough applications 
        is he trying hard? or did he need coaching 
        if yes what are the areas he need to improve?
        Here is the chat transcript report for multiple clients of a sales rep:
        {chat_info}
        
        Make your response short and to the point and in bullet points 
            """,])

    print(response.text)
    return response.text

# def main():

#     st.header('Sent Buildings with Additional Building Info')
#     sent_properties = get_sent_properties()
#     if sent_properties:
#         df = pd.DataFrame(sent_properties, columns=['Client ID', 'Building ID', 'Building Name', 'Address', 'City', 'State', 'Company', 'Cooperation Percentage'])
#         total_clients = df['Client ID'].nunique()  
#         total_buildings = df['Building ID'].nunique() 
#         st.write(f"Total clients: {total_clients}")
#         st.write(f"Total buildings: {total_buildings}")
        
#         st.dataframe(df)
    
#     st.header('Building Options Received But Not Sent, which can be sent with Additional Building Info')
#     not_send_properties = get_not_sent_properties()
#     if not_send_properties:
#         df = pd.DataFrame(not_send_properties, columns=['Client ID', 'Building ID', 'Building Name', 'Address', 'City', 'State', 'Company', 'Cooperation Percentage'])
#         total_clients = df['Client ID'].nunique()  
#         total_buildings = df['Building ID'].nunique() 
#         st.write(f"Total clients: {total_clients}")
#         st.write(f"Total buildings: {total_buildings}")
        
#         st.dataframe(df)

#     else:
#         st.warning("No data found or unable to connect to the database.")
    

    # st.header('Get Client Related Info:')
    # client_id_input = st.text_input("Enter Client ID:")
    
    # if st.button("Fetch Chat"):
    #     if client_id_input:

    #         chat_transcript, client_name, client_url, assigned_employee_name = fetch_chat_data(DATABASE_URL, client_id_input)

    #         if chat_transcript:
    #             ai_response = get_client_info(chat_transcript, client_name, assigned_employee_name)
                
    #             # Display the AI response
    #             st.subheader("Client Information Summary")
    #             st.text(ai_response)
    #         else:
    #             st.warning(f"No chat data found for Client ID: {client_id_input}")
    #     else:
    #         st.warning("Please enter a valid Client ID.")
            
#     st.header("Get sales Rep Clients with reports")
    
#     salesRep_name = st.selectbox("Select Sales Rep:", [" ","Alina Vector", "Ryan Rehman", "Waseem Zubair", "Sara Edward", "John Green"])
#     days = st.selectbox("Select Days:", [" ",1, 2, 10, 20, 30])
#     data_received = get_assigned_employee_clients(salesRep_name, days)
    

# if __name__ == "__main__":
#     main()


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
    
    if st.button("Fetch Chat with Details"):
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

    st.header("Get sales Rep reports")
    
    salesRep_name = st.selectbox("Select Sales Rep:", [" ","Alina Victor", "Ryan Rehman", "Waseem Zubair", "Sara Edward", "John Green", "James Hanan", "Bill Smith", "Brad Steele", "Brandon Wilson", "Thomas Junior"])
    days = st.selectbox("Select Days:", [" ",1, 5, 10, 15, 20, 25, 30])
    print(salesRep_name, days)
    if st.button("Fetch Clients and Generate Replies"):
        if salesRep_name.strip() and days:
            client_ids = get_assigned_employee_clients(salesRep_name, days)
            print(client_ids)
            if client_ids:
                ai_responses = []

                for client_id in client_ids:
                    chat_transcript, client_name, client_url, assigned_employee_name = fetch_chat_data(DATABASE_URL, client_id)
                    
                    if chat_transcript:
                        ai_response = get_client_info(chat_transcript, client_name, assigned_employee_name)
                        print(ai_response)
                        ai_responses.append(ai_response)
                    else:
                        st.warning(f"No chat data found for Client ID: {client_id}")

                consolidated_chat_info = "\n\n".join(ai_responses)
                performance_response = get_sales_rep_performance(consolidated_chat_info)

                st.subheader("Sales Rep Performance Summary")
                st.text(performance_response)
            else:
                st.warning(f"No clients found for Sales Rep {salesRep_name} in the last {days} days.")
        else:
            st.warning("Please select a valid Sales Rep and number of days.")

if __name__ == "__main__":
    main()
