#!/usr/bin/env python3
import argparse
import sys
import os


#  -pop seq={seq} protocolVersion=3

template = """
apiVersion: batch/v1
kind: Job
metadata:
  name: {d.name}-{mode}-{}
  namespace: {d.namespace}
  labels:
    app: cassandra-stress
spec:
  parallelism: {d.parallelism}
  template:
    spec:
      containers:
      - name: cassandra-stress
        image: scylladb/scylla:{d.scylla_version}
        command:
          - "/bin/bash"
          - "-c"
          - '/opt/scylladb/share/cassandra/bin/cassandra-stress {mode} cl=QUORUM duration=15m -mode native user={d.username} password={d.password} cql3 -rate threads={d.threads} throttle={d.throttle}/s -node {host} -col "n=FIXED(1)"'
        resources:
          limits:
            cpu: "{d.cpu_limit}"
            memory: {d.memory_limit}Mi
          requests:
            cpu: "{d.cpu}"
            memory: {d.memory}Mi
      restartPolicy: Never
      nodeSelector:
      tolerations:
        - key: role
          operator: Equal
          value: cassandra-stress
          effect: NoSchedule
      affinity:
        podAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                topologyKey: kubernetes.io/hostname
                labelSelector:
                  matchLabels:
                    app: cassandra-stress
       
"""

def parse():
    parser = argparse.ArgumentParser(description='Generate cassandra-stress job templates for Kubernetes.')
    parser.add_argument('--name', default='cassandra-stress', help='name of the generated yaml file - defaults to cassandra-stress')
    parser.add_argument('--mode', default='write', help='comma delimited the modes to apply: read or write or mixed read,write (for read,write consider halving the parallism to retain workload)')
    parser.add_argument('--namespace', default='default', help='namespace of the cassandra-stress jobs - defaults to "default"')
    parser.add_argument('--scylla-version', default='4.2.0', help='version of scylla server to use for cassandra-stress - defaults to 4.0.0', dest='scylla_version')
    parser.add_argument('--protocol-version', type=int, default=4, help='version of protocol - defaults to 4 which is shard aware', dest='protocol_version')
    parser.add_argument('--hosts', required=True, default=None, help='comma delimited list of ips or dns names of host to connect to a job will be created for each host - required parameter')
    parser.add_argument('--parallelism', default=110, type=int, help='the parallelism for the jobs')
    parser.add_argument('--username', default='scylla', help='the CQL username for the cluster, defaults to scylla')
    parser.add_argument('--password', required=True, default=None, help='the CQL password for the cluster')
    parser.add_argument('--cpu', default=1, type=int, help='number of cpus that will be used for each job - defaults to 1')
    parser.add_argument('--ops', type=int, default=50000000, help='number of operations for each job - defaults to 10000000')
    parser.add_argument('--memory', default=1024, help='memory that will be used for each job in GB, ie 2G - defaults to 2G * cpu')
    parser.add_argument('--threads', default=500, help='number of threads used for each job - defaults to 50 * cpu')
    parser.add_argument('--throttle', default=164000, help='throttling in requests per second for the test')
    parser.add_argument('--connections-per-host', default=None, help='number of connections per host - defaults to number of cpus', dest='connections_per_host')
    parser.add_argument('--print-to-stdout', action='store_const', const=True, help='print to stdout instead of writing to a file', dest='print_to_stdout')
    return parser.parse_args()

def create_job_list(args):
    manifests = []
    hosts = args.hosts.split(',')
    num_hosts = len(hosts)
    modes = args.mode.split(',')

    for m in modes:
      for i in range(num_hosts):
          seq = '{}..{}'.format(i*250000000+1, ((i+1) * 250000000))
          manifests.append(template.format(i, d=args, host=hosts[i], mode=m, seq=seq))
    return manifests

def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

if __name__ == "__main__":
    args = parse()

    # Fix arguments
    if args.memory is None:
      args.memory = args.cpu*1024
    if args.threads is None:
      args.threads = 50*args.cpu
    if args.connections_per_host is None:
      args.connections_per_host = args.cpu
    args.cpu_limit = args.cpu *2
    args.memory_limit = args.memory *2
    # Create manifests
    manifests = create_job_list(args)
    if args.print_to_stdout:
      print('\n---\n'.join(manifests))
    else:
      f = open(get_script_path() + '/' + args.name + '.yaml', 'w')
      f.write('\n---\n'.join(manifests))
      f.close()
