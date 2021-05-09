from diagrams import Cluster, Diagram 
from diagrams.k8s.compute import Pod, DaemonSet
from diagrams.k8s.storage import PV, PVC, StorageClass


with Diagram("Persistent Storage for a Pod", show=False):
    
    with Cluster("k8s"):
        pod = Pod("d1")
        pvc = PVC("pvc-1")
        pv = PV("pvc-[uuid]")
        sc = StorageClass("fast")
        ds = DaemonSet("StorageOS")

        pod >> pvc << pv << sc >> ds