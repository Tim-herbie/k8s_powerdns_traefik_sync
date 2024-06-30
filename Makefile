.ONESHELL:
PTS_DB_PASSWORD = $(shell kubectl get secret postgres.pts-postgres-db.credentials.postgresql.acid.zalan.do -n $(NAMESPACE) -o json | jq '.data | map_values(@base64d)' | jq -r '.password')
KUBERNETES_API_IP=$(shell kubectl config view --minify --output 'jsonpath={.clusters[0].cluster.server}' | sed -E 's|https://([^:/]+).*|\1/32|')

NAMESPACE := pdns
POWERDNS_API_IP := 10.0.60.120/32

all: prep install-networkpolicies postgres-db-install wait_for_postgresql postgres-db-init pts-install

prep:
	kubectl create namespace $(NAMESPACE) --dry-run=client -o yaml | kubectl apply -f -

install-networkpolicies:
	printf '%s' "$$(cat ./networkpolicies/pts-np.yaml \
        | sed -e 's|{{KUBERNETES_API_IP}}|$(KUBERNETES_API_IP)|g' -e 's|{{POWERDNS_API_IP}}|$(POWERDNS_API_IP)|g')" \
        | kubectl -n $(NAMESPACE) apply -f -
	kubectl -n $(NAMESPACE) apply -f ./networkpolicies/db-np.yaml

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
	printf '%s' "$$(cat ./deployment.yaml | sed 's|{{PTS_DB_PASSWORD}}|$(PTS_DB_PASSWORD)|g')" | kubectl -n $(NAMESPACE) apply -f -
delete:
	kubectl -n $(NAMESPACE) delete -f ./deployment.yaml --ignore-not-found=true
	kubectl -n $(NAMESPACE) delete -f ./postgres-init.yaml --ignore-not-found=true
	kubectl -n $(NAMESPACE) delete -f ./postgres-db.yaml --ignore-not-found=true
#	kubectl delete ns $(NAMESPACE)