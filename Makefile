.ONESHELL:
PTS_DB_PASSWORD = $(shell kubectl get secret postgres.pts-postgres-db.credentials.postgresql.acid.zalan.do -n $(NAMESPACE) -o json | jq '.data | map_values(@base64d)' | jq -r '.password')

NAMESPACE := pdns
PDNS_API_URL := https://pdns-auth.example.com/api/v1
DNS_ZONE := example.com.
K8S_INGRESS := ingress.example.com.

all: prep postgres-db-install wait_for_postgresql postgres-db-init pts-install

prep:
	kubectl create namespace $(NAMESPACE) --dry-run=client -o yaml | kubectl apply -f -

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

pts-install:
	cat ./deployment.yaml | sed 's|{{PTS_DB_PASSWORD}}|$(PTS_DB_PASSWORD)|g' | sed 's|{{DNS_ZONE}}|$(DNS_ZONE)|g' | sed 's|{{K8S_INGRESS}}|$(K8S_INGRESS)|g' | sed 's|{{PDNS_API_URL}}|$(PDNS_API_URL)|g' | kubectl -n $(NAMESPACE) apply -f -

delete:
	kubectl -n $(NAMESPACE) delete -f ./deployment.yaml --ignore-not-found=true
	kubectl -n $(NAMESPACE) delete -f ./postgres-init.yaml --ignore-not-found=true
	kubectl -n $(NAMESPACE) delete -f ./postgres-db.yaml --ignore-not-found=true
#	kubectl delete ns $(NAMESPACE)