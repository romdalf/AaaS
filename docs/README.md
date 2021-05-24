# anything-as-a-Service (AaaS)

## learner Outcomes
* Get familiar with kubernetes and persistent storage
* Get hands-on to deploy and migrate stateful workload
* Get hands-on on Continuous deployment

## prerequisites
A good 50% of the content could be followed without having a real k8s cluster and using instead one of the multiple one-node kubernetes project like minikube or code-reayd-container.  
However, to appreciate the content, a 3-nodes kubernetes (k8s) cluster would be required especially when looking into persistent storage.  

Two get a 3-nodes k8s cluster, there are a couple of options:
- get some free trial credits from one the cloud provider like DigitalOcean, Civo, or the big ones and deploy a basic k8s cluster 
- get 3 VMs, each having 2vCPU/2GB RAM/20GB disk, and deploy a [k3s](https://k3s.io) cluster using [k3sup](https://github.com/alexellis/k3sup) to ease the process
- use a dev/test k8s cluster within your environment as full clean-up procedure is supplied at the end of every chapter

For the purposes of this guide, a k8s cluster deployed within DigitalOcean is used. The overall guide is totally agnostic of any k8s cluster platform provider. 

## git 
Embrace the infrastructure-as-code practice and clone this repository. The content provides a comprehensive ramp up also from a Git perspective illustrating the many advantages: 

* fork this repository by clicking the "fork" icon on the top right corner to have a copy of this repository within your own account
* clone the forked repository with the following command: 
```
git clone https://github.com/<replace_with_your_account_handle>/AaaS.git
cd AaaS
```