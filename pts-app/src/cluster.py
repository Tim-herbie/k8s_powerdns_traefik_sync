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

    # Define variables
    domains_data = []

    for ingress_route in ingress_routes.get('items', []):
        
        # Define variables
        entrypoints_list = []

        # Get 'spec' from 'ingress_route'
        spec = ingress_route.get('spec', {})

        # Get 'entryPoints' from 'spec'
        entrypoints = spec.get('entryPoints', [])

        # Get 'routes' from 'spec'
        routes = spec.get('routes', [])
        
        for route in routes:
            match = route.get('match', '')
            if 'Host(' in match:
                domain = match.split('Host(')[-1].split(')')[0]
                
                # Strip quotes and any other unnecessary characters
                domain = domain.strip('"').strip("'").strip('`')

                # Handle only domains that were defined before
                if PTS_DOMAIN_LIST == "all" or any(domain.endswith(d) for d in PTS_DOMAIN_LIST.split(",")):
                    # Get all entrypoints
                    for entrypoint in entrypoints:
                        entrypoints_list.append(entrypoint)

                    # Create the domain + entrypoint object
                    domain_data = {
                        "domain": domain,
                        "entrypoints": entrypoints_list
                    }
                    domains_data.append(domain_data)
                else:
                    if DEBUG_LOGGING:
                        log_message("This domain is not in the PTS domain list and will not be handled:")
                        log_message(domain)

    # Print collected domain values
    if DEBUG_LOGGING:
        log_message("Collected domain values:")
        log_message(domains_data)

    return domains_data

def get_traefik_service_objects():
    # Define variables
    service_objects = []
    
    
    # Load in-cluster config
    config.load_incluster_config()

    if DEBUG_LOGGING:
        log_message("Kubernetes config loaded.")

    # Create an instance of the CoreV1Api class
    v1_api = client.CoreV1Api()

    # Define the namespace you want to query
    namespace = TRAEFIK_NAMESPACE

    # List all services in the specified namespace
    services = v1_api.list_namespaced_service(namespace)
    
    # Iterate through the services and print relevant details
    for svc in services.items:
        entrypoints = []

        for port in svc.spec.ports:
            entrypoints.append(port.name)
        
        # Extract the LoadBalancer IP
        if svc.status.load_balancer and svc.status.load_balancer.ingress:
            for ingress in svc.status.load_balancer.ingress:
                if ingress.ip:
                    if DEBUG_LOGGING:
                        log_message(f"LoadBalancer IP: {ingress.ip}")

                    service_object = {
                        "service_name": svc.metadata.name,
                        "entrypoint_names": entrypoints,
                        "loadbalancer_ip": ingress.ip
                    }
                elif ingress.hostname:
                    if DEBUG_LOGGING:
                        log_message(f"LoadBalancer Hostname: {ingress.hostname}")
                    
                    service_object = {
                        "service_name": svc.metadata.name,
                        "entrypoint_names": entrypoints,
                        "loadbalancer_ip": ingress.hostname
                    }
            service_objects.append(service_object)
        else:
            log_message("Error: LoadBalancer IP is not set!")

    return service_objects

def create_dns_records(entrypoints):
    # Get all Traefik services
    traefik_service_objects = get_traefik_service_objects()

    for entrypoint in entrypoints:

        for service_object in traefik_service_objects:
            service_object_name = service_object['service_name']
            service_object_entrypoints = service_object['entrypoint_names']
            service_object_lb_ip = service_object['loadbalancer_ip']
            
            if entrypoint in service_object_entrypoints:
                if DEBUG_LOGGING:
                    log_message(f"The Entrypoint {entrypoint} was found in the Traefik Kubernetes Service {service_object_name} and will be mapped to the IP {service_object_lb_ip}")
                return service_object_lb_ip
