# 201 - anatomy of a stateful deployment

Within 101, a simple Pod definition was used to provision a container with a persistent volume,  deleting the pod, the action is direct and definitive but still let the persistent volume usable.  
From a k8s standpoint, a stateful application is a first class citizen and as such has it's own definition called a [StatefulSet](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/).  
Note that deleting a StatefulSet, Pod(s) are not deleted but scaled down to 0. Scaling down a Satefulet to 0 could provide a ordered and graceful termination of the pods.









### stateful workload
When deploying a legacy workload or a stateful workload, it requires capability to record data in a persistent way. However, by design and out-of-the-box, Kubernetes doesn't provide any scalable and high available persistent storage option.  
As such, a solution like [StorageOS](https://storageos.com) is required to provide Kubernetes with a cloud native storage solution capable of interacting natively, high available, scalable vertically and horizontally, and secure persistent storage. 

As an example, a typical scenario would be the deletion of the containers running a front-end and/or a database. When recreating the corresponding containers, it will restart with the relevant persistent storage at the last known state at the deletion time. 

### cms drupal with postgresql
The CMS Drupal is well know solution used by enterprise companies. The CMS is written in PHP, requires multiple libraries, an Apache server with PHP module, and a database service like PostgreSQL. The actual [installation guide](https://www.drupal.org/docs/installing-drupal) is quite long and extensive.

From a container perspective, the following entries will show how to perform a Kubernetes deployment in an incremental way; from a testing approach to a production grade release management one.

#### namespace
Also known as project, a namespace is a logical separation providing the necessary abstract for multi-tenancy. To create a namespace for DBaaS, the following manifest can be applied:
```yaml
---
apiVersion: v1
kind: Namespace
metadata:
  name: foodmag-app
```
To apply this satefulset manifest, run the following:
```
kubectl apply -f cd/foodmag-namespace.yaml
```

#### postgresql 
Postgresql is the chosen one here. This workload represents perfectly the concept of stateful application as we wish to keep the data in through any failure or life-cycle events. To create such specific workload, a statefulset configuration will be used:
```yaml
--- # Service will allow to expose the postgresql server service to access internally
apiVersion: v1
kind: Service
metadata:
  name: foodmag-app-db
  namespace: foodmag-app
  labels:
    app: foodmag-app-db
    env: prod
spec:
  type: ClusterIP
  ports:
   - port: 5432
  selector:
    app: foodmag-app-db
    env: prod
--- # StatefullSet is a definition the application and volumes to be used
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: foodmag-app-db
  namespace: foodmag-app
  annotations:
    backup.velero.io/backup-volumes: foodmag-app-db-pvc
spec:
  selector:
    matchLabels:
      app: foodmag-app-db
      env: prod
  serviceName: foodmag-app-db-service
  replicas: 1
  template:
    metadata:
      labels:
        app: foodmag-app-db
        env: prod
    spec:
      containers:
        - name: foodmag-app-db
          image: postgres
          ports:
            - containerPort: 5432
              name: foodmag-app-db
          env:
            - name: POSTGRES_DB
              value: foodmagappdb
            - name: POSTGRES_USER
              value: foodmagapp
            - name: POSTGRES_PASSWORD
              value: foodmagpassword
            - name: PGDATA
              value: /var/lib/postgresql/data/pgdata
          volumeMounts:
            - name: foodmag-app-db-pvc
              mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
    - metadata:
        name: foodmag-app-db-pvc
        labels:
          app: foodmag-app-db
          env: prod
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: "storageos-rep-1"
        resources:
          requests:
            storage: 1Gi
```
To apply this satefulset manifest, run the following:
```
kubectl apply -f cd/foodmag-db-statefulset.yaml
```

#### drupal 
Similarly to PostgreSQL, Drupal has also to record states because of its deployment style and also its multi-site, document library, themes, and other potential features. To create such specific workload, a statefulset configuration will be used:
```yaml
--- # Service will allow to expose the cms externally to the load balancer
apiVersion: v1
kind: Service
metadata:
  name: foodmag-app-fe-service
  namespace: foodmag-app
  labels:
    app: foodmag-app-fe
    env: prod
spec:
  type: NodePort
  ports:
   - port: 80
     nodePort: 30080
  selector:
    app: foodmag-app-fe
    env: prod
--- # StatefullSet is a definition the application and volumes to be used
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: foodmag-app-fe
  namespace: foodmag-app
  annotations:
    backup.velero.io/backup-volumes: foodmag-app-fe-pv
spec:
  selector:
    matchLabels:
      app: foodmag-app-fe
      env: prod
  serviceName: foodmag-app-fe-service
  replicas: 1
  template:
    metadata:
      labels:
        app: foodmag-app-fe
        env: prod
    spec:
      initContainers:
        - name: fix-perms
          image: drupal:latest
          command: ['/bin/bash','-c']
          args: ['/bin/cp -R /var/www/html/sites/ /data/; chown -R www-data:www-data /data/']
          volumeMounts:
            - name: foodmag-app-fe-pv
              mountPath: /data
      containers:
        - name: foodmag-app-fe
          image: drupal:latest
          ports:
            - containerPort: 30080
              name: foodmag-app-fe
          volumeMounts:
            - name: foodmag-app-fe-pv
              mountPath: /var/www/html/modules
              subPath: modules
            - name: foodmag-app-fe-pv
              mountPath: /var/www/html/profiles
              subPath: profiles
            - name: foodmag-app-fe-pv
              mountPath: /var/www/html/themes
              subPath: themes
            - name: foodmag-app-fe-pv
              mountPath: /var/www/html/sites
              subPath: sites
  volumeClaimTemplates:
    - metadata:
        name: foodmag-app-fe-pv
        labels:
          app: foodmag-app-fe
          env: prod
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: "storageos-rep-1"
        resources:
          requests:
            storage: 1Gi
```
To apply this satefulset manifest, run the following:
```
kubectl apply -f cd/foodmag-fe-statefulset.yaml
```

At this stage, to access the freshly deployed environment, it will require to search on which node the workload is running to get its IP access it via the relevant ports.
Another approach which is less time consumming would be to simply perform a local forward to access it like we would be within the same network segment:
```
kubectl port-forward svc/foodmag-app-fe-service -n foodmag-app 8081:80 [--address local_ip_address] 
```

What about the storage layer? Persistent volume have been claimed by the workloads and can be checked via:
```
kubectl get pvc -n foodmag-app
```
and from a StorageOS perspective if more details are needed:
```
kubectl exec -n kube-system -it cli -- storageos get volumes -A
```


### ingress and cert-manager (optional)
Note: this part is depending of the type of Kubernetes cluster deployment. This repo example has been tested successfully with DigitalOcean Kubernetes Service.  
Using helm, the following commands have to be perfomed:
```
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install nginx-ingress ingress-nginx/ingress-nginx --set controller.publishService.enabled=true
```
Verify the deployment of the load balancer for readiness:
```
kubectl --namespace default get services -o wide -w nginx-ingress-ingress-nginx-controller
```
Once the nginx ingress is deployed successfully, deploying cert-manager will allow to provide with TLS termination dynamically provisioned with Let's Encrypt:
```
kubectl create namespace cert-manager
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install cert-manager jetstack/cert-manager --namespace cert-manager --version v1.2.0 --set installCRDs=true
```
Once cert-manager is deployed, a manifest has to be applied to configure the certificate issuer (see the file certmanager_issuer.yaml in the directory extra):
```yaml 
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: doks-cert
spec:
  acme:
    # Email address used for ACME registration
    email: your@email
    server: https://acme-v02.api.letsencrypt.org/directory
    privateKeySecretRef:
      # Name of a secret used to store the ACME account private key
      name: doks-cert-private-key
    # Add a single challenge solver, HTTP01 using nginx
    solvers:
    - http01:
        ingress:
          class: nginx
```

### argocd (optional)
Deploying ArgoCD to illustrate the concept of Continuous Delivery using GitOps.
```
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```
Recovering credentials:
``` 
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d 
```
Connecting to the UI via a port forwarding:
```
kubectl port-forward svc/argocd-server -n argocd 8080:443
```
Note: a ingress configuration example is available in the folder "extra"