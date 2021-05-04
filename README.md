![argrocd-sync](https://argocd.doks.myshiny.space/api/badge?name=myshiny-app&revision=true)

## Databas-as-a-Service (DBaaS)
This repository content is used to illustrate the usage of persistent storage within Kubernetes when migrating a stateful legacy application leveraging (StorageOS[https://storageos.com]) as a cloud native storage backend.


### prerequisites 
T

== prepare cluster ==
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
curl -sL https://storageos.run |bash 


== access === 
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d 
kubectl port-forward svc/argocd-server -n argocd 8080:443 --address 




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