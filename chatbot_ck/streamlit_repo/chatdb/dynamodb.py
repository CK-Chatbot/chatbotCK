import boto3

# Get the service resource.
dynamodb = boto3.resource("dynamodb")

# Create the DynamoDB table.
table = dynamodb.create_table(
    TableName="EXAMPLE_TABLE",
    KeySchema=[{"AttributeName": "SessionId", "KeyType": "HASH"}],
    AttributeDefinitions=[
        {"AttributeName": "SessionId", "AttributeType": "S"}
    ],
    BillingMode="PAY_PER_REQUEST",
)

