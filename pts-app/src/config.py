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