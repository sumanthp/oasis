from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_iam as iam,
)
from constructs import Construct

class AiEngineSandboxStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Create a VPC for the Sandbox Environments
        # We use a dedicated VPC to ensure candidate environments are isolated
        self.vpc = ec2.Vpc(
            self, "AiEngineSandboxVpc",
            max_azs=2,
            nat_gateways=1, # Allow outbound internet for downloading packages
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                )
            ]
        )

        # 2. Create an ECS Cluster to host the ephemeral candidate sandboxes
        self.cluster = ecs.Cluster(
            self, "AiEngineSandboxCluster",
            vpc=self.vpc,
            container_insights=True # Important for evaluating candidate traces/performance
        )

        # 3. Create a Task Execution Role that the Sandbox API can assume
        self.task_execution_role = iam.Role(
            self, "SandboxTaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")
            ]
        )

        # TODO: Define specific Task Definitions for each Challenge Type (Domain A, B, C)
        # These will be dynamically triggered by the FastAPI Orchestrator
