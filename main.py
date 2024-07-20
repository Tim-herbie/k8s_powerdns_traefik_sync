from kubernetes import client, config
from psycopg2 import sql
import psycopg2
import requests
import time
import sys
import os
from datetime import datetime

# powerdns traefik sync tool settings
DEBUG_LOGGING = os.getenv('DEBUG_LOGGING', '').lower() == 'true'
SLEEP_DURATION = int(os.getenv('SLEEP_DURATION', '30'))
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Group, version and plural for IngressRoute
TRAEFIK_CRD_GROUP = os.getenv('TRAEFIK_CRD_GROUP', 'traefik.io')
TRAEFIK_CRD_VERSION = os.getenv('TRAEFIK_CRD_VERSION', 'v1alpha1')
TRAEFIK_CRD_PLURAL = os.getenv('TRAEFIK_CRD_PLURAL', 'ingressroutes')

# Configuration for PowerDNS
PDNS_API_URL = os.getenv('PDNS_API_URL')
PDNS_API_KEY = os.getenv('PDNS_API_KEY')
SERVER_ID = 'localhost'
PDNS_ZONE_NAME = os.getenv('PDNS_ZONE_NAME')

# Configuration for PowerDNS Record
RECORD_TYPE = 'CNAME'
TTL = int(os.getenv('TTL', '3600'))
CONTENT = os.getenv('CONTENT')

# # Define your database connection parameters
db_params = {
    'dbname': os.getenv('PTS_DB_NAME'),
    'user': os.getenv('PTS_DB_USER'),
    'password': os.getenv('PTS_DB_PASSWORD'),
    'host': os.getenv('PTS_DB_HOST', 'pts-postgres-db'),
    'port': os.getenv('PTS_DB_PORT', '5432')
}

def log_message(message):
    print(message)
    sys.stdout.flush()

############
# PDNS API #
############
def get_dns_records(PDNS_API_URL, PDNS_API_KEY, SERVER_ID, PDNS_ZONE_NAME, record_name):
    headers = {
        'X-API-Key': PDNS_API_KEY,
        'Content-Type': 'application/json',
    }

    # Get the zone details
    zone_url = f"{PDNS_API_URL}/servers/{SERVER_ID}/zones/{PDNS_ZONE_NAME}"
    response = requests.get(zone_url, headers=headers)

    if response.status_code != 200:
        log_message(f"[{timestamp}]: Failed to retrieve zone details: {response.status_code} {response.text}")
        return False

    zone_data = response.json()

    # Check if the record exists in the zone data
    for record_set in zone_data.get('rrsets', []):
        if record_set['name'] == record_name:
            if DEBUG_LOGGING:
                log_message(f"Record {record_name} found with type {record_set['type']}.")
            return True

    log_message(f"[{timestamp}]: Record {record_name} not found.")
    return False

def add_dns_record(PDNS_API_URL, PDNS_API_KEY, SERVER_ID, PDNS_ZONE_NAME, record_name, RECORD_TYPE, CONTENT, TTL):
    headers = {
        'X-API-Key': PDNS_API_KEY,
        'Content-Type': 'application/json',
    }

    endpoint = f"{PDNS_API_URL}/servers/{SERVER_ID}/zones/{PDNS_ZONE_NAME}"
    payload = {
        "rrsets": [
            {
                "name": record_name,
                "type": RECORD_TYPE,
                "changetype": "REPLACE",
                "ttl": TTL,
                "records": [
                    {
                        "content": CONTENT,
                        "disabled": False,
                    }
                ]
            }
        ]
    }

    response = requests.patch(endpoint, headers=headers, json=payload)

    if response.status_code == 204:
        log_message(f"[{timestamp}]: DNS record {record_name} updated successfully.")
        return True
    else:
        log_message(f"[{timestamp}]: Failed to update DNS record {record_name}: {response.status_code} {response.text}")
        return False
    
def delete_dns_record(PDNS_API_URL, PDNS_API_KEY, SERVER_ID, PDNS_ZONE_NAME, record_name, RECORD_TYPE):
    headers = {
        'X-API-Key': PDNS_API_KEY,
        'Content-Type': 'application/json',
    }

    endpoint = f"{PDNS_API_URL}/servers/{SERVER_ID}/zones/{PDNS_ZONE_NAME}"
    payload = {
        "rrsets": [
            {
                "name": record_name,
                "type": RECORD_TYPE,
                "changetype": "DELETE",
            }
        ]
    }

    response = requests.patch(endpoint, headers=headers, json=payload)

    if response.status_code == 204:
        log_message(f"[{timestamp}]: DNS record {record_name} successfully removed.")
        return True
    else:
        log_message(f"[{timestamp}]: Failed to update DNS record {record_name}: {response.status_code} {response.text}")
        return False

############
# PTS DB #
############
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

def main():
    # Log start of the loop
    log_message("Starting the powerdns-traefik-sync tool.")
    
    while True:
        try:
            # Load in-cluster config
            config.load_incluster_config()
            if DEBUG_LOGGING:
                log_message("Kubernetes config loaded.")

            # Create an instance of the API class
            custom_api = client.CustomObjectsApi()

            # List all IngressRoute objects in all namespaces
            ingress_routes = custom_api.list_cluster_custom_object(TRAEFIK_CRD_GROUP, TRAEFIK_CRD_VERSION, TRAEFIK_CRD_PLURAL)
            if DEBUG_LOGGING:
                log_message(f"Retrieved {len(ingress_routes.get('items', []))} IngressRoute objects.")

            # Collect host values
            hosts = []
            for ingress_route in ingress_routes.get('items', []):
                spec = ingress_route.get('spec', {})
                routes = spec.get('routes', [])
                for route in routes:
                    match = route.get('match', '')
                    if 'Host(' in match:
                        host = match.split('Host(')[-1].split(')')[0]
                        # Strip quotes and any other unnecessary characters
                        host = host.strip('"').strip("'").strip('`')
                        hosts.append(host)
            
            # Print collected host values
            if DEBUG_LOGGING:
                log_message("Collected host values:")
                for host in hosts:
                    log_message(host)

            # Check if each host exists as a DNS record
            for host in hosts:
                full_record_name = f"{host}."
                if DEBUG_LOGGING:
                    log_message(f"Checking if DNS record {full_record_name} exists...")
                record_exists = get_dns_records(PDNS_API_URL, PDNS_API_KEY, SERVER_ID, PDNS_ZONE_NAME, full_record_name)
                if not record_exists:  # If record doesn't exist, create it
                    insert_traefik_ingressroute(db_params, host, RECORD_TYPE, CONTENT, TTL)
                    if add_dns_record(PDNS_API_URL, PDNS_API_KEY, SERVER_ID, PDNS_ZONE_NAME, full_record_name, RECORD_TYPE, CONTENT, TTL):
                        log_message(f"[{timestamp}]: The DNS record {full_record_name} has been created.")
                    else:
                        log_message(f"[{timestamp}]: Failed to create DNS record {full_record_name}.")

            # Check if a ingressroute does not exist anymore
            existing_dns_records = get_added_traefik_ingressroutes(db_params)
            if existing_dns_records is not None:
                for dns_record in existing_dns_records:
                    name_to_check = dns_record[1]
                    full_record_name = f"{dns_record[1]}."
                    if name_to_check in hosts:
                        if DEBUG_LOGGING:
                            print(f"Found '{name_to_check}' was no longer found.")
                    else:
                        print(f"Traefik Ingressroute: '{name_to_check}' not found in ingress routes.")
                        delete_dns_record(PDNS_API_URL, PDNS_API_KEY, SERVER_ID, PDNS_ZONE_NAME, full_record_name, RECORD_TYPE)
                        remove_added_traefik_ingressroute(db_params, name_to_check)
            else:
                print("Failed to fetch DNS records.")


        except Exception as e:
            log_message(f"An error occurred: {e}")

        # Sleep for ... seconds before repeating the process
        if DEBUG_LOGGING:
            log_message(f"Sleeping for {SLEEP_DURATION} seconds...")
        time.sleep(SLEEP_DURATION)

if __name__ == '__main__':
    main()
