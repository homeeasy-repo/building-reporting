import psycopg2
import os
import pandas as pd
# from dotenv import load_dotenv

# load_dotenv()
# DATABASE_URL = os.getenv('DATABASE_URL')

def fetch_chat_data(DATABASE_URL, client_id):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        chat_query = """
            SELECT TO_CHAR(created, 'HH12:MM DD/MM/YYYY'), status, message
            FROM public.textmessage
            WHERE client_id = %s
            ORDER BY created ASC;
        """
        cur.execute(chat_query, (client_id,))
        chats = cur.fetchall()

        client_query = """
            SELECT fullname, id, assigned_employee_name
            FROM public.client
            WHERE id = %s;
        """
        cur.execute(client_query, (client_id,))
        client_info = cur.fetchone()

        chat_transcript = ""
        for timestamp, status, message in chats:
            if status == "Received":
                chat_transcript += f"[{timestamp}] Client: {message}\n"
            else:
                chat_transcript += f"[{timestamp}] Sales Rep: {message}\n"

        if client_info:
            client_name, client_id, assigned_employee_name = client_info
        else:
            client_name = "Client"
            client_id = None
            assigned_employee_name = None

        client_url = (
            f"<https://services.followupboss.com/2/people/view/{client_id}|{client_name}>"
            if client_id
            else client_name
        )

        if not chat_transcript:
            print(f"No chat transcript found for client ID: {client_id}")

        cur.close()
        conn.close()

        return chat_transcript, client_name, client_url, assigned_employee_name

    except Exception as e:
        print(f"Error fetching chat data for client ID {client_id}: {e}")
        return "", "", "#", None