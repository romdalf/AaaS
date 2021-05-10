# 201 - anatomy of a stateful deployment

Within 101, a simple Pod definition was used to provision a container with a persistent volume,  deleting the pod, the action is direct and definitive but still let the persistent volume usable.  
From a k8s standpoint, a stateful application is a first class citizen and as such has it's own definition called a [StatefulSet](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/).  
Note that deleting a StatefulSet, Pod(s) are not deleted but scaled down to 0. Scaling down a Satefulet to 0 could provide a ordered and graceful termination of the pods.

In this chapter, a typical CMS application will be deployed using a StatefulSet and PVCs. This CMS is composed of:
- a web app written in PHP called Drupal
- a database using PostgreSQL 
- Drupal food magazine demo data will be used to highlight persistent storage

Drupal is well know solution used by enterprise companies. Being written in PHP, it requires multiple dependencies like system & PHP libraries, an Apache server with PHP module, and a database service. The actual [installation guide](https://www.drupal.org/docs/installing-drupal) is quite long and extensive.

## foodmag-app
The next sections will provide a breakdown of the different configuration objects necessary to have a working stateful application for production grade usage.

The following diagram shows the expected results:  

![foodmag-app overview](images/foodmag-app_overview.png)

## namespace
Also known as project, a [namespace](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/) provides features like:
- multi tenancy
- cluster resources definition via quota
- grouping objects together  

k8s is using a set of default namespaces, names might be different from one k8s flavor to another, to provide a clear segmentation between software components.

A namespace called ```foodmag-app``` will be created to group all the related resources for the stateful application.  

To create a namespace, the following configuration file can be applied:

```foodmag-namespace.yaml```:
```yaml
---
apiVersion: v1
kind: Namespace
metadata:
  name: foodmag-app
```
To apply this configuration file, run the following:
```
kubectl apply -f doc/201/foodmag-app/foodmag-app-namespace.yaml
namespace/foodmag-app created

kubectl get namespaces
NAME                 STATUS   AGE
default              Active   3d2h
foodmag-app          Active   16s
kube-node-lease      Active   3d2h
kube-public          Active   3d2h
kube-system          Active   3d2h
storageos-etcd       Active   2d11h
```

## statefulset 
The concept has been introduced at beginning of this chapter. For more details, do not hesitate to browse the [k8s statefulset documentation](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/). 

With no further suspens, here is the YAML for ```foodmag-app``` with some comments:
```yaml
apiVersion: apps/v1
kind: StatefulSet                               #|> Calling the StatefulSet API object.
metadata:
  name: foodmag-app                             #|> The name of our application, it will be used as a reference key for all related objects.
  namespace: foodmag-app                        #|> The name space in which all the configuration objects will exist.
spec:
  selector:
    matchLabels:                                #|> Although no necessary, labels are a good practice to gather more details about what the app.
      app: foodmag-app
      env: prod
  serviceName: foodmag-app                      #|> ServiceName is the overall DNS name for the stateful application that could be address as serviceName.namespace.svc.cluster.local
  replicas: 1                                   #|> Number of instances to scale to; if 2, pods will have 2 instances running on two different nodes.
  template:                                     #|> The template is used to define the desired state of the application
    metadata:
      labels:
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
            - name: foodmag-app-cms-pvc
              mountPath: /var/www/html/profiles
              subPath: profiles
            - name: foodmag-app-cms-pvc
              mountPath: /var/www/html/themes
              subPath: themes
  volumeClaimTemplates:                                 #|> The template is used to define the desired state of the persistent storage.
    - metadata:                 
        name: foodmag-app-sql-pvc
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
        name: foodmag-app-cms-pvc
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

The results will be followings:
```
kubectl apply -f doc/201/foodmag-app/foodmag-app-statefulset.yaml 
statefulset.apps/foodmag-app configured

kubectl get all -n foodmag-app -o wide
NAME                READY   STATUS    RESTARTS   AGE   IP            NODE          NOMINATED NODE   READINESS GATES
pod/foodmag-app-0   2/2     Running   0          11m   10.244.0.29   dbaas-8rowa   <none>           <none>

NAME                           READY   AGE   CONTAINERS                        IMAGES
statefulset.apps/foodmag-app   1/1     13m   foodmag-app-sql,foodmag-app-cms   postgres:latest,drupal:latest

kubectl get pvc -n foodmag-app
NAME                                STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS      AGE
foodmag-app-cms-pvc-foodmag-app-0   Bound    pvc-7dc38e7a-d28a-4c76-969d-4fe3958a0925   5Gi        RWO            storageos-rep-1   3h44m
foodmag-app-sql-pvc-foodmag-app-0   Bound    pvc-cc13bc1e-1d9b-4382-854a-3b9c12a5489b   5Gi        RWO            storageos-rep-1   3h44m
```

The above command outputs have an explicit usage of namespace. Let's have a look without it:
```
kubectl get all
NAME     READY   STATUS    RESTARTS   AGE
pod/d1   1/1     Running   46         46h
pod/d2   1/1     Running   46         46h

NAME                 TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
service/kubernetes   ClusterIP   10.245.0.1   <none>        443/TCP   3d19h 

kubectl get pvc 
NAME    STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS      AGE
pvc-1   Bound    pvc-f4af80a7-1224-4641-abae-8403e3c9827b   5Gi        RWO            fast              3d2h
pvc-2   Bound    pvc-3e303b09-dc6f-4cf7-b46a-d368463f629c   5Gi        RWO            storageos-rep-1   46h
```
This shows the concept of segmentation of resource opening doors to multi-tenancy. This will be investigated further in the Security chapter.  

Finally, some objects can't be bound to a specific namespace like the persistent volumes even with an explicit parameters:
```
kubectl get pv -n foodmag-app
NAME                                       CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM                                           STORAGECLASS      REASON   AGE
pvc-3e303b09-dc6f-4cf7-b46a-d368463f629c   5Gi        RWO            Delete           Bound    default/pvc-2                                   storageos-rep-1            47h
pvc-7dc38e7a-d28a-4c76-969d-4fe3958a0925   5Gi        RWO            Delete           Bound    foodmag-app/foodmag-app-cms-pvc-foodmag-app-0   storageos-rep-1            4h30m
pvc-cc13bc1e-1d9b-4382-854a-3b9c12a5489b   5Gi        RWO            Delete           Bound    foodmag-app/foodmag-app-sql-pvc-foodmag-app-0   storageos-rep-1            4h30m
pvc-f4af80a7-1224-4641-abae-8403e3c9827b   5Gi        RWO            Delete           Bound    default/pvc-1                                   fast                       3d3h
```

## what's in the box?
At the current stage, the StatefulSet created a couple of objects:
- StatefulSet (1)
- Persistent Volume Claims (2)
- Pods (2)
- Persistent Volumes(2) 

The following command will provide the complete inventory: 
```
kubectl describe -n foodmag-app statefulset.apps/foodmag-app
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

## where is my foodmag?
Despite the fact that both containers have been deployed successfully with their persistent storage, and despite the fact both containers have ports being defined, there is are no exposure for the outside world to access the CMS front-end. 

To do so, a service object needs offer exposure from the outside world to the appropriate container, in this case the ```foodmag-app-cms```. This can be done via the following YAML code:

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

The results will be the followings:

```
kubectl apply -f doc/201/foodmag-app/foodmag-app-cms-service.yaml 
service/foodmag-app-cms-service created

kubectl get all -n foodmag-app -o wide
NAME                READY   STATUS    RESTARTS   AGE   IP            NODE          NOMINATED NODE   READINESS GATES
pod/foodmag-app-0   2/2     Running   0          8h    10.244.0.29   dbaas-8rowa   <none>           <none>

NAME                              TYPE       CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE   SELECTOR
service/foodmag-app-cms-service   NodePort   10.245.253.117   <none>        80:30080/TCP   37s   app=foodmag-app,env=prod

NAME                           READY   AGE   CONTAINERS                        IMAGES
statefulset.apps/foodmag-app   1/1     8h    foodmag-app-sql,foodmag-app-cms   postgres:latest,drupal:latest
```

The above shows the new service being available to expose the CMS front-end TCP port 80 on a node redirecting traffic to the container TCP port 30080.

What about the ```foodmag-app-sql```? Good question! This is indeed the same issue but the main difference is about to radius of exposure. While the CMS needs to be exposed to the outside world, the database has to be exposed only to the CMS.  
As a matter of fact, if the database service is not created, skipping the next step and going forward with connecting to the CMS will results in failure to configure and deploy the demo data in. This can be done via the following YAML code: 

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
kubectl apply -f doc/201/foodmag-app/foodmag-app-sql-service.yaml 
service/foodmag-app-sql-service created

kubectl get all -n foodmag-app -o wide
NAME                READY   STATUS    RESTARTS   AGE   IP            NODE          NOMINATED NODE   READINESS GATES
pod/foodmag-app-0   2/2     Running   0          8h    10.244.0.29   dbaas-8rowa   <none>           <none>

NAME                              TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE   SELECTOR
service/foodmag-app-cms-service   NodePort    10.245.253.117   <none>        80:30080/TCP   26m   app=foodmag-app,env=prod
service/foodmag-app-sql-service   ClusterIP   10.245.211.246   <none>        5432/TCP       7s    app=foodmag-app,env=prod

NAME                           READY   AGE   CONTAINERS                        IMAGES
statefulset.apps/foodmag-app   1/1     8h    foodmag-app-sql,foodmag-app-cms   postgres:latest,drupal:latest
```

Notes:
- As discussed above, due to the exposure radius, the CMS use a [k8s service](https://kubernetes.io/docs/concepts/services-networking/service/) type ```NodePort``` to expose the service to the outside world while the database is using a ```ClusterIP``` to expose the service only within the cluster bubble.
- At the current state, no external IP is currently assigned, which is expected. 

For the current time, a forwarding process will use to access the CMS front-end on a local machine:

```
ip a
...
5: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 00:15:5d:31:47:14 brd ff:ff:ff:ff:ff:ff
    inet 172.22.135.113/20 brd 172.22.143.255 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 fe80::215:5dff:fe31:4714/64 scope link 
       valid_lft forever preferred_lft forever

kubectl port-forward -n foodmag-app service/foodmag-app-cms-service 8080:80 --address 172.22.135.113
Forwarding from 172.22.135.113:8080 -> 80
```

Open a browser with as URL ```172.22.135.113:8080``` which should show the following:  

Welcome page to install the CMS
![foodmag-app browser](images/foodmag-app_browser-01.png)

Select Demo to insert the foodmag data
![foodmag-app browser](images/foodmag-app_browser-02.png)

Provide the database details (see env details from the statefulset): 
- select PostgreSQL
- database name
- database username
- database password
- database service name

![foodmag-app browser](images/foodmag-app_browser-03.png)

Installation in progress (with more questions about name, email,...):
![foodmag-app browser](images/foodmag-app_browser-04.png)

Tadadaaaaaa! Here our website!
![foodmag-app browser](images/foodmag-app_browser-05.png)


