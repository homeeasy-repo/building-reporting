import json
import logging
import re
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import google.generativeai as genai
from model import Client, TextMessage, Building
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
session = Session()

def get_date_weeks_ago(weeks):
    """Calculate the start date based on the number of weeks."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=weeks * 7)
    return start_date, end_date

def query_clients_by_sales_rep(session, sales_rep, start_date, end_date):
    """Query clients assigned to the given sales rep within the date range."""
    return session.query(
        Client.id.label('client_id'),
        Client.fullname,
        Client.created
    ).filter(
        Client.assigned_employee_name == sales_rep,
        Client.created >= start_date,
        Client.created <= end_date
    ).all()

def query_text_messages_for_client(session, client_id):
    """Query chat messages for a specific client."""
    return session.query(
        TextMessage.message
    ).filter(
        TextMessage.client_id == client_id
    ).all()

def extract_building_options(messages):
    """Use AI to extract building options from chat messages."""
    if not messages:
        logging.warning("No messages to process.")
        return []

    building_options = []
    batch_size = 3

    for i in range(0, len(messages), batch_size):
        message_batch = messages[i:i + batch_size]
        combined_messages = " ".join([msg.message for msg in message_batch])

        prompt = f"""
        Please extract the building options provided by the sales rep from this chat.
        Return the building name and address in JSON format:
        {{
            "building_name": "ABC",
            "building_address": "Street number Street name, City, State or region ZIP code, Country"
        }}
        If no building is mentioned, return NULL.
        Here is the chat: {combined_messages}
        """

        response = model.generate_content(prompt)

        try:
            building_text = response.candidates[0].content.parts[0].text.strip()

        
            building_text = re.sub(r'```json\n|\n```|\n', '', building_text).strip()
            building_info = json.loads(building_text)

            building_name = building_info.get("building_name")
            building_address = building_info.get("building_address")

            if building_name and building_address:
                building_options.append({
                    "building_name": building_name,
                    "building_address": building_address
                })
        except json.JSONDecodeError as json_err:
            logging.error(f"Error extracting building options: {json_err}")
            print(f"Invalid JSON format: {building_text}")
        except Exception as e:
            logging.error(f"Error extracting building options: {e}")

    return building_options


def get_building_id(session, building_name, building_address):
    """Fetch building ID from the database based on name and address."""
    building = session.query(Building.id).filter(
        Building.address == building_address
    ).first()

    return building.id if building else None

from contextlib import contextmanager

@contextmanager
def get_session():
    session = Session() 
    try:
        yield session
    finally:
        session.close()  


def process_clients_for_sales_rep(sales_rep, weeks):
    """Main function to process clients for a given Sales Rep and number of weeks."""
    start_date, end_date = get_date_weeks_ago(weeks)
    
    building_data = []

    with get_session() as session:
        clients = query_clients_by_sales_rep(session, sales_rep, start_date, end_date)

        for client in clients:
            messages = query_text_messages_for_client(session, client.client_id)
            building_options = extract_building_options(messages)

            if building_options:
                for building in building_options:
                    building_id = get_building_id(session, building['building_name'], building['building_address'])

                    if building_id:
                        building_data.append({
                            'client_id': client.client_id,
                            'building_id': building_id
                        })
                    else:
                        logging.warning(f"Building not found for Client ID: {client.client_id}")

    return building_data if building_data else []


