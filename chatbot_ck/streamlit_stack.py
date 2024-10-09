from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_logs as logs,
    aws_ecs_patterns as ecs_patterns,
    aws_elasticloadbalancingv2 as elbv2,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3 as s3,
    aws_codebuild as codebuild,
    aws_lambda as _lambda,
    Duration,
    Stack,
    RemovalPolicy,
    custom_resources as cr,
    CustomResource,
    aws_ecr_assets as ecr_assets,
    CfnOutput,
    Fn,

)
from chatbot_ck.streamlit_repo.utils.constants import *
import os
from pathlib import Path
class StreamlitStack(Stack):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)
        kb_id=Fn.import_value("KnowledgeBaseId")
        self.min_task_count=2
        self.max_task_count=10
        self.desired_task_count=2
        self.container_cpu=256
        self.container_memory=512
        self.container_port=8501
        self.target_cpu_utilization=50
        self.vpc_cidr="10.0.0.0/16"
        # VPC and subnets
        # vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_id=self.node.try_get_context("vpc_id"))
        # public_subnet_a = ec2.Subnet.from_subnet_id(self, "PublicSubnetA", self.node.try_get_context("public_subnet_a_id"))
        # public_subnet_b = ec2.Subnet.from_subnet_id(self, "PublicSubnetB", self.node.try_get_context("public_subnet_b_id"))
        # private_subnet_a = ec2.Subnet.from_subnet_id(self, "PrivateSubnetA", self.node.try_get_context("private_subnet_a_id"))
        # private_subnet_b = ec2.Subnet.from_subnet_id(self, "PrivateSubnetB", self.node.try_get_context("private_subnet_b_id"))
        
        vpc = ec2.Vpc(
            self,
            "VPC",
            ip_addresses=ec2.IpAddresses.cidr(self.vpc_cidr),
            max_azs=2,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PUBLIC,
                    name="Public",
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    name="Private",
                    cidr_mask=24,
                ),
            ],
        )

        # Create VPC Flow Logs
        vpc_log_group = logs.LogGroup(
            self,
            "VPCLogGroup",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )

        vpc_log_role = iam.Role(
            self,
            "VPCLogRole",
            assumed_by=iam.ServicePrincipal("vpc-flow-logs.amazonaws.com"),
        )

        vpc_log_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "logs:PutRetentionPolicy",
                ],
                resources=["*"],
            )
        )

        ec2.FlowLog(
            self,
            "VPCFlowLog",
            resource_type=ec2.FlowLogResourceType.from_vpc(vpc),
            destination=ec2.FlowLogDestination.to_cloud_watch_logs(vpc_log_group),
            traffic_type=ec2.FlowLogTrafficType.ALL,
        )

        # Logging
        access_logs_bucket = s3.Bucket(
            scope=self,
            id='accessLogsS3Bucket',
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            public_read_access=False,
            removal_policy=RemovalPolicy.DESTROY,  # removal_policy=RemovalPolicy.RETAIN in production
            versioned=False,
            auto_delete_objects=True,  # False in production
            enforce_ssl=True,
        )

        log_bucket = s3.Bucket(
            scope=self,
            id='ALBAccessLogsBucket',
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            public_read_access=False,
            removal_policy=RemovalPolicy.DESTROY,  # removal_policy=RemovalPolicy.RETAIN in production
            server_access_logs_bucket=access_logs_bucket,
            server_access_logs_prefix='chatbot-bucket/serverAccessLogging',
            versioned=False,
            auto_delete_objects=True,  # False in production
            enforce_ssl=True,
        )
        
        # ECS cluster
        cluster = ecs.Cluster(self, 'ChatCluster', vpc=vpc, container_insights=True, enable_fargate_capacity_providers=True)

        # ECR repository
        streamlit_repo = ecr.Repository(
            self,
            "StreamlitRepo",
            image_scan_on_push=True,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Build Docker image and push to ECR
        current = Path(__file__).parent
        docker_dir = str(Path(current / 'streamlit_repo').resolve())
        docker_image_asset = ecr_assets.DockerImageAsset(
            self,
            'ChatDockerImage',
            directory=docker_dir,  # Directory with Dockerfile
        )

        # Define an ECS task definition with a single container
        task_definition = ecs.FargateTaskDefinition(
            self,
            'ChatTaskDef',
            memory_limit_mib=4096,
            cpu=2048,
            runtime_platform=ecs.RuntimePlatform(
                operating_system_family=ecs.OperatingSystemFamily.LINUX,
                cpu_architecture=ecs.CpuArchitecture.X86_64,
            ),
        )

        # Add container to the task definition
        container = task_definition.add_container(
            'ChatBotContainer',
            image=ecs.ContainerImage.from_docker_image_asset(docker_image_asset),
            logging=ecs.LogDrivers.aws_logs(stream_prefix='Chatbot', log_retention=logs.RetentionDays.ONE_DAY),
            environment= {
                "KNOWLEDGE_BASE_ID": kb_id,
                "CDK_DEFAULT_REGION": region,
            }
        )
        
        # Open the necessary port internally
        container.add_port_mappings(ecs.PortMapping(container_port=self.container_port, protocol=ecs.Protocol.TCP))

        # Fargate service
        streamlit_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "StreamlitService",
            # cpu=self.container_cpu,
            # memory_limit_mib=self.container_memory,
            # desired_count=self.desired_task_count,
            cluster=cluster,
            task_definition=task_definition,
            assign_public_ip=False,
            # chỗ này ban đầu là assign_public_ip=False,
            public_load_balancer=True,
            listener_port=80,
            desired_count=1,
            load_balancer_name='chatbot-application-lb',
            redirect_http=False,
            protocol=elbv2.ApplicationProtocol.HTTP,  # Ensure HTTPS protocol is used
            circuit_breaker=ecs.DeploymentCircuitBreaker(enable=True, rollback=True),
        )

        # Custom header for CloudFront
        streamlit_service.target_group.configure_health_check(
            path="/health",
            healthy_http_codes="200-399",
        )

        streamlit_service.load_balancer.log_access_logs(log_bucket, prefix="access-logs")
        # streamlit_service.load_balancer.add_listener("StreamlitHTTPListener",
        #                                             port=80, default_target_groups=[streamlit_service.target_group])
        streamlit_header_value = f"{Stack.of(self).stack_name}-{Stack.of(self).account}"
        # streamlit_service.listener.add_targets(
        #     "StreamlitALBListenerRule",
        #     port=80,
        #     targets=[streamlit_service.service],
        #     conditions=[
        #         elbv2.ListenerCondition.http_header(
        #             "X-Custom-Header", [streamlit_header_value]
        #         )
        #     ],
        #     priority=1,
        # )
    

        # Auto scaling
        streamlit_service.service.auto_scale_task_count(
            min_capacity=self.min_task_count,
            max_capacity=self.max_task_count,
        ).scale_on_cpu_utilization(
            "StreamlitAutoScaling",
            target_utilization_percent=self.target_cpu_utilization,
            scale_in_cooldown=Duration.seconds(60),
            scale_out_cooldown=Duration.seconds(60),
        )


        # Bedrock IAM Policy
        bedrock_iam_policy = iam.Policy(
            self,
            "BedrockPermissionsPolicy",
            statements=[
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                "bedrock:InvokeModel",
                "bedrock:Retrieve",
                "bedrock:InvokeModelWithResponseStream",
                "bedrock:RetrieveAndGenerate",
                ],
                resources=[
                f"arn:aws:bedrock:{region}::foundation-model/{ModelId.CLAUDE_3_5_SONNET.value}",
                f"arn:aws:bedrock:{region}::foundation-model/{ModelId.CLAUDE_3_HAIKU.value}",
                f"arn:aws:bedrock:{region}::foundation-model/{ModelId.TITAN_EMBED_TEXT_V1.value}",
                f"arn:aws:bedrock:{region}:{account_id}:knowledge-base/{kb_id}"
                ],
            ),
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                "s3:GetObject"
                ],
                resources=["*"],  # Corrected to be a list
            ),
            ],
        )

        streamlit_service.task_definition.add_to_task_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    'secretsmanager:GetSecretValue',
                    "kms:Decrypt",
                ],
                resources=['*'],  # place secret ARN here
            )
        )
        # Attach the Bedrock permissions to the task role
        streamlit_service.task_definition.task_role.attach_inline_policy(bedrock_iam_policy)

        # Grant ECR repository permissions for the task execution role
        streamlit_repo.grant_pull_push(streamlit_service.task_definition.execution_role)

        # # Grant permissions for CloudWatch Logs
        # log_group = logs.LogGroup(
        #     self,
        #     'MyLogGroup',
        #     log_group_name='/ecs/my-fargate-service',
        #     removal_policy=RemovalPolicy.DESTROY,
        # )

        # log_group.grant_write(streamlit_service.task_definition.execution_role)


        # CloudFront distribution
        streamlit_origin = origins.HttpOrigin(
            domain_name=streamlit_service.load_balancer.load_balancer_dns_name,
            http_port=80,
            protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY,
            custom_headers={"X-Custom-Header": streamlit_header_value},
        )

        streamlit_distribution = cloudfront.Distribution(
            self,
            "StreamlitDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=streamlit_origin,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.HTTPS_ONLY,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD,
            ),
            price_class=cloudfront.PriceClass.PRICE_CLASS_ALL,
            enabled=True,
            http_version=cloudfront.HttpVersion.HTTP2,
            default_root_object="index.html",
            # logging_config=cloudfront.LoggingConfiguration(
            #     bucket=logs_bucket, include_cookies=True
            # ),
        )
        


      