# anything-as-a-Service (AaaS)
This repository content is used to illustrate the anything-as-a-service with the migration of a stateful/legacy application on kubernetes (k8s) with persistent storage using [StorageOS](https://storageos.com) as cloud native storage backend.  

To ease the reading and practices, cloning this repository is advised as it will give the access to all the configuration files used in each chapters avoiding copy/pasting (headache with YAML) and direct inline modification from CLI or code editor. 

To clone:
```
git clone https://github.com/rovandep/AaaS.git
cd AaaS
```

The content is divided in chapters providing a ramping up from basic to advanced hands-on. The only knowledge requirements at the start are basic linux skills and container understanding. 

| Chapter  | Title | Status |
| --- | --- | --- | 
| [101](doc/101/) | basics of k8s and persistent storage | ![done](https://img.shields.io/badge/status-100%25-green)|
| [201](doc/201/) | anatomy of a stateful deployment | ![draft](https://img.shields.io/badge/status-75%25-yellow) |
| [301]() | gitops to the rescue | ![todo](https://img.shields.io/badge/status-0%25-red) |
| [401]() | multi-cluster capabilities | ![todo](https://img.shields.io/badge/status-0%25-red) |
| [501]() | securing a stateful deployment | ![todo](https://img.shields.io/badge/status-0%25-red) |
| [captsone]() | full migration scenario from legacy to k8s | ![todo](https://img.shields.io/badge/status-0%25-red) |

Fork, PR, Issues are welcome! #sharingiscaring