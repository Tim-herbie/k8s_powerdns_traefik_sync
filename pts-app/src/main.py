import time

from database import *
from powerdns import *
from utils import *
from config import *
from cluster import *

def main():
    # Log start of the loop
    log_message("Starting the powerdns-traefik-sync tool.")
    
    while True:
        try:
            # Get all dns names from the kubeapi
            hosts = get_ingressroute_objects()

            # Check if a DNS record exists for each host
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
                            print(f"Found '{name_to_check}'")
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
