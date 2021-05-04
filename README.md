![argrocd-sync](https://argocd.doks.myshiny.space/api/badge?name=myshiny-app&revision=true)

## database-as-a-Service (DBaaS)
This repository content is used to illustrate the usage of persistent storage within Kubernetes when migrating a stateful legacy application leveraging [StorageOS](https://storageos.com) as a cloud native storage backend.


## prerequisites 
The only one requirement is to have a running kubernetes cluster deployed either on-prem or in any cloud providers. 

## preparing the cluster
### argocd
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




k get all -n myshiny-app -o wide
k port-forward svc/myshiny-app-fe-service -n myshiny-app 8081:80 --address
k delete namespace myshiny-app 


bkps	
OKWQ6SNKQ3URNC2VER6G  
Secret	
ygD0kKCSNT1S5n31CkW+VvzHhJf9p9xn5l5hMtpHQ14



velero install                                                                                   \
--provider aws                                                                                   \
--plugins velero/velero-plugin-for-aws:v1.2.0                                                    \
--bucket storageos-s3-backup                                                                                  \
--secret-file ./credentials-Velero                                                               \
--use-volume-snapshots=false                                                                     \
--backup-location-config region=do,s3ForcePathStyle="true",s3Url=https://bkps.myshiny.space \
--use-restic
