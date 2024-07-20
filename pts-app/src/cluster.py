import kubernetes

from utils import *
from config import *
from kubernetes import client, config

def get_ingressroute_objects():
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

    return hosts