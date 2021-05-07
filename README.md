![argrocd-sync](https://argocd.doks.myshiny.space/api/badge?name=foodmag-app&revision=true)

# database-as-a-Service (DBaaS)
This repository content is used to illustrate the deployment or migration of a stateful/legacy application on Kubernetes (k8s) with persistent storage using [StorageOS](https://storageos.com) as cloud native stroage backend. The stateful application is composed of Drupal using PostgreSQL. 

The content is built as a step by step approach to grow knowledge from basic to advanced. The only knowledge requirements are basic linux and container with docker. 

## preparing the cluster
A good 50% of this repo could be done without having a real k8s cluster and using instead minikube or any similar one node k8s project. However, to make it through the full guide, it would be recommended, especially when looking into persistent storage.  

To deploy a k8s cluster, 3 VMs would be required, each having 2vCPU/2GB RAM/20GB disk. There are a couple of ways to deploy a 3 node k8s cluster without to much of hazzle like [k3s](https://k3s.io/) providing the user with a very lightweight k8s option consuming very little resources but yet offering the basic magic power of k8s.

For the purposes of this guide, a k8s cluster deployed within DigitalOcean is used. The overall guide should be agnostic of any k8s cluster provider (aks, eks, ...). 

### connecting to k8s
The first component to connect to k8s platform is [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/), the link provides the installation methodology based on the operating system.  
The second component to connect is a config file also referred as kubeconfig which presents itself as yaml file. If on linux machine, the file is usually found in: 
``` 
ls -al ~/.kube/
```
The file can save in that path under the name config or any other that can be exported as an environment variable as such:
```
export KUBECONFIG=~/.kube/file_name 
```
like so if the file was called ```digitalocean```: 
```
export KUBECONFIG=~/.kube/digitalocean
```
Once exported, ```kubectl``` can be used to verify connectivity:
```
kubectl get nodes
NAME          STATUS   ROLES    AGE   VERSION
dbaas-8row6   Ready    <none>   54m   v1.20.2
dbaas-8rowa   Ready    <none>   54m   v1.20.2
dbaas-8rowe   Ready    <none>   54m   v1.20.2
```
This output shows a 3 node cluster running a kubernetes version 1.20.2 freshly deployed ready to schedule workload.

### deploying a persistent storage solution
K8s is designed to support stateless workload natively. To support stateful workload, a persistent storage solution has to be implemented in order to provide a volume to be consummed by the application. The volume will survice the application rescheduling, scaling up/down, or deletion.  
[StorageOS](https://storageos.com) is cloud native, software-defined storage for running containerized applications in production, running in the cloud, on-prem and in hybrid/multi-cloud environments. 

StorageOS has a free forever developer tier that can be used for such environment or for a development platform. A [self evaluation guide](https://docs.storageos.com/docs/self-eval/) provides the user with a script to do a rapid deployment which will consume local disk space on nodes while providing a fully distributed persistent storage for stateful applications. Remember, this is not suited for a production deployment but performed for testing. 

From the admin machine where ```kubectl``` is connected with freshly deployed k8s cluster, the following script can be ran:
```
curl -sL https://storageos.run | bash
```
Wait! Be brave, don't just copy/paste the above... curl first, review and then execute.

The output would like like:
```
rovandep in ~ ❯ curl -sL https://storageos.run |bash
Welcome to the StorageOS quick installation script.
I will install StorageOS version v2.4.0-rc.1 into
namespace kube-system now. If I encounter any errors
I will stop immediately.

Creating etcd namespace storageos-etcd
namespace/storageos-etcd created
Creating etcd ClusterRole and ClusterRoleBinding
clusterrolebinding.rbac.authorization.k8s.io/etcd-operator created
clusterrole.rbac.authorization.k8s.io/etcd-operator created
Creating etcd operator Deployment
deployment.apps/etcd-operator created
Creating etcd cluster in namespace storageos-etcd
etcdcluster.etcd.database.coreos.com/storageos-etcd created
Installing StorageOS Operator version v2.4.0-rc.1
Warning: apiextensions.k8s.io/v1beta1 CustomResourceDefinition is deprecated in v1.16+, unavailable in v1.22+; use apiextensions.k8s.io/v1 CustomResourceDefinition
customresourcedefinition.apiextensions.k8s.io/storageosclusters.storageos.com created
customresourcedefinition.apiextensions.k8s.io/storageosupgrades.storageos.com created
customresourcedefinition.apiextensions.k8s.io/jobs.storageos.com created
customresourcedefinition.apiextensions.k8s.io/nfsservers.storageos.com created
namespace/storageos-operator created
clusterrole.rbac.authorization.k8s.io/storageos-operator created
serviceaccount/storageoscluster-operator-sa created
Warning: rbac.authorization.k8s.io/v1beta1 ClusterRoleBinding is deprecated in v1.17+, unavailable in v1.22+; use rbac.authorization.k8s.io/v1 ClusterRoleBinding
clusterrolebinding.rbac.authorization.k8s.io/storageoscluster-operator-rolebinding created
deployment.apps/storageos-cluster-operator created
Operator installed, waiting for pod to become ready
StorageOS Operator installed successfully
Creating Secret definining the API Username and Password
secret/storageos-api created
Installing StorageOS Cluster version v2.4.0-rc.1
storageoscluster.storageos.com/self-evaluation created
Waiting for StorageOS pods to become ready
Waiting for StorageOS pods to become ready
Waiting for StorageOS pods to become ready
Waiting for StorageOS pods to become ready
Waiting for StorageOS pods to become ready
StorageOS Cluster installed successfully
Deploying the StorageOS CLI as a pod in the kube-system namespace
pod/cli created
Waiting for the cli pod to become ready
StorageOS CLI pod is running
Your StorageOS Cluster now is up and running!

Now would be a good time to deploy your first volume - see
https://docs.storageos.com/docs/self-eval/#a-namestorageosvolumeaprovision-a-storageos-volume
for an example of how to mount a StorageOS volume in a pod

Don't forget to license your cluster - see https://docs.storageos.com/docs/operations/licensing/

This cluster has been set up with an etcd based on ephemeral
storage. It is suitable for evaluation purposes only - for
production usage please see our etcd installation nodes at
https://docs.storageos.com/docs/prerequisites/etcd/
```

Let's verify the status of the StorageOS cluster within our k8s cluster:
```
kubectl exec -n kube-system -it cli -- storageos get cluster
ID:           ed08d40e-5035-4270-81bd-2af74d53b5f8
Created at:   2021-05-07T09:32:40Z (2 minutes ago)
Updated at:   2021-05-07T09:32:40Z (2 minutes ago)
Nodes:        3
  Healthy:    3
  Unhealthy:  0
```

## my first app
Before starting to run, let's have a little walk. The following example is from the actual StorageOS self evaluation guide providing two YAML definition for creating a Persistent Volume Claim (PVC) and an application (Pod) that will consume the persistent volume (PV). 

```myfirstpvc.yaml```:
```yaml
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-1
spec:
  storageClassName: "fast"
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
```

The above provides a "voucher" with the name "pvc-1" for the application to get a volume of 5GB out of the storage class called "fast". This would be the most simplistic attempt to explain a PVC.  

```myfirstpod.yaml```: 
```yaml
---
apiVersion: v1
kind: Pod
metadata:
 name: d1
spec:
 containers:
   - name: debian
     image: debian:9-slim
     command: ["/bin/sleep"]
     args: [ "3600" ]
     volumeMounts:
       - mountPath: /mnt
         name: v1
 volumes:
   - name: v1
     persistentVolumeClaim:
       claimName: pvc-1
```

The above provides a blueprint of our application. It tells that we will be getting a debian container base image with a specific nature (9-slim), that we will run a command once up and that we want to redeem our volume voucher and mounting the volume at ```/mnt```.

### storageos
For the puproses of this demo, the Free For Every Developer edition of Storage is used via the automated deployment (note: this deployment method is not suitable for production usage):
```
curl -sL https://storageos.run |bash 
``` 
Once deployed, a new storageClass has to be created using a replica 1 volume:
```yaml
---
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: storageos-rep-1
provisioner: csi.storageos.com
allowVolumeExpansion: true
parameters:
  fsType: ext4
  pool: default
  storageos.com/replicas: "1"
  csi.storage.k8s.io/controller-expand-secret-name: csi-controller-expand-secret
  csi.storage.k8s.io/controller-publish-secret-name: csi-controller-publish-secret
  csi.storage.k8s.io/node-publish-secret-name: csi-node-publish-secret
  csi.storage.k8s.io/provisioner-secret-name: csi-provisioner-secret
  csi.storage.k8s.io/controller-expand-secret-namespace: kube-system
  csi.storage.k8s.io/controller-publish-secret-namespace: kube-system
  csi.storage.k8s.io/node-publish-secret-namespace: kube-system
  csi.storage.k8s.io/provisioner-secret-namespace: kube-system
```

## from legacy deployment to kubenetes stateful workload
### deployment overview
While a legacy workload has to be deployed, the activity will require the full understanding of the infrastructure at all layers including, and not limited to, compute, operating system flavor, storage (both local or remote), networking (DNS, IP, load balancer, firewall, ...), package management, sources, along side potential release management and automation software.  
Considering the above, it is almost impossible to provide a single and unique deployment methodology allowing to deploy in a fully agnostic approach or if only one of the infrastructure component state would change.

Using containers provide from an application standpoint the necessary abstraction layers with a portable image to be deployed on any platform provider running a container runtime like Kubernetes with containerd or cri-o.  
Using Kubernetes provide from an infrastructure standpoint the necessary abstraction layers with the removal of all infrastructure component considerations rendering agnostic any container deployment.

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