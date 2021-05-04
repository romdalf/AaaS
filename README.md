![argrocd-sync](https://argocd.doks.myshiny.space/api/badge?name=myshiny-app&revision=true)

# database-as-a-Service (DBaaS)
This repository content is used to illustrate the usage of persistent storage within Kubernetes when migrating a legacy application towards a containerized stateful worload leveraging [StorageOS](https://storageos.com) as a cloud native storage backend.


## prerequisites 
The only one requirement is to have a running kubernetes cluster deployed either on-prem or in any cloud providers. 

## preparing the cluster
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

### storageos
For the puproses of this demo, the Free For Every Developer edition of Storage is used via the automated deployment (note: this deployment method is not suitable for production usage):
```
curl -sL https://storageos.run |bash 
``` 
Once deployed, a new storageClass has to be created using a replica 1 volume:
```yaml
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
  name: food-app
```