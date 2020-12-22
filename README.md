Scylla Summit Demo
==================

Goal
====
* Show how easy it is to reach multi-million-ops-per-second with Scylla Cloud on appropriate nodes

Stack
=====
* Scylla Enterprise 2020.1.4 (latest cloud version)
* 3-node cluster composed of `i3en.16xlarge` instances in AWS
* an EKS cluster for running docker-based `cassandra-stress` workload on the scylla cloud cluster with `22` kuberentes workers `c5.4xlarge`

* cassandra stress launched with the following configuration (credentials and node ip address omitted)

```cassandra-stress write cl=QUORUM duration=15m -mode native cql3 -rate threads=350 throttle=86000/s -col n=FIXED\(1\)```

* `120x3` kubernetes jobs for a total of `360` pods executing cassandra stress jobs
* A whopping 1.5 mm ops / sec / node for a total of almost 5mm ops / sec / cluster

Requirements
============
* `pulumi@v2.15.6`
* `aws-cli/2.1.8`
* jq

Process
=======
* Sign up to Scylla cloud 
* Bootstrap a new cluster in BYOA mode
* Set aws credentials for the connected account
* Setup an eks cluster and worker nodes

```
cd pulumi-eks
pulumi up
```

* Get the cluster id from the output

```
CLUSTER_ID=`pulumi stack output kubeconfig | jq -r '.users[0].user.exec.args[3]'`
echo $CLUSTER_ID
```

* Import `kubeconfig` from EKS (this will override your current kubeconfig so back it up before `cp ~/.kube/config ~/.kube/config.bak`)

```
aws eks --region us-east-1 update-kubeconfig --name $CLUSTER_ID
```

* Apply the worklow

```
kubectl apply -f k8s-cassandra-stress/cassandra-stress.yaml
```

* Observe the workload pods are running and not in error state

```
kubectl get pods
```

* If you want k8s dashboards

- install metrics server

```
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/download/v0.3.7/components.yaml
```

- install dashboard

```
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.0.5/aio/deploy/recommended.yaml

```

- create service account

```
kubectl apply -f eks-admin-service-account.yaml
```

- get a token for the dashboard login page

```
kubectl -n kube-system describe secret $(kubectl -n kube-system get secret | grep eks-admin | awk '{print $1}') 
```