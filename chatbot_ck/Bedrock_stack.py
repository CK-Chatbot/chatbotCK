import os
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    #aws_lambda as _lambda,
    CfnOutput,
    Duration as Duration,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_secretsmanager as secretsmanager,
    aws_kms as kms,
    aws_iam as iam,
)

from constructs import Construct
from cdklabs.generative_ai_cdk_constructs import (
    bedrock,
)
your_bucket_name = os.getenv("YOUR_BUCKET_NAME")
account_id = os.getenv("CDK_DEFAULT_ACCOUNT")
region = os.getenv("CDK_DEFAULT_REGION")

class BedrockStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Knowledge Base
        kb = bedrock.KnowledgeBase(self, 'KnowledgeBase-OS', 
            embeddings_model= bedrock.BedrockFoundationModel.TITAN_EMBED_TEXT_V1,
            instruction= 'Use this knowledge base and www.cloud-kinetics.com to answer questions about inquiries (FaQs, services offerings,...) related to Cloud Kinetics Company',
            description= 'This knowledge base contains the information about Cloud Kinetics company.',                    
        )


        #S3 bucket for Bedrock data source
        docBucket = s3.Bucket.from_bucket_name(self, "DockBucket-OS", bucket_name=your_bucket_name)

        #Create data source from website
        kb.add_web_crawler_data_source(
            data_source_name='CK-Website',
            description= 'This data source website',
            source_urls= ['https://www.cloud-kinetics.com/'],
            chunking_strategy= bedrock.ChunkingStrategy.HIERARCHICAL_COHERE,
        )

        #Create additional bedrock policy
        bedrock_iam_policy = iam.Policy(
            self,
            "BedrockPermissionsPolicy",
            statements=[
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                "s3:GetObject",
                "s3:PutObject",
                ],
                resources=["*"],  # Corrected to be a list
            ),
            ],
        )
        # Grant permissions for Bedrock
        kb.role.attach_inline_policy(bedrock_iam_policy)
        #Connect data source to knowledge base
        dataSource = bedrock.S3DataSource(self, 'DataSource-OS',
            bucket= docBucket,
            knowledge_base=kb,
            data_source_name='CK-Sale-Assets',
            chunking_strategy= bedrock.ChunkingStrategy.semantic(breakpoint_percentile_threshold=90,buffer_size=1,max_tokens=500),
            parsing_strategy= bedrock.ParsingStategy.foundation_model(
                parsing_model= bedrock.BedrockFoundationModel.ANTHROPIC_CLAUDE_HAIKU_V1_0.as_i_model(self),
            )
        )
        
        CfnOutput(self, "KnowledgeBaseId", value=kb.knowledge_base_id, export_name="KnowledgeBaseId")
        CfnOutput(self, 'DataSourceId', value= dataSource.data_source_id, export_name="DataSourceId")
        CfnOutput(self, 'DocumentBucket', value= docBucket.bucket_name, export_name="DocumentBucket")
    
        
