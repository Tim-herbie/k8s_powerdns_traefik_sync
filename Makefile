#########################
### Variables Section ###
#########################

.ONESHELL:
# PostgreSQL OPERATOR Variables
PostgreSQL_OPERATOR_NAMESPACE := postgres
PostgreSQL_OPERATOR_VERSION := 1.10.1
POSTGRES_OPERATOR_CHECK = $(shell kubectl get pods -A -l app.kubernetes.io/name=postgres-operator)

# PowerDNS Variables 
PTS_DB_PASSWORD = $(shell kubectl get secret postgres.pts-postgres-db.credentials.postgresql.acid.zalan.do -n $(NAMESPACE) -o json | jq '.data | map_values(@base64d)' | jq -r '.password')

# PTS Tool Variables
PTS_MODE := standard

NAMESPACE := pdns
PDNS_API_URL := https://pdns-auth.example.com/api/v1
DNS_ZONE := example.com.
TRAEFIK_NAMESPACE := traefik #necessary for the standard method
K8S_INGRESS := ingress.example.com. #necessary for the advanced method

.PHONY: install-postgresql-operator

###########################
### Deployment Section ####
###########################
all: prep install-postgresql-operator wait_for_postgres_operator postgres-db-install wait_for_postgresql postgres-db-init svc-reader-rbac pts-install

prep:
	kubectl create namespace $(NAMESPACE) --dry-run=client -o yaml | kubectl apply -f -
	kubectl -n $(NAMESPACE) apply -f ./secret.yaml

install-postgresql-operator:
ifneq ($(strip $(POSTGRES_OPERATOR_CHECK)),)
	$(info Postgres Operator is already installed. Nothing to do here.)
else
	helm upgrade --install postgres-operator \
	--set configKubernetes.enable_pod_antiaffinity=true \
	--set configKubernetes.enable_readiness_probe=true \
	--namespace $(PostgreSQL_OPERATOR_NAMESPACE) \
	--version=$(PostgreSQL_OPERATOR_VERSION) \
	postgres-operator-charts/postgres-operator
endif

wait_for_postgres_operator:
	@while true; do \
        status=$$(kubectl -n $(PostgreSQL_OPERATOR_NAMESPACE) get pods -l app.kubernetes.io/name=postgres-operator -o json | jq -r '.items[].status.phase'); \
        if [ "$$status" = "Running" ]; then \
            echo "Postgres Operator is ready."; \
            break; \
        else \
            echo "Postgres Operator is not ready yet. Waiting..."; \
            sleep 10; \
        fi; \
    done

postgres-db-install:
	kubectl -n $(NAMESPACE) apply -f ./postgres-db.yaml

wait_for_postgresql:
	@while true; do \
        status=$$(kubectl get postgresql pts-postgres-db -o json | jq -r '.status.PostgresClusterStatus'); \
        if [ "$$status" = "Running" ]; then \
            echo "PostgreSQL cluster is now Running."; \
            break; \
        else \
            echo "PostgreSQL cluster is still not ready. Waiting..."; \
            sleep 10; \
        fi; \
    done

postgres-db-init:
	kubectl -n $(NAMESPACE) apply -f ./postgres-init.yaml

svc-reader-rbac:
ifeq ($(PTS_MODE), standard)
	kubectl -n $(TRAEFIK_NAMESPACE) apply -f ./service-reader-rbac.yaml
endif

pts-install:
	cat ./deployment.yaml | sed 's|{{PTS_DB_PASSWORD}}|$(PTS_DB_PASSWORD)|g' | sed 's|{{DNS_ZONE}}|$(DNS_ZONE)|g' | sed 's|{{K8S_INGRESS}}|$(K8S_INGRESS)|g' | sed 's|{{PDNS_API_URL}}|$(PDNS_API_URL)|g' | sed 's|{{PTS_MODE}}|$(PTS_MODE)|g' | sed 's|{{PTS_IMAGE_TAG}}|$(PTS_IMAGE_TAG)|g' | kubectl -n $(NAMESPACE) apply -f -

delete:
	kubectl -n $(NAMESPACE) delete -f ./deployment.yaml --ignore-not-found=true
	kubectl -n $(NAMESPACE) delete -f ./postgres-init.yaml --ignore-not-found=true
	kubectl -n $(NAMESPACE) delete -f ./postgres-db.yaml --ignore-not-found=true
#	helm -n $(PostgreSQL_OPERATOR_NAMESPACE) uninstall postgres-operator
#	kubectl delete ns $(PostgreSQL_OPERATOR_NAMESPACE)
#	kubectl delete ns $(NAMESPACE)