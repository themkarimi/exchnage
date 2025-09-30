# Deployment Proposal for Exchange Service

This **Exchange Service**, developed using the **Python/Django framework**, is intended to run in a Kubernetes cluster with **scalability, reliability, and availability** in mind.  

Upon inspection of the code, to comply with **12-factor app standards**, it was necessary for the application to be completely stateless. The local storage used for media was an obstacle that needed to be addressed.  

Changes were made so that the app now uses **MinIO Object Storage** for its static and media files. With this change, the app can be easily deployed and scaled in a Kubernetes environment.

---

## CI/CD

- **GitLab CI** is used for automation.  
- On changes to the main branch, the pipeline is triggered.  
- If a staging environment is introduced, the pipeline can be separated by environments.  
- The application has been **dockerized using best practices**, and requirements are explicitly specified.  

For deployment, we use a **GitOps process**:  
- A separate repo (`Exchange-DevOps`) maintains the application manifests.  
- **ArgoCD** watches for changes and applies them (e.g., updating image tags during the deploy stage of CI/CD).  
- Three manifests need to be updated:  
  1. The main app  
  2. The **Django-Q** manifest (for background jobs)  
  3. The **migrations job** (to update the database)  

---

## Database

- A **Master-Slave PostgreSQL deployment** has been set up using the **Bitnami Helm chart**.  
- Database backup jobs and monitoring are enabled.  

---

## Load Balancing

- If a **WAF** is in place, requests are routed to Kubernetes workers.  
- If not, we can use **MetalLB** or **Cilium** to provide a virtual IP address.  
- Requests are received by **NGINX Ingress** and distributed to endpoints using Kubernetes’ internal routing (via `kube-proxy` and iptables rules).  

For database load balancing:  
- Currently, none is implemented (testing purposes).  
- In production, it is recommended to use **HAProxy** or **ProxySQL** for query routing, load balancing, and health checks.  

---

## MinIO

- A **four-node MinIO cluster** has been deployed for handling static files.  

---

## Monitoring

- Implemented using **kube-prometheus-stack** (Grafana, Prometheus, and Alertmanager).  
- An **alert bot** is needed to send alerts to **Telegram or SMS**.  
- Metrics are scraped from the Exchange application and all backing services.  

---

## Logging

- **Elasticsearch and Kibana** are implemented via the **ECK Operator**.  
- Logs are collected with a **Fluent Bit DaemonSet** and shipped to Elasticsearch.  