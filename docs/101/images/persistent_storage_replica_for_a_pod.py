from diagrams import Cluster, Diagram, Edge
from diagrams.k8s.compute import Pod, DaemonSet
from diagrams.k8s.storage import PV, PVC, StorageClass


with Diagram("Persistent Storage with replica for a Pod", show=False):
    
    with Cluster("k8s"):
        pod = Pod("d2")
        pvc = PVC("pvc-2")
        pv1 = PV("pvc-[uuid] (primary)")
        pv2 = PV("pvc-[uuid] (replica)")
        sc = StorageClass("storageos-rep-1")
        ds = DaemonSet("StorageOS")

        pod >> pvc 
        pvc << pv1 << sc
        pvc - Edge(color="red", style="dotted") - pv2 
        pv2 - Edge(color="brown", style="dotted") - sc
        sc >> ds