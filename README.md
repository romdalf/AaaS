# anything-as-a-Service (AaaS)
This repository content is used to illustrate the anything-as-a-service with the migration of a stateful/legacy application on kubernetes (k8s) with persistent storage using [StorageOS](https://storageos.com) as cloud native stroage backend.  


The end goals are to:
- build knowledge about k8s YAML configuration files 
- use persistent storage with a cloud native software defined storage solution
- deploy using cloud native pattern a stateful application composed of:
  - Drupal; a CMS using both local filesystem and a database for data
  - PostgreSQL; a relational database  
- scaling a stateful application
- use a continuous deployment approach based on GitOps principals 
- provide multi-cluster capabilities from an application workload perspective
- provide multi-cluster capabilities from a DR-like perspective
- secure the application
- migrate an existing stateful application from a legacy infrastructure to k8s

The content is built as a step by step approach to grow knowledge from basic to advanced. The only knowledge requirements at the start are basic linux skills and container understanding. 

[101 - basics of persistent storage on k8s](doc/101/)  
[201 - anatomy of a stateful deployment](doc/201/)  
[301 - gitops to the rescue](doc/301)

