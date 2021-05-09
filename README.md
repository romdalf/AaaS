# anything-as-a-Service (AaaS)
This repository content is used to illustrate the anything-as-a-service with the migration of a stateful/legacy application on kubernetes (k8s) with persistent storage using [StorageOS](https://storageos.com) as cloud native stroage backend.  

The content is divided in chapters providing a ramping up from basic to advanced hands-on. The only knowledge requirements at the start are basic linux skills and container understanding. 

[101 - basics of k8s and persistent storage](doc/101/) ![done](https://img.shields.io/badge/status-100%25-green)     
- build knowledge about k8s YAML configuration files                                
- use persistent storage with a cloud native software defined storage solution   

[201 - anatomy of a stateful deployment](doc/201/) ![draft](https://img.shields.io/badge/status-50%25-yellow)
- deploy using cloud native pattern a stateful application composed of:             
  - Drupal; a CMS using both local filesystem and a database for data
  - PostgreSQL; a relational database  
- scaling a stateful application      

[301 - gitops to the rescue](doc/301) ![0%](https://img.shields.io/badge/status-0%25-red)
- use a continuous deployment approach based on GitOps principals

[401 - multi-cluster capabilities]() ![draft](https://img.shields.io/badge/status-0%25-red)
- provide multi-cluster capabilities from an application workload perspective
- provide multi-cluster capabilities from a DR-like perspective

[501 - securing a stateful deployment]() ![draft](https://img.shields.io/badge/status-0%25-red)
- secure the deployment 
- secure the application
- secure the persistent data

[Capstone]() ![draft](https://img.shields.io/badge/status-0%25-red)
- migrate an existing stateful application from a legacy infrastructure to k8s using cloud patterns

S