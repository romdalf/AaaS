![argrocd-sync](https://argocd.doks.myshiny.space/api/badge?name=foodmag-app&revision=true)

# anything-as-a-Service (AaaS)
This repository content is used to illustrate the deployment or migration of a stateful/legacy application on Kubernetes (k8s) with persistent storage using [StorageOS](https://storageos.com) as cloud native stroage backend.  
The stateful application is composed of:
- Drupal; a CMS using both local filesystem and a database for data
- PostgreSQL; a relational database 

The content is built as a step by step approach to grow knowledge from basic to advanced. The only knowledge requirements are basic linux and container with docker. 

[101 - basics of persistent storage on k8s](doc/101/README.md) 
[201 - anatomy of a stateful deployment](doc/201/README.md)

