from diagrams import Cluster, Diagram, Edge
from diagrams.k8s.compute import Pod, DaemonSet
from diagrams.k8s.storage import PV, PVC, StorageClass

with Diagram("foodmag-app overview", show=False):
    
    with Cluster("k8s"):
        ds = DaemonSet("StorageOS")
        sc = StorageClass("storageos-rep-1")
        pvc = PV("pvc-[uuid]")
        pvp = PV("pvc-[uuid]")

        with Cluster("namespace: foodmag-app"):
            cms = Pod("drupal")
            sql = Pod("postgresql")
            pvcc = PVC("pvc-cms")
            pvcp = PVC("pvc-sql")



            # cms >> sql 
            cms >> pvcc 
            sql >> pvcp 

            pvcc << pvc << sc 
            pvcp << pvp << sc 
            sc >> ds 