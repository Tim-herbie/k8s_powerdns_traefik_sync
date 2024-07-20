import psycopg2

from utils import *
from config import *
from psycopg2 import sql


def insert_traefik_ingressroute(db_params, host, RECORD_TYPE, CONTENT, TTL):
    # Establish the connection
    try:
        conn = psycopg2.connect(**db_params)
        if DEBUG_LOGGING:
            print("Connection to the database established successfully.")
    except Exception as error:
        print(f"Error: Could not make connection to the database.\n{error}")
        exit(1)

    # Create a cursor object
    cur = conn.cursor()

    # Construct the query
    query = sql.SQL("INSERT INTO records (name, type, content, ttl) VALUES ({0}, {1}, {2}, {3})").format(
        sql.Literal(host),
        sql.Literal(RECORD_TYPE),
        sql.Literal(CONTENT),
        sql.Literal(TTL)
    )

    try:
        # Execute the query
        cur.execute(query)
        
        # Commit the transaction
        conn.commit()
        if DEBUG_LOGGING:
            print("Record inserted successfully.")
    except Exception as error:
        print(f"Error: Failed to execute query.\n{error}")
        conn.rollback()
    
    # Close the cursor and connection
    cur.close()
    conn.close()
    if DEBUG_LOGGING:
        print("Connection closed.")

def get_added_traefik_ingressroutes(db_params):
    # Establish the connection
    try:
        conn = psycopg2.connect(**db_params)
        if DEBUG_LOGGING:
            print("Connection to the database established successfully.")
    except Exception as error:
        print(f"Error: Could not make connection to the database.\n{error}")
        exit(1)

    # Create a cursor object
    cur = conn.cursor()

    # Construct the query
    query = sql.SQL("SELECT * FROM records")

    try:
        # Execute the query
        cur.execute(query)
        
        # Fetch all results
        rows = cur.fetchall()
        
        # Close the cursor and connection
        cur.close()
        conn.close()
        if DEBUG_LOGGING:
            print("Connection closed.")
        
        # Return fetched rows
        return rows
    except Exception as error:
        print(f"Error: Failed to execute query.\n{error}")

        # Close the cursor and connection
        cur.close()
        conn.close()
        if DEBUG_LOGGING:
            print("Connection closed.")
        return None
    
def remove_added_traefik_ingressroute(db_params, host):
    # Establish the connection
    try:
        conn = psycopg2.connect(**db_params)
        if DEBUG_LOGGING:
            print("Connection to the database established successfully.")
    except Exception as error:
        print(f"Error: Could not make connection to the database.\n{error}")
        exit(1)

    # Create a cursor object
    cur = conn.cursor()

    # Construct the query
    query = sql.SQL("DELETE FROM records WHERE name = {0}").format(
        sql.Literal(host),
    )

    try:
        # Execute the query
        cur.execute(query)
        
        # Commit the transaction
        conn.commit()
        if DEBUG_LOGGING:
            print("Record successfully removed.")
    except Exception as error:
        print(f"Error: Failed to execute query.\n{error}")
        conn.rollback()
    
    # Close the cursor and connection
    cur.close()
    conn.close()
    if DEBUG_LOGGING:
        print("Connection closed.")