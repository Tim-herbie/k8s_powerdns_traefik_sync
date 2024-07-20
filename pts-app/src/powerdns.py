import requests

from utils import *
from config import *

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
        log_message(f"DNS record {record_name} successfully removed.")
        return True
    else:
        log_message(f"Failed to update DNS record {record_name}: {response.status_code} {response.text}")
        return False