# 201 - anatomy of a stateful deployment

# foodmag - a blog about food!

Within 101, a simple Pod definition was used to provision a container with a persistent volume,  deleting the pod, the action is direct and definitive but still let the persistent volume usable.  

From a k8s standpoint, a stateful application is a first class citizen and as such has it's own definition called a [StatefulSet](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/).  
Note that deleting a StatefulSet, Pod(s) are not deleted but scaled down to 0. Scaling down a Satefulet to 0 could provide a ordered and graceful termination of the pods.

In this chapter, a typical CMS application will be deployed using a StatefulSet and PVCs. This CMS is composed of:
- a web app written in PHP called Drupal
- a database using PostgreSQL 
- Drupal food magazine demo data will be used to highlight persistent storage

Drupal is well know solution used by enterprise companies. Being written in PHP, it requires multiple dependencies like system & PHP libraries, an Apache server with PHP module, and a database service. The actual [installation guide](https://www.drupal.org/docs/installing-drupal) is quite long and extensive.

The next sections will provide a breakdown of the different configuration objects necessary to have a working stateful application for production grade usage.

The following diagram shows the expected results, each discrete elements will be explained and configured:  

![foodmag overview](images/foodmag-app_overview.png)

## the old empire
With this short section, let's imagine would it would be done provision, configure and deploy such a simple architecture. This breakdown could be considered as a worklow from an automation and release tooling perspective:

1. define two network zones (nightmare time!)
1. get IP addresses (hoping there is an IPAM)
1. configure DNS
1. provision at least 2 (virtual) machines
1. update the operating systems to the latest corporate release if golden image is not yet
1. configure the operating systems with the latest and greatest access policies
1. deploy backup, security and auditing packages
1. deploy observability packages
1. configure additional storage for both (virtual) machines
1. deploy DB service on one (virtual)machine 
1. deploy CMS service on one (virtual)machine
1. check connectivity and adjust firewall
1. request SSL certificate for external exposure
1. configure load balancer for external exposure
1. check external exposure
1. Dev team to access, verify and confirm all good and most likely requests some additional libs or packages to be deployed
1. Dev team to load the contents 
1. configure CMS & DB backup
1. configure system level backup

By experience, the above would have a lead time between 1 week (impressive) up to months!  

## the new republic
Taking the above into consideration, let's try to build a table to address each elements from one world to another. 

|tasks|k8s|
|-----|---|
|1,2,3,7,8,12,13*,14*|abstracted by k8s platform
|4,5,6|container spec definition of StatefulSet & rollout strategies
|     |container image management for life-cycle
|9    |volumeMounts settings within the container & volumeClaimTemplates spec
|10,11|container spec definition of StatefulSet
|     |container image management for life-cycle
|15,16,17|abstracted by Continuous Deployment
|18   |Ops

Notes: 
- ```abstracted by k8s platform``` means the necessary components are deployed and available to developers using k8s API object constructs like annotations, labels, API objects, ... 
- ```*``` should be totally abstracted but some organizations wants control SSL and load balancer configuration mostly because of lack of trust and/or automation skills.

# statful application deployment

## namespace - segmentation and multi-tenancy
k8s by definition is a platform to be shared with many teams to deploy many workloads. To avoid chaos, disaster and entropy, there is a need to give a ```space``` for each team projects to exist without impacting any others. This first segmenation and multi-tenancy attribute is called a ```namespace``` (also known as ```project``` for other k8s distributions) and provides features like:
- multi tenancy
- grouping objects together  
- cluster resources definition via quota
- explicit cluster resource partitioning from other namespace

 Official documentation: [namespace](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/)

k8s has a bunch of built-in namespaces, numbers are varying by k8s distributions and added components, to provide a clear segmentation between k8s components and workloads.

If not explicitly defined, any deployment will happen in the namespace called ```default```. This is obviously a bad practices and only appreciated when doing demo or introduction like in 101.  
Here, a namespace called ```foodmag-app``` will be created to group all the related resources for the stateful application. To create a namespace, the following configuration file can be applied:

```foodmag-app-namespace.yaml```:
```yaml
---
apiVersion: v1
kind: Namespace
metadata:
  name: foodmag-app
```
The above YAML is a perfect small sized example to present the structure:  
1. reference to an API version (it could also refer to a specific API set like ```apps/v1```)
1. reference to an API object, ```Namespace```, CRUD operations
1. reference to metadata defining a name for the obeject 
1. indentation, indentation, indentation!

To apply this configuration file, run the following:
```
kubectl apply -f doc/201/foodmag-app/v1/foodmag-app-namespace.yaml
namespace/foodmag-app created
```
The results will be followings:
```
kubectl get namespaces
NAME                 STATUS   AGE
default              Active   3d2h
foodmag-app          Active   16s
kube-node-lease      Active   3d2h
kube-public          Active   3d2h
kube-system          Active   3d2h
storageos-etcd       Active   2d11h
```

## statefulset - the desired state of a stateful application
The concept has been introduced at beginning of this chapter. For more details, do not hesitate to browse the [k8s statefulset documentation](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/). With no further suspens, here is the YAML for the StatefulSet with some comments.

```foodmag-app-statefulset.yaml```:
```yaml
apiVersion: apps/v1
kind: StatefulSet                                       #|> Calling the StatefulSet API object.
metadata:
  name: foodmag-app                                     #|> The name of our application, it will be used as a reference key for all related objects.
  namespace: foodmag-app                                #|> The name space in which all (almost) objects will exist.
spec:
  selector:
    matchLabels:                                        #|> Another kind of labels to refer to when configuring other objects like service as example
      app: foodmag-app
      env: prod
  serviceName: foodmag-app                              #|> ServiceName is the DNS name, serviceName-[id], to address the application with
  replicas: 1                                           #|> Number of instances to scale to; if 2, pods will have 2 instances running on two different nodes.
  template:                                             #|> The template is used to define the desired state of the application
    metadata:
      labels:                                           #|> Labels allows to ease searches like "show all prod objects"
        app: foodmag-app
        env: prod
    spec:
      containers:                                       #|> This section is used to define each container desired state.
        - name: foodmag-app-sql                         #|  Desired state is: a container called foodmag-app-sql based on the latest image of postgres.
          image: postgres:latest                        #|
          ports:
            - containerPort: 5432                       #|> This will inform that postgres has the port 5432 can be exposed and a name is given.
              name: foodmag-app-sql                     
          env:                                          #|> This will define environment variables that the container image can leverage to configure
            - name: POSTGRES_DB                         #|  the services running in it like here about setting up postgres. 
              value: foodmagappdb                       #|  
            - name: POSTGRES_USER                       #|
              value: foodmagapp                         #|
            - name: POSTGRES_PASSWORD                   #|
              value: foodmagpassword                    #|
            - name: PGDATA                              #|
              value: /var/lib/postgresql/data/pgdata    #|
          volumeMounts:                                 #|> This will define the appropriate PVC and its mount point.
            - name: foodmag-app-sql-pvc                 #|
              mountPath: /var/lib/postgresql/data       #|
        - name: foodmag-app-cms                         #|> Second container for the cms part.
          image: drupal:latest
          ports:
            - containerPort: 30080
              name: foodmag-app-cms
          volumeMounts:                                 #|> This will define the appropriate PVC and its mount point.
            - name: foodmag-app-cms-pvc                 #|  Note the subPath is a special construct to allow a single PVC to have multiple
              mountPath: /var/www/html/modules          #|  mount points for the same container. 
              subPath: modules                          #|
            - name: foodmag-app-cms-pvc                 #|
              mountPath: /var/www/html/profiles         #|
              subPath: profiles                         #|
            - name: foodmag-app-cms-pvc                 #|
              mountPath: /var/www/html/themes           #|
              subPath: themes                           #|
  volumeClaimTemplates:                                 #|> A special PVC template used to define the desired state for persistent storage.
    - metadata:                 
        name: foodmag-app-sql-pvc                       #|> PVC name prefix resulting in prefix-ServiceName-[id]
        labels:
          app: foodmag-app
          env: prod
      spec:
        accessModes: ["ReadWriteOnce"]                  #|> AccessMode is a very important topics. It will be covered later in this section.
        storageClassName: "storageos-rep-1"             #|> This will define the appropriate storageClass with features like replica, encryption, ...
        resources:
          requests:
            storage: 5Gi                                #|> This will define the provisioned disk size of the volume.
    - metadata:
        name: foodmag-app-cms-pvc                       #|> Second PVC definition
        labels:
          app: foodmag-app
          env: prod
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: "storageos-rep-1"
        resources:
          requests:
            storage: 5Gi
```

To apply this configuration file, run the following:
```
kubectl apply -f doc/201/foodmag-app/v1/foodmag-app-statefulset.yaml 
```
The results will be followings:
```
kubectl get all -n foodmag-app -o wide
```
```
NAME                READY   STATUS    RESTARTS   AGE   IP            NODE          NOMINATED NODE   READINESS GATES
pod/foodmag-app-0   2/2     Running   0          11m   10.244.0.29   dbaas-8rowa   <none>           <none>

NAME                           READY   AGE   CONTAINERS                        IMAGES
statefulset.apps/foodmag-app   1/1     13m   foodmag-app-sql,foodmag-app-cms   postgres:latest,drupal:latest
```

## statefulset - what's in the box?
At the current stage, the StatefulSet created a couple of objects:
- 1 StatefulSet
- 1 Pod with 2 containers
- 2 Persistent Volume Claims
- 2 Persistent Volumes 

How does it translate into a CLI investigation? 

```StatefulSet```:
```
kubectl describe -n foodmag-app statefulset.apps/foodmag-app
```
```
Name:               foodmag-app
Namespace:          foodmag-app
CreationTimestamp:  Mon, 10 May 2021 11:18:35 +0200
Selector:           app=foodmag-app,env=prod
Labels:             <none>
Annotations:        <none>
Replicas:           1 desired | 1 total
Update Strategy:    RollingUpdate
  Partition:        0
Pods Status:        1 Running / 0 Waiting / 0 Succeeded / 0 Failed
Pod Template:
  Labels:  app=foodmag-app
           env=prod
  Containers:
   foodmag-app-sql:
    Image:      postgres:latest
    Port:       5432/TCP
    Host Port:  0/TCP
    Environment:
      POSTGRES_DB:        foodmagappdb
      POSTGRES_USER:      foodmagapp
      POSTGRES_PASSWORD:  foodmagpassword
      PGDATA:             /var/lib/postgresql/data/pgdata
    Mounts:
      /var/lib/postgresql/data from foodmag-app-sql-pvc (rw)
   foodmag-app-cms:
    Image:        drupal:latest
    Port:         30080/TCP
    Host Port:    0/TCP
    Environment:  <none>
    Mounts:
      /var/www/html/modules from foodmag-app-cms-pvc (rw,path="modules")
      /var/www/html/profiles from foodmag-app-cms-pvc (rw,path="profiles")
      /var/www/html/themes from foodmag-app-cms-pvc (rw,path="themes")
  Volumes:  <none>
Volume Claims:
  Name:          foodmag-app-sql-pvc
  StorageClass:  storageos-rep-1
  Labels:        app=foodmag-app
                 env=prod
  Annotations:   <none>
  Capacity:      5Gi
  Access Modes:  [ReadWriteOnce]
  Name:          foodmag-app-cms-pvc
  StorageClass:  storageos-rep-1
  Labels:        app=foodmag-app
                 env=prod
  Annotations:   <none>
  Capacity:      5Gi
  Access Modes:  [ReadWriteOnce]
Events:          <none>
```

```Pod```
```
kubectl describe -n foodmag-app pod/foodmag-app-0
```
```
Name:         foodmag-app-0
Namespace:    foodmag-app
Priority:     0
Node:         dbaas-8row6/10.110.0.9
Start Time:   Sat, 15 May 2021 12:43:14 +0200
Labels:       app=foodmag-app
              controller-revision-hash=foodmag-app-74b7569896
              env=prod
              statefulset.kubernetes.io/pod-name=foodmag-app-0
Annotations:  <none>
Status:       Running
IP:           10.244.0.246
IPs:
  IP:           10.244.0.246
Controlled By:  StatefulSet/foodmag-app
Containers:
  foodmag-app-sql:
    Container ID:   containerd://a10ecf729e42881e983b91e3614d0a6ae35a35f2db7d530e0f022cd76eb33e83
    Image:          postgres:latest
    Image ID:       docker.io/library/postgres@sha256:117c3ea384ce21421541515edfb11f2997b2c853d4fdd58a455b77664c1adc20
    Port:           5432/TCP
    Host Port:      0/TCP
    State:          Running
      Started:      Sat, 15 May 2021 12:43:19 +0200
    Ready:          True
    Restart Count:  0
    Environment:
      POSTGRES_DB:        foodmagappdb
      POSTGRES_USER:      foodmagapp
      POSTGRES_PASSWORD:  foodmagpassword
      PGDATA:             /var/lib/postgresql/data/pgdata
    Mounts:
      /var/lib/postgresql/data from foodmag-app-sql-pvc (rw)
      /var/run/secrets/kubernetes.io/serviceaccount from default-token-d8d7d (ro)
  foodmag-app-cms:
    Container ID:   containerd://c4d4c9b2ba0ee82ddc729dedf8636ef3c25d483d04fcadf9c0335c1916dffd75
    Image:          drupal:latest
    Image ID:       docker.io/library/drupal@sha256:1cbebc5ce01d094d772338a12da507be6862a1318a7bb45c350d462f97d3500f
    Port:           30080/TCP
    Host Port:      0/TCP
    State:          Running
      Started:      Sat, 15 May 2021 12:43:20 +0200
    Ready:          True
    Restart Count:  0
    Environment:    <none>
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from default-token-d8d7d (ro)
      /var/www/html/modules from foodmag-app-cms-pvc (rw,path="modules")
      /var/www/html/profiles from foodmag-app-cms-pvc (rw,path="profiles")
      /var/www/html/themes from foodmag-app-cms-pvc (rw,path="themes")
Conditions:
  Type              Status
  Initialized       True 
  Ready             True 
  ContainersReady   True 
  PodScheduled      True 
Volumes:
  foodmag-app-sql-pvc:
    Type:       PersistentVolumeClaim (a reference to a PersistentVolumeClaim in the same namespace)
    ClaimName:  foodmag-app-sql-pvc-foodmag-app-0
    ReadOnly:   false
  foodmag-app-cms-pvc:
    Type:       PersistentVolumeClaim (a reference to a PersistentVolumeClaim in the same namespace)
    ClaimName:  foodmag-app-cms-pvc-foodmag-app-0
    ReadOnly:   false
  default-token-d8d7d:
    Type:        Secret (a volume populated by a Secret)
    SecretName:  default-token-d8d7d
    Optional:    false
QoS Class:       BestEffort
Node-Selectors:  <none>
Tolerations:     node.kubernetes.io/not-ready:NoExecute op=Exists for 300s
                 node.kubernetes.io/unreachable:NoExecute op=Exists for 300s
Events:
  Type     Reason                  Age        From                     Message
  ----     ------                  ----       ----                     -------
  Normal   Scheduled               <invalid>  storageos-scheduler      Successfully assigned foodmag-app/foodmag-app-0 to dbaas-8row6
  Normal   SuccessfulAttachVolume  <invalid>  attachdetach-controller  AttachVolume.Attach succeeded for volume "pvc-101a37ba-ccd3-456d-9657-c3a4749bb94b"
  Normal   SuccessfulAttachVolume  <invalid>  attachdetach-controller  AttachVolume.Attach succeeded for volume "pvc-d3b7aaa5-1ea1-4684-8679-0299427ad2f3"
  Normal   Pulling                 <invalid>  kubelet                  Pulling image "postgres:latest"
  Normal   Created                 <invalid>  kubelet                  Created container foodmag-app-sql
  Normal   Pulled                  <invalid>  kubelet                  Successfully pulled image "postgres:latest" in 887.676858ms
  Normal   Started                 <invalid>  kubelet                  Started container foodmag-app-sql
  Normal   Pulling                 <invalid>  kubelet                  Pulling image "drupal:latest"
  Normal   Pulled                  <invalid>  kubelet                  Successfully pulled image "drupal:latest" in 938.777937ms
  Normal   Created                 <invalid>  kubelet                  Created container foodmag-app-cms
  Normal   Started                 <invalid>  kubelet                  Started container foodmag-app-cms
```

```PVC```:
```
kubectl get pvc -n foodmag-app -o wide
```
```
NAME                                STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS      AGE   VOLUMEMODE
foodmag-app-cms-pvc-foodmag-app-0   Bound    pvc-d3b7aaa5-1ea1-4684-8679-0299427ad2f3   5Gi        RWO            storageos-rep-1   46m   Filesystem
foodmag-app-sql-pvc-foodmag-app-0   Bound    pvc-101a37ba-ccd3-456d-9657-c3a4749bb94b   5Gi        RWO            storageos-rep-1   46m   Filesystem
```

```PV```
```
kubectl get pv -n foodmag-app -o wide
```
```
NAME                                       CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM                                           STORAGECLASS      REASON   AGE     VOLUMEMODE
pvc-101a37ba-ccd3-456d-9657-c3a4749bb94b   5Gi        RWO            Delete           Bound    foodmag-app/foodmag-app-sql-pvc-foodmag-app-0   storageos-rep-1            49m     Filesystem
pvc-3e303b09-dc6f-4cf7-b46a-d368463f629c   5Gi        RWO            Delete           Bound    default/pvc-2                                   storageos-rep-1            6d20h   Filesystem
pvc-d3b7aaa5-1ea1-4684-8679-0299427ad2f3   5Gi        RWO            Delete           Bound    foodmag-app/foodmag-app-cms-pvc-foodmag-app-0   storageos-rep-1            49m     Filesystem
pvc-f4af80a7-1224-4641-abae-8403e3c9827b   5Gi        RWO            Delete           Bound    default/pvc-1                                   fast                       8d      Filesystem
```
Note that, even if explicitly using ```foodmag-app``` namespace arguments, some objects can't be not attached to/filtered with a specific namespace like the persistent volumes created out of the PVCs. The above output shows all existing persistem volumes from 101 and 201 despite the ```-n foodmag-app```.  
This illustrates the concept of segmentation of resource opening doors to multi-tenancy. This will be investigated further within the Security chapter (501).


## statefulset - where is my foodmag?
Despite the fact that both containers have been deployed successfully with their persistent storage and having ports being defined, there is are no exposure for the outside world to access the CMS front-end. 

To do so, a service object needs offer exposure from the outside world to the appropriate container, in this case the ```foodmag-app-cms```. This can be done via the following YAML code:

```foodmag-app-cms-service.yaml```:
```yaml 
---
apiVersion: v1
kind: Service
metadata:
  name: foodmag-app-cms-service
  namespace: foodmag-app
  labels:
    app: foodmag-app
    env: prod
spec:
  type: NodePort
  ports:
   - port: 80
     nodePort: 30080
  selector:
    app: foodmag-app
    env: prod
```

To apply this configuration file, run the following:
```
kubectl apply -f doc/201/foodmag-app/v1/foodmag-app-cms-service.yaml
``` 
What about the ```foodmag-app-sql```? Good question! This is indeed the same issue but with a difference to the exposure radius. While the CMS needs to be exposed to the outside world, the database has to be exposed only to the CMS. This can be done via the following YAML code: 

```foodmag-app-sql-service.yaml```:
```yaml
---
apiVersion: v1
kind: Service
metadata:
  name: foodmag-app-sql-service
  namespace: foodmag-app
  labels:
    app: foodmag-app
    env: prod
spec:
  type: ClusterIP
  ports:
   - port: 5432
  selector:
    app: foodmag-app
    env: prod
```

The results will be the followings:
```
kubectl apply -f doc/201/foodmag-app/v1/foodmag-app-sql-service.yaml 
```
The results will be the followings:
```
kubectl get service -n foodmag-app -o wide
```
```
NAME                      TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE   SELECTOR
foodmag-app-cms-service   NodePort    10.245.147.20   <none>        80:30080/TCP   86m   app=foodmag-app,env=prod
foodmag-app-sql-service   ClusterIP   10.245.7.31     <none>        5432/TCP       86m   app=foodmag-app,env=prod
```
The above shows:
- the cms service being exposed on TCP port 80 on a node redirecting traffic to the container TCP port 30080.
- the sql service being exposed on TCP port 5432 using a cluster IP.
- the selector with available labels to ensure proper connection to the proper StatefulSet (see previous section ```describe```).

Notes:
- As discussed above, due to the exposure radius, the CMS use a [k8s service](https://kubernetes.io/docs/concepts/services-networking/service/) type ```NodePort``` to expose the service to the outside world while the database is using a ```ClusterIP``` to expose the service only within the cluster bubble.
- At the current state, no external IP is currently assigned, which is expected. 
- The Service manifests could be added at the StatefulSet one to provide a single configuration file.

For the current time, a forwarding process will use to access the CMS front-end on a local machine:

```
ip a
```
```
5: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 00:15:5d:31:47:14 brd ff:ff:ff:ff:ff:ff
    inet 172.22.135.113/20 brd 172.22.143.255 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 fe80::215:5dff:fe31:4714/64 scope link 
       valid_lft forever preferred_lft forever
```
```
kubectl port-forward -n foodmag-app service/foodmag-app-cms-service 8080:80 --address 172.22.135.113
```

Open a browser with as URL ```172.22.135.113:8080``` which should show the following:  

Welcome page to install the CMS
<!-- ![foodmag-app browser](images/foodmag-app_browser-01.png) -->

Select Demo to insert the foodmag data
<!-- ![foodmag-app browser](images/foodmag-app_browser-02.png) -->

Provide the database details (or see env details from the statefulset if modified): 
- select PostgreSQL
- database name: foodmagappdb
- database username: foodmagapp
- database password: foodmagpassword
- database service name: foodmag-app-db

<!-- ![foodmag-app browser](images/foodmag-app_browser-03.png) -->

Installation in progress (with more questions about name, email,...):
<!-- ![foodmag-app browser](images/foodmag-app_browser-04.png) -->

Tadadaaaaaa! Here our website!
<!-- ![foodmag-app browser](images/foodmag-app_browser-05.png) -->

## Scale up, Scale down... Scale up, Scale down
Scaling up/down is handy where there is a need 


