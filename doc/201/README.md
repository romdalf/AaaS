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
kubectl apply -f doc/201/foodmag-app/foodmag-namespace.yaml
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




