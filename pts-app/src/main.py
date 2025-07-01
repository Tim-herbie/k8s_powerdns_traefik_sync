import time

from database import *
from powerdns import *
from utils import *
from config import *
from cluster import *

def handle_dns_creation(domains):
    # Check if a DNS record exists for each domain
    for domain in domains:

        # Extract the domain parameters from the object
        DOMAIN_DATA = domain['domain']
        ENTRYPOINTS = domain['entrypoints']
        FULL_RECORD_NAME = f"{DOMAIN_DATA}."

        # Get all Traefik service objects if the standard mode is chosen
        if PTS_MODE == "standard":
            LOADBALANCER_IP = create_dns_records(ENTRYPOINTS)

        # Debug Logs
        if DEBUG_LOGGING:
            log_message(f"Checking if DNS record {FULL_RECORD_NAME} exists...")
        
        # Check if the domain exists in the PowerDNS Server
        record_exists = get_dns_records(PDNS_API_URL, PDNS_API_KEY, SERVER_ID, PDNS_ZONE_NAME, FULL_RECORD_NAME)

        # If Record doesn't exist, create it
        if not record_exists:

            # Create the DNS-Record within the PowerDNS Server and log the result
            if PTS_MODE == "standard":
                # Add domain to the pts database
                insert_traefik_ingressroute(db_params, DOMAIN_DATA, RECORD_TYPE, LOADBALANCER_IP, TTL)

                if add_dns_record(PDNS_API_URL, PDNS_API_KEY, SERVER_ID, PDNS_ZONE_NAME, FULL_RECORD_NAME, RECORD_TYPE, LOADBALANCER_IP, TTL):
                    log_message(f"[{timestamp}]: The DNS record {FULL_RECORD_NAME} was added to the PTS database.")
                else:
                    log_message(f"[{timestamp}]: Failed to create DNS record {FULL_RECORD_NAME}.")
            elif PTS_MODE == "advanced":
                # Add domain to the pts database
                insert_traefik_ingressroute(db_params, DOMAIN_DATA, RECORD_TYPE, CONTENT, TTL)

                if add_dns_record(PDNS_API_URL, PDNS_API_KEY, SERVER_ID, PDNS_ZONE_NAME, FULL_RECORD_NAME, RECORD_TYPE, CONTENT, TTL):
                    log_message(f"[{timestamp}]: The DNS record {FULL_RECORD_NAME} was added to the PTS database.")
                else:
                    log_message(f"[{timestamp}]: Failed to create DNS record {FULL_RECORD_NAME}.")

def remove_stale_dns_records(domains):
    # Check if an ingressroute does not exist anymore
    existing_dns_records = get_added_traefik_ingressroutes(db_params)
    if existing_dns_records is not None:
        for dns_record in existing_dns_records:
            
            # Define domain that will be checked
            name_to_check = dns_record[1]

            # Define DNS Record of the domain
            FULL_RECORD_NAME = f"{dns_record[1]}."

            # Boolean Variable
            existing_dns_record = False

            for domain in domains:
                # Check if the domain exists in the existing ingressroutes
                if domain.get('domain') == name_to_check:
                    existing_dns_record = True
                    break
            
            if existing_dns_record:
                if DEBUG_LOGGING:
                        print(f"Found '{name_to_check}'")
            else:
                print(f"[{timestamp}]: Traefik Ingressroute: '{name_to_check}' not found in ingress routes.")
                delete_dns_record(PDNS_API_URL, PDNS_API_KEY, SERVER_ID, PDNS_ZONE_NAME, FULL_RECORD_NAME, RECORD_TYPE)
                remove_added_traefik_ingressroute(db_params, name_to_check)
    else:
        print("Failed to fetch DNS records.")

def main():
    # Log start of the loop
    log_message(f"Starting the powerdns-traefik-sync tool in the {PTS_MODE} Mode.")
    
    while True:
        try:
            # Get all dns names from the kubeapi
            domains = get_ingressroute_objects()

            # Handles the DNS record creation logic based on the mode
            handle_dns_creation(domains)
            
            # Checks for ingress routes that no longer exist and removes the corresponding DNS records
            remove_stale_dns_records(domains)

        except Exception as e:
            log_message(f"An error occurred: {e}")

        # Sleep for ... seconds before repeating the process
        if DEBUG_LOGGING:
            log_message(f"Sleeping for {SLEEP_DURATION} seconds...")
        time.sleep(SLEEP_DURATION)

if __name__ == '__main__':
    main()
