import os
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    #aws_lambda as _lambda,
    CfnOutput,
    Duration as Duration,
    RemovalPolicy
)
from constructs import Construct
from cdklabs.generative_ai_cdk_constructs import (
    bedrock,
)
your_bucket_name = os.getenv("YOUR_BUCKET_NAME")


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
        dataSource = bedrock.S3DataSource(self, 'DataSource-OS',
            bucket= docBucket,
            knowledge_base=kb,
            data_source_name='CK-Sale-Assets',
            chunking_strategy= bedrock.ChunkingStrategy.FIXED_SIZE,
        )
        CfnOutput(self, "KnowledgeBaseId", value=kb.knowledge_base_id, export_name="KnowledgeBaseId")
        CfnOutput(self, 'DataSourceId', value= dataSource.data_source_id, export_name="DataSourceId")
        CfnOutput(self, 'DocumentBucket', value= docBucket.bucket_name, export_name="DocumentBucket")
    
        
