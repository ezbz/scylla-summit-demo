import * as pulumi from "@pulumi/pulumi";
import * as awsx from "@pulumi/awsx";
import * as eks from "@pulumi/eks";

const projectName = pulumi.getProject();

const vpc = new awsx.ec2.Vpc(`${projectName}-2`, {
    tags: { "Name": `${projectName}-2` },
});

const cluster = new eks.Cluster(`${projectName}-2`, {
    vpcId: vpc.id,
    publicSubnetIds: vpc.publicSubnetIds,
    desiredCapacity: 24,
    minSize: 10,
    maxSize: 30,
    instanceType: 'c5.4xlarge',
    deployDashboard: false,
    enabledClusterLogTypes: [
        "api",
        "audit",
        "authenticator",
    ],
});

export const kubeconfig = cluster.kubeconfig;

