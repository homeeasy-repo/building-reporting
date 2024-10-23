import psycopg2
import os
import csv
import streamlit as st
import pandas as pd
from fub_chat import fetch_chat_data
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime
from building_id import process_clients_for_sales_rep  
from selected_building_id import seleted_building

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
            st.write(f"Client IDs: {client_ids}")
            if client_ids:
                ai_responses = []

                for client_id in client_ids:
                    chat_transcript, client_name, client_url, assigned_employee_name = fetch_chat_data(DATABASE_URL, client_id)
                    
                    if chat_transcript:
                        ai_response = get_client_info(chat_transcript, client_name, assigned_employee_name)
                        st.write(f"AI Response of Client Id:{client_id} ==> {ai_response}")
                        ai_responses.append(ai_response)
                    else:
                        st.warning(f"No chat data found for Client ID: {client_id}")

                consolidated_chat_info = "\n\n".join(ai_responses)
                performance_response = get_sales_rep_performance(consolidated_chat_info)

                st.subheader("Sales Rep Final Performance Summary")
                st.text(performance_response)
            else:
                st.warning(f"No clients found for Sales Rep {salesRep_name} in the last {days} days.")
        else:
            st.warning("Please select a valid Sales Rep and number of days.")

def get_lead_progress_report(database_url, sales_rep_name, weeks):
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()

        # Format the interval string
        interval_string = f"{weeks} week"

        query = """
        SELECT c.id, c.fullname, c.addresses, c.created 
        FROM client c
        JOIN employee e ON c.assigned_employee = e.id
        WHERE e.fullname = %s
        AND c.created >= NOW() - INTERVAL %s;
        """

        cur.execute(query, (sales_rep_name, interval_string))
        result = cur.fetchall()

        cur.close()
        conn.close()

        return result

    except Exception as e:
        st.error(f"Error: {e}")
        return None

def format_address(address_list):
    """Format the client address from a list of address components into a readable string."""
    if address_list and isinstance(address_list, list):
        address_components = address_list[0]  
        city = address_components.get('city', '')
        state = address_components.get('state', '')
        street = address_components.get('street', '')
        country = address_components.get('country', '')
        return f"{street}, {city}, {state}, {country}".strip(", ")
    return "Address Not Available"

def get_client_info_for_tour(chat_transcript):
    model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")
    response = model.generate_content([f"""
        Please analyze the provided chat transcript and extract the following details for the client interaction:
        If any of the details are not available, print "Not Found" for that specific field:

        For what day client booked tour: {{"tour_booking_day": "Not Found"}}  
        Client Tour the Building (Y/N): {{"client_tour": "Not Found"}}  
        Actual Tour Executed: {{"actual_tour_day": "Not Found"}}  
        Applied for Application (Y/N): {{"applied_for_application": "Not Found"}}  
        Applied for Application (Day/Date): {{"application_date": "Not Found"}}  
        Application Approved (Y/N): {{"application_approved": "Not Found"}}  
        Application Approval Date/Day: {{"approval_date": "Not Found"}}   

        Ensure that the extracted information is accurate and formatted clearly. 
        For any field without available data, please indicate "Not Found." Thank you!
        Here is the chat: {chat_transcript}
    """])

    content = response.text
    
    content = content.replace('```json', '').replace('```', '').strip()
    
    # Manually clean and parse the dictionary-like string
    content = content.strip('{}')  # Remove outer braces
    extracted_info = {}
    
    # Now split the content into key-value pairs
    for part in content.split(','):
        if ':' in part:
            key, value = part.split(':', 1)
            cleaned_key = key.strip().replace('"', '').strip()
            cleaned_value = value.strip().replace('"', '').strip()
            extracted_info[cleaned_key] = cleaned_value
    
    return extracted_info



from io import StringIO  # Import StringIO for text-based in-memory operations

def generate_csv_report(database_url, sales_rep_name, weeks):
    leads = get_lead_progress_report(database_url, sales_rep_name, weeks)

    if not leads:
        st.warning(f"No leads found for {sales_rep_name} in the last {weeks} weeks.")
        return

    csv_data = []
    csv_headers = [
        "Client Name", "Client Address", "Lead Created Date", "Sales Rep Name",
        "Sent Building Options ID", "Client Selected Building (Y/N)", 
        "Selected Building ID", "For what day client booked tour", 
        "Client Tour the Building (Y/N)", "Actual Tour Executed",
        "Applied for Application (Y/N)", "Applied for Application (Day/Date)",
        "Application Approved (Y/N)", "Application Approval Date/Day"
    ]

    building_data = process_clients_for_sales_rep(sales_rep_name, weeks)
    selected_building_data = seleted_building(sales_rep_name, weeks)

    if building_data is None:
        st.error(f"Could not fetch building data for {sales_rep_name} in the last {weeks} weeks.")
        return

    for lead in leads:
        client_id, client_name, client_address, created_date = lead
        formatted_address = format_address(client_address)

        building_ids = set()
        selected_Building_IDs = set()

        for building_client in building_data:
            if building_client['client_id'] == client_id:
                building_ids.add(building_client['building_id'])
        
        for client_building in selected_building_data:
            if client_building['client_id'] == client_id:
                selected_Building_IDs.add(client_building['building_id'])

        building_ids_str = ', '.join(map(str, sorted(building_ids))) if building_ids else "Not Found"
        selected_building_ids_str = ', '.join(map(str, sorted(selected_Building_IDs))) if selected_Building_IDs else "Not Found"

        chat_transcript = fetch_chat_data(DATABASE_URL, client_id)
        tour_info = get_client_info_for_tour(chat_transcript)

        csv_row = [
            client_name, formatted_address, created_date, sales_rep_name,
            building_ids_str, 
            "N" if "Not Found" in selected_building_ids_str else "Y",  
            selected_building_ids_str,  
            tour_info.get("tour_booking_day"),  
            tour_info.get("client_tour"),  
            tour_info.get("actual_tour_day"),  
            tour_info.get("applied_for_application"),  
            tour_info.get("application_date"),
            tour_info.get("application_approved"), 
            tour_info.get("approval_date")
        ]
        csv_data.append(csv_row)

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(csv_headers)
    writer.writerows(csv_data)
    
    output.seek(0)

    csv_filename = f"Lead_Progress_Report_{sales_rep_name}_{weeks}_weeks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    st.download_button(label="Download CSV", data=output.getvalue(), file_name=csv_filename, mime='text/csv')


def main():
    st.header("Lead Progress Tour Report")

    sales_rep_name = st.selectbox("Select Sales Rep:", ["","Alina Victor", "Ryan Rehman", "Waseem Zubair", "Sara Edward", "John Green", "James Hanan", "Bill Smith", "Brad Steele", "Brandon Wilson", "Thomas Junior"])
    weeks = st.selectbox("Select Number of Weeks:", ["", 1, 2, 3, 4, 5, 6])

    if st.button("Generate Lead Progress Tour Report"):
        generate_csv_report(DATABASE_URL, sales_rep_name, weeks)


if __name__ == "__main__":
    main()
