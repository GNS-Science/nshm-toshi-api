# Toshi search — captured live state

- **Captured:** 2026-09-21T04:25:00Z by `scripts/capture_search_state.sh`
- **Stage:** prod
- **Region:** ap-southeast-2
- **Stack:** nzshm22-toshi-api-prod
- **Account:** <AWS-ACCOUNT-ID>

Pre-teardown snapshot of both search backends: the managed domain declared
in serverless.yml, and the OpenSearch Serverless collection that exists only
in live AWS state. Read-only capture — see the script for what was run.

> Secret-looking environment values, the AWS account ID, endpoint hostnames and
> IP addresses are redacted — this file is committed to a public repository.
> See #386.

## CloudFormation stack resources

What the template thinks exists. Compare against the OpenSearch sections below.

### All stack resources

```
$ aws cloudformation describe-stack-resources --stack-name nzshm22-toshi-api-prod --region ap-southeast-2
{
    "StackResources": [
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "ApiGatewayDeployment1785293071334",
            "PhysicalResourceId": "9a2h9g",
            "ResourceType": "AWS::ApiGateway::Deployment",
            "Timestamp": "2026-07-29T02:45:36.387000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "ApiGatewayMethodGraphqlGet",
            "PhysicalResourceId": "nzshm-ApiGa-1INIKWVV0NBA3",
            "ResourceType": "AWS::ApiGateway::Method",
            "Timestamp": "2026-06-16T23:07:40.729000+00:00",
            "ResourceStatus": "UPDATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "ApiGatewayMethodGraphqlOptions",
            "PhysicalResourceId": "nzshm-ApiGa-16ZNQX4Y8ZGS6",
            "ResourceType": "AWS::ApiGateway::Method",
            "Timestamp": "2026-06-16T23:07:40.749000+00:00",
            "ResourceStatus": "UPDATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "ApiGatewayMethodGraphqlPost",
            "PhysicalResourceId": "nzshm-ApiGa-UT457DF8VUWB",
            "ResourceType": "AWS::ApiGateway::Method",
            "Timestamp": "2026-06-16T23:07:40.644000+00:00",
            "ResourceStatus": "UPDATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "ApiGatewayResourceGraphql",
            "PhysicalResourceId": "vfyf86",
            "ResourceType": "AWS::ApiGateway::Resource",
            "Timestamp": "2021-04-13T05:03:45.268000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "ApiGatewayRestApi",
            "PhysicalResourceId": "aihssdkef5",
            "ResourceType": "AWS::ApiGateway::RestApi",
            "Timestamp": "2021-04-13T05:03:43.072000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "ElasticSearchInstance",
            "PhysicalResourceId": "nzshm22-toshi-api-es-prod",
            "ResourceType": "AWS::Elasticsearch::Domain",
            "Timestamp": "2021-04-13T05:16:47.355000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "GraphqlLambdaFunction",
            "PhysicalResourceId": "nzshm22-toshi-api-prod-graphql",
            "ResourceType": "AWS::Lambda::Function",
            "Timestamp": "2026-07-29T02:45:33.279000+00:00",
            "ResourceStatus": "UPDATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "GraphqlLambdaPermissionApiGateway",
            "PhysicalResourceId": "nzshm22-toshi-api-prod-GraphqlLambdaPermissionApiGateway-00GaRjkJb5FJ",
            "ResourceType": "AWS::Lambda::Permission",
            "Timestamp": "2026-06-16T23:07:38.645000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "GraphqlLambdaVersionQuQtWvyRGB69bD4iUY0LGkiuKPKccE0Jyj1L3LvDblk",
            "PhysicalResourceId": "arn:aws:lambda:ap-southeast-2:<AWS-ACCOUNT-ID>:function:nzshm22-toshi-api-prod-graphql:6",
            "ResourceType": "AWS::Lambda::Version",
            "Timestamp": "2026-07-29T02:45:35.609000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "GraphqlLogGroup",
            "PhysicalResourceId": "/aws/lambda/nzshm22-toshi-api-prod-graphql",
            "ResourceType": "AWS::Logs::LogGroup",
            "Timestamp": "2026-06-16T23:07:25.915000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "IamRoleLambdaExecution",
            "PhysicalResourceId": "nzshm22-toshi-api-prod-ap-southeast-2-lambdaRole",
            "ResourceType": "AWS::IAM::Role",
            "Timestamp": "2024-05-07T23:01:31.423000+00:00",
            "ResourceStatus": "UPDATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "JwtAuthorizerApiGatewayAuthorizer",
            "PhysicalResourceId": "brdsld",
            "ResourceType": "AWS::ApiGateway::Authorizer",
            "Timestamp": "2026-06-16T23:07:38.524000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "JwtAuthorizerLambdaFunction",
            "PhysicalResourceId": "nzshm22-toshi-api-prod-jwtAuthorizer",
            "ResourceType": "AWS::Lambda::Function",
            "Timestamp": "2026-07-29T02:45:33.272000+00:00",
            "ResourceStatus": "UPDATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "JwtAuthorizerLambdaPermissionApiGateway",
            "PhysicalResourceId": "nzshm22-toshi-api-prod-JwtAuthorizerLambdaPermissionApiGateway-Gw94vc1oqy6H",
            "ResourceType": "AWS::Lambda::Permission",
            "Timestamp": "2026-06-16T23:07:38.545000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "JwtAuthorizerLambdaVersion3JQxznEQRYVpQoPR08e00ee7BkQ5MEm6TBMcbLMv9RY",
            "PhysicalResourceId": "arn:aws:lambda:ap-southeast-2:<AWS-ACCOUNT-ID>:function:nzshm22-toshi-api-prod-jwtAuthorizer:5",
            "ResourceType": "AWS::Lambda::Version",
            "Timestamp": "2026-07-29T02:45:35.412000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "JwtAuthorizerLogGroup",
            "PhysicalResourceId": "/aws/lambda/nzshm22-toshi-api-prod-jwtAuthorizer",
            "ResourceType": "AWS::Logs::LogGroup",
            "Timestamp": "2026-06-16T23:07:26.106000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "ServerlessDeploymentBucket",
            "PhysicalResourceId": "nzshm22-toshi-api-prod-serverlessdeploymentbucket-1x2pkablsqcxi",
            "ResourceType": "AWS::S3::Bucket",
            "Timestamp": "2021-04-13T05:03:15.485000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "ServerlessDeploymentBucketPolicy",
            "PhysicalResourceId": "nzshm22-toshi-api-prod-ServerlessDeploymentBucke-1KAO4F4Q99A5T",
            "ResourceType": "AWS::S3::BucketPolicy",
            "Timestamp": "2022-02-21T23:17:00.385000+00:00",
            "ResourceStatus": "UPDATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "ToshiAutomationClient",
            "PhysicalResourceId": "335e69ia1pf12k7a6dhf0kvf1m",
            "ResourceType": "AWS::Cognito::UserPoolClient",
            "Timestamp": "2026-06-16T23:07:25.973000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "ToshiBucket",
            "PhysicalResourceId": "nzshm22-toshi-api-prod",
            "ResourceType": "AWS::S3::Bucket",
            "Timestamp": "2021-04-13T05:04:04.236000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "ToshiGroupReaders",
            "PhysicalResourceId": "toshi-readers",
            "ResourceType": "AWS::Cognito::UserPoolGroup",
            "Timestamp": "2026-06-16T23:07:44.356000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "ToshiGroupRunziAdmin",
            "PhysicalResourceId": "runzi-admin",
            "ResourceType": "AWS::Cognito::UserPoolGroup",
            "Timestamp": "2026-06-16T23:07:44.335000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "ToshiGroupRunziBatch",
            "PhysicalResourceId": "runzi-batch",
            "ResourceType": "AWS::Cognito::UserPoolGroup",
            "Timestamp": "2026-06-16T23:07:44.303000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "ToshiGroupRunziLocal",
            "PhysicalResourceId": "runzi-local",
            "ResourceType": "AWS::Cognito::UserPoolGroup",
            "Timestamp": "2026-06-16T23:07:44.357000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "ToshiGroupWriters",
            "PhysicalResourceId": "toshi-writers",
            "ResourceType": "AWS::Cognito::UserPoolGroup",
            "Timestamp": "2026-06-16T23:07:44.425000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "ToshiIdentityPool",
            "PhysicalResourceId": "ap-southeast-2:4dd8c37d-3a77-4bb2-8366-78b8f869bd78",
            "ResourceType": "AWS::Cognito::IdentityPool",
            "Timestamp": "2026-06-16T23:07:27.999000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "ToshiIdentityPoolRoleAttachment",
            "PhysicalResourceId": "ap-southeast-2:4dd8c37d-3a77-4bb2-8366-78b8f869bd78",
            "ResourceType": "AWS::Cognito::IdentityPoolRoleAttachment",
            "Timestamp": "2026-06-16T23:08:02.486000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "ToshiM2MSecret",
            "PhysicalResourceId": "arn:aws:secretsmanager:ap-southeast-2:<AWS-ACCOUNT-ID>:secret:toshi-m2m-prod-nOrcpl",
            "ResourceType": "AWS::SecretsManager::Secret",
            "Timestamp": "2026-06-16T23:07:19.937000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "ToshiResourceServer",
            "PhysicalResourceId": "toshi",
            "ResourceType": "AWS::Cognito::UserPoolResourceServer",
            "Timestamp": "2026-06-16T23:07:24.179000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "ToshiScientistClient",
            "PhysicalResourceId": "3thdbdiedo5q2lqbjceg7a46pa",
            "ResourceType": "AWS::Cognito::UserPoolClient",
            "Timestamp": "2026-06-16T23:07:25.910000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "ToshiUserPool",
            "PhysicalResourceId": "ap-southeast-2_xas5hRD2T",
            "ResourceType": "AWS::Cognito::UserPool",
            "Timestamp": "2026-06-16T23:07:21.245000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "ToshiUserPoolDomain",
            "PhysicalResourceId": "toshi-<AWS-ACCOUNT-ID>-prod",
            "ResourceType": "AWS::Cognito::UserPoolDomain",
            "Timestamp": "2026-06-16T23:07:25.499000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "WarmUpPluginLowConcurrencyWarmerEventsRuleSchedule1",
            "PhysicalResourceId": "nzshm22-toshi-api-prod-WarmUpPluginLowConcurrencyW-1OFOSD98IMN9M",
            "ResourceType": "AWS::Events::Rule",
            "Timestamp": "2022-02-21T23:18:45.170000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "WarmUpPluginLowConcurrencyWarmerLambdaFunction",
            "PhysicalResourceId": "nzshm22-toshi-api-prod-warmup-plugin-lowConcurrencyWarmer",
            "ResourceType": "AWS::Lambda::Function",
            "Timestamp": "2026-07-29T02:45:32.784000+00:00",
            "ResourceStatus": "UPDATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "WarmUpPluginLowConcurrencyWarmerLambdaPermissionEventsRuleSchedule1",
            "PhysicalResourceId": "nzshm22-toshi-api-prod-WarmUpPluginLowConcurrencyWarmerLambdaPermissionEventsRuleSched-96FDXGBH9PEX",
            "ResourceType": "AWS::Lambda::Permission",
            "Timestamp": "2022-02-21T23:18:57.425000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "WarmUpPluginLowConcurrencyWarmerLambdaVersionoJgxSQHa9SVbyAYL0b1STxRVVtekUvz7r5yQJyoPo",
            "PhysicalResourceId": "arn:aws:lambda:ap-southeast-2:<AWS-ACCOUNT-ID>:function:nzshm22-toshi-api-prod-warmup-plugin-lowConcurrencyWarmer:6",
            "ResourceType": "AWS::Lambda::Version",
            "Timestamp": "2026-06-22T02:50:12.123000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "WarmUpPluginLowConcurrencyWarmerLogGroup",
            "PhysicalResourceId": "/aws/lambda/nzshm22-toshi-api-prod-warmup-plugin-lowConcurrencyWarmer",
            "ResourceType": "AWS::Logs::LogGroup",
            "Timestamp": "2022-02-21T23:17:01.784000+00:00",
            "ResourceStatus": "CREATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        },
        {
            "StackName": "nzshm22-toshi-api-prod",
            "StackId": "arn:aws:cloudformation:ap-southeast-2:<AWS-ACCOUNT-ID>:stack/nzshm22-toshi-api-prod/7da89aa0-9c15-11eb-b4b7-06b6a0304954",
            "LogicalResourceId": "WarmUpPluginLowConcurrencyWarmerRole",
            "PhysicalResourceId": "nzshm22-toshi-api-prod-ap-southeast-2-lowconcurrencywarmer-role",
            "ResourceType": "AWS::IAM::Role",
            "Timestamp": "2026-06-16T23:07:37.090000+00:00",
            "ResourceStatus": "UPDATE_COMPLETE",
            "DriftInformation": {
                "StackResourceDriftStatus": "NOT_CHECKED"
            }
        }
    ]
}
```

### Search-related stack resources only

```
$ aws cloudformation describe-stack-resources --stack-name nzshm22-toshi-api-prod --region ap-southeast-2 --query StackResources[?contains(ResourceType, 'arch')].{Logical:LogicalResourceId,Type:ResourceType,Physical:PhysicalResourceId,Status:ResourceStatus}
[
    {
        "Logical": "ElasticSearchInstance",
        "Type": "AWS::Elasticsearch::Domain",
        "Physical": "nzshm22-toshi-api-es-prod",
        "Status": "CREATE_COMPLETE"
    }
]
```

## Lambda environment

The open question: ES_ENDPOINT / ES_INDEX are not in serverless.yml (removed in 6e9b8d9, 2026-06-16) yet reads still work, so they must be set out-of-band. This is what a deploy would overwrite.

### Function environment: nzshm22-toshi-api-prod-graphql

```
$ aws lambda get-function-configuration --function-name nzshm22-toshi-api-prod-graphql --region ap-southeast-2 --query {Runtime:Runtime,Memory:MemorySize,Timeout:Timeout,LastModified:LastModified,Environment:Environment}
{
    "Runtime": "python3.12",
    "Memory": 4096,
    "Timeout": 30,
    "LastModified": "2026-07-29T02:45:27.000+0000",
    "Environment": {
        "Variables": {
            "FIRST_DYNAMO_ID": "100000",
            "DEPLOYMENT_STAGE": "prod",
            "GRAPHQL_PATH": "/graphql",
            "S3_BUCKET_NAME": "nzshm22-toshi-api-prod",
            "URL_DEFAULT_TTL": "60",
            "REGION": "ap-southeast-2"
        }
    }
}
```

### Function environment: nzshm22-toshi-api-prod-jwtAuthorizer

```
$ aws lambda get-function-configuration --function-name nzshm22-toshi-api-prod-jwtAuthorizer --region ap-southeast-2 --query {Runtime:Runtime,Memory:MemorySize,Timeout:Timeout,LastModified:LastModified,Environment:Environment}
{
    "Runtime": "python3.12",
    "Memory": 512,
    "Timeout": 10,
    "LastModified": "2026-07-29T02:45:27.000+0000",
    "Environment": {
        "Variables": {
            "DEPLOYMENT_STAGE": "prod",
            "COGNITO_REGION": "ap-southeast-2",
            "S3_BUCKET_NAME": "nzshm22-toshi-api-prod",
            "COGNITO_CLIENT_ID": "3thdbdiedo5q2lqbjceg7a46pa,335e69ia1pf12k7a6dhf0kvf1m",
            "COGNITO_USER_POOL_ID": "ap-southeast-2_xas5hRD2T",
            "URL_DEFAULT_TTL": "60",
            "LEGACY_API_KEY": "***REDACTED***",
            "REGION": "ap-southeast-2"
        }
    }
}
```

## OpenSearch managed domain

Declared in serverless.yml:238-251 as Elasticsearch 6.2 / t2.small / 10GB gp2. Any divergence below is drift accumulated since 2020.

### Domain names

```
$ aws opensearch list-domain-names --region ap-southeast-2
{
    "DomainNames": [
        {
            "DomainName": "nzshm22-toshi-api-es-prod",
            "EngineType": "Elasticsearch"
        },
        {
            "DomainName": "nzshm22-toshi-api-es-test",
            "EngineType": "Elasticsearch"
        }
    ]
}
```

### Domain status: nzshm22-toshi-api-es-prod

```
$ aws opensearch describe-domain --domain-name nzshm22-toshi-api-es-prod --region ap-southeast-2
{
    "DomainStatus": {
        "DomainId": "<AWS-ACCOUNT-ID>/nzshm22-toshi-api-es-prod",
        "DomainName": "nzshm22-toshi-api-es-prod",
        "ARN": "arn:aws:es:ap-southeast-2:<AWS-ACCOUNT-ID>:domain/nzshm22-toshi-api-es-prod",
        "Created": true,
        "Deleted": false,
        "Endpoint": "search-nzshm22-toshi-api-es-prod-<REDACTED>.ap-southeast-2.es.amazonaws.com",
        "Processing": false,
        "UpgradeProcessing": false,
        "EngineVersion": "Elasticsearch_7.10",
        "ClusterConfig": {
            "InstanceType": "m7g.medium.search",
            "InstanceCount": 1,
            "DedicatedMasterEnabled": false,
            "ZoneAwarenessEnabled": false,
            "WarmEnabled": false,
            "ColdStorageOptions": {
                "Enabled": false
            },
            "MultiAZWithStandbyEnabled": false,
            "NodeOptions": [
                {
                    "NodeType": "coordinator",
                    "NodeConfig": {
                        "Enabled": false
                    }
                }
            ]
        },
        "EBSOptions": {
            "EBSEnabled": true,
            "VolumeType": "gp3",
            "VolumeSize": 50,
            "Iops": 3000,
            "Throughput": 125
        },
        "AccessPolicies": "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"AWS\":\"*\"},\"Action\":[\"es:*\",\"es:ESHttpGet\"],\"Resource\":\"arn:aws:es:ap-southeast-2:<AWS-ACCOUNT-ID>:domain/nzshm22-toshi-api-es-prod/*\",\"Condition\":{\"IpAddress\":{\"aws:SourceIp\":\"<REDACTED-IP>\"}}}]}",
        "IPAddressType": "ipv4",
        "SnapshotOptions": {
            "AutomatedSnapshotStartHour": 0
        },
        "CognitoOptions": {
            "Enabled": false
        },
        "EncryptionAtRestOptions": {
            "Enabled": false
        },
        "NodeToNodeEncryptionOptions": {
            "Enabled": false
        },
        "AdvancedOptions": {
            "rest.action.multi.allow_explicit_index": "true",
            "override_main_response_version": "true"
        },
        "LogPublishingOptions": {
            "ES_APPLICATION_LOGS": {
                "CloudWatchLogsLogGroupArn": "arn:aws:logs:ap-southeast-2:<AWS-ACCOUNT-ID>:log-group:/aws/OpenSearchService/domains/nzshm22-toshi-api-es-prod/application-logs",
                "Enabled": true
            },
            "INDEX_SLOW_LOGS": {
                "CloudWatchLogsLogGroupArn": "arn:aws:logs:ap-southeast-2:<AWS-ACCOUNT-ID>:log-group:/aws/OpenSearchService/domains/nzshm22-toshi-api-es-prod/index-logs",
                "Enabled": true
            }
        },
        "ServiceSoftwareOptions": {
            "CurrentVersion": "Elasticsearch_7_10_R20250403",
            "NewVersion": "Elasticsearch_7_10_R20260720",
            "UpdateAvailable": true,
            "Cancellable": false,
            "UpdateStatus": "ELIGIBLE",
            "Description": "A newer release Elasticsearch_7_10_R20260720 is available.",
            "AutomatedUpdateDate": "1970-01-01T12:00:00+12:00",
            "OptionalDeployment": true
        },
        "DomainEndpointOptions": {
            "EnforceHTTPS": false,
            "TLSSecurityPolicy": "Policy-Min-TLS-1-2-2019-07",
            "CustomEndpointEnabled": false
        },
        "AdvancedSecurityOptions": {
            "Enabled": false,
            "InternalUserDatabaseEnabled": false
        },
        "IdentityCenterOptions": {},
        "AutoTuneOptions": {
            "State": "DISABLED",
            "UseOffPeakWindow": false
        },
        "ChangeProgressDetails": {
            "ChangeId": "bd5c14e5-51a9-4fa1-a99c-70d8daae767d",
            "ConfigChangeStatus": "Completed",
            "InitiatedBy": "CUSTOMER",
            "StartTime": "2026-05-05T02:07:43.671000+12:00",
            "LastUpdatedTime": "2026-05-05T02:08:28.270000+12:00"
        },
        "OffPeakWindowOptions": {
            "Enabled": false,
            "OffPeakWindow": {
                "WindowStartTime": {
                    "Hours": 0,
                    "Minutes": 0
                }
            }
        },
        "SoftwareUpdateOptions": {
            "AutoSoftwareUpdateEnabled": false,
            "UseLatestServiceSoftwareForBlueGreen": true
        },
        "DomainProcessingStatus": "Active",
        "ModifyingProperties": [],
        "AIMLOptions": {
            "NaturalLanguageQueryGenerationOptions": {
                "DesiredState": "DISABLED",
                "CurrentState": "NOT_ENABLED"
            },
            "S3VectorsEngine": {
                "Enabled": false
            },
            "ServerlessVectorAcceleration": {
                "Enabled": false
            }
        },
        "DeploymentStrategyOptions": {
            "DeploymentStrategy": "CapacityOptimized"
        },
        "AutomatedSnapshotPauseOptions": {
            "Enabled": false,
            "State": "Disabled"
        },
        "UseCase": "MIXED",
        "EngineMode": "GENERAL"
    }
}
```

### Domain config (includes access policies): nzshm22-toshi-api-es-prod

```
$ aws opensearch describe-domain-config --domain-name nzshm22-toshi-api-es-prod --region ap-southeast-2 --query DomainConfig.{Engine:EngineVersion.Options,Cluster:ClusterConfig.Options,EBS:EBSOptions.Options,Access:AccessPolicies.Options,Advanced:AdvancedOptions.Options}
{
    "Engine": "Elasticsearch_7.10",
    "Cluster": {
        "InstanceType": "m7g.medium.search",
        "InstanceCount": 1,
        "DedicatedMasterEnabled": false,
        "ZoneAwarenessEnabled": false,
        "WarmEnabled": false,
        "ColdStorageOptions": {
            "Enabled": false
        },
        "MultiAZWithStandbyEnabled": false,
        "NodeOptions": [
            {
                "NodeType": "coordinator",
                "NodeConfig": {
                    "Enabled": false
                }
            }
        ]
    },
    "EBS": {
        "EBSEnabled": true,
        "VolumeType": "gp3",
        "VolumeSize": 50,
        "Iops": 3000,
        "Throughput": 125
    },
    "Access": "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"AWS\":\"*\"},\"Action\":[\"es:*\",\"es:ESHttpGet\"],\"Resource\":\"arn:aws:es:ap-southeast-2:<AWS-ACCOUNT-ID>:domain/nzshm22-toshi-api-es-prod/*\",\"Condition\":{\"IpAddress\":{\"aws:SourceIp\":\"<REDACTED-IP>\"}}}]}",
    "Advanced": {
        "rest.action.multi.allow_explicit_index": "true",
        "override_main_response_version": "true"
    }
}
```

### Metric ClusterIndexWritesBlocked: nzshm22-toshi-api-es-prod

```
$ aws cloudwatch get-metric-statistics --namespace AWS/ES --metric-name ClusterIndexWritesBlocked --dimensions Name=DomainName,Value=nzshm22-toshi-api-es-prod Name=ClientId,Value=<AWS-ACCOUNT-ID> --start-time 2026-05-24T00:00:00Z --end-time 2026-09-21T00:00:00Z --period 86400 --statistics Maximum Sum --region ap-southeast-2 --query sort_by(Datapoints, &Timestamp)[].{T:Timestamp,Max:Maximum,Sum:Sum}
[
    {
        "T": "2026-05-24T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-05-25T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-05-26T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-05-27T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-05-28T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-05-29T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-05-30T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-05-31T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-01T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-02T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-03T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-04T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-05T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-06T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-07T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-08T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-09T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-10T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-11T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-12T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-13T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-14T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-15T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-16T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-17T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-18T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-19T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-20T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-21T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-22T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-23T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-24T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-25T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-26T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-27T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-28T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-29T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-30T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-01T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-02T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-03T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-04T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-05T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-06T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-07T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-08T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-09T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-10T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-11T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-12T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-13T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-14T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-15T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-16T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-17T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-18T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-19T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-20T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-21T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-22T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-23T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-24T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-25T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-26T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-27T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-28T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-29T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-30T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-31T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-01T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-02T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-03T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-04T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-05T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-06T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-07T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-08T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-09T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-10T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-11T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-12T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-13T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-14T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-15T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-16T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-17T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-18T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-19T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-20T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-21T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-22T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-23T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-24T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-25T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-26T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-27T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-28T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-29T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-30T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-31T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-01T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-02T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-03T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-04T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-05T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-06T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-07T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-08T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-09T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-10T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-11T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-12T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-13T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-14T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-15T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-16T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-17T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-18T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-19T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-20T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    }
]
```

### Metric FreeStorageSpace: nzshm22-toshi-api-es-prod

```
$ aws cloudwatch get-metric-statistics --namespace AWS/ES --metric-name FreeStorageSpace --dimensions Name=DomainName,Value=nzshm22-toshi-api-es-prod Name=ClientId,Value=<AWS-ACCOUNT-ID> --start-time 2026-05-24T00:00:00Z --end-time 2026-09-21T00:00:00Z --period 86400 --statistics Maximum Sum --region ap-southeast-2 --query sort_by(Datapoints, &Timestamp)[].{T:Timestamp,Max:Maximum,Sum:Sum}
[
    {
        "T": "2026-05-24T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-05-25T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-05-26T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-05-27T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47963835.32800002
    },
    {
        "T": "2026-05-28T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47930503.96600001
    },
    {
        "T": "2026-05-29T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-05-30T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-05-31T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-06-01T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-06-02T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.706000015
    },
    {
        "T": "2026-06-03T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-06-04T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-06-05T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-06-06T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-06-07T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-06-08T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.706000015
    },
    {
        "T": "2026-06-09T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-06-10T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.61600002
    },
    {
        "T": "2026-06-11T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-06-12T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47963835.34400002
    },
    {
        "T": "2026-06-13T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-06-14T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-06-15T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.706000015
    },
    {
        "T": "2026-06-16T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-06-17T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.706000015
    },
    {
        "T": "2026-06-18T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-06-19T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-06-20T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-06-21T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-06-22T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-06-23T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-06-24T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-06-25T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.706000015
    },
    {
        "T": "2026-06-26T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47963835.34400002
    },
    {
        "T": "2026-06-27T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-06-28T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-06-29T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-06-30T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-07-01T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-07-02T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-07-03T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-07-04T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-07-05T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-07-06T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-07-07T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-07-08T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-07-09T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-07-10T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.706000015
    },
    {
        "T": "2026-07-11T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-07-12T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-07-13T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-07-14T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.706000015
    },
    {
        "T": "2026-07-15T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-07-16T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-07-17T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-07-18T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-07-19T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47963835.34400002
    },
    {
        "T": "2026-07-20T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-07-21T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-07-22T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.702000014
    },
    {
        "T": "2026-07-23T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-07-24T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-07-25T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-07-26T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-07-27T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47697184.412000015
    },
    {
        "T": "2026-07-28T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.706000015
    },
    {
        "T": "2026-07-29T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47963835.34400002
    },
    {
        "T": "2026-07-30T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47897172.61200002
    },
    {
        "T": "2026-07-31T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-08-01T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-08-02T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-08-03T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-08-04T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47963835.34000002
    },
    {
        "T": "2026-08-05T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-08-06T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-08-07T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-08-08T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-08-09T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-08-10T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-08-11T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-08-12T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-08-13T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-08-14T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-08-15T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-08-16T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-08-17T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-08-18T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-08-19T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-08-20T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47963835.34400002
    },
    {
        "T": "2026-08-21T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-08-22T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-08-23T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-08-24T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997166.710000016
    },
    {
        "T": "2026-08-25T12:00:00+12:00",
        "Max": 33331.366,
        "Sum": 47997131.981
    },
    {
        "T": "2026-08-26T12:00:00+12:00",
        "Max": 33331.331,
        "Sum": 47997116.30499999
    },
    {
        "T": "2026-08-27T12:00:00+12:00",
        "Max": 33331.331,
        "Sum": 47997116.30499999
    },
    {
        "T": "2026-08-28T12:00:00+12:00",
        "Max": 33331.331,
        "Sum": 47997116.30099999
    },
    {
        "T": "2026-08-29T12:00:00+12:00",
        "Max": 33331.331,
        "Sum": 47997116.30499999
    },
    {
        "T": "2026-08-30T12:00:00+12:00",
        "Max": 33331.331,
        "Sum": 47997116.30499999
    },
    {
        "T": "2026-08-31T12:00:00+12:00",
        "Max": 33331.331,
        "Sum": 47963784.97399999
    },
    {
        "T": "2026-09-01T12:00:00+12:00",
        "Max": 33331.331,
        "Sum": 47997116.30499999
    },
    {
        "T": "2026-09-02T12:00:00+12:00",
        "Max": 33331.331,
        "Sum": 47997116.30499999
    },
    {
        "T": "2026-09-03T12:00:00+12:00",
        "Max": 33331.331,
        "Sum": 47997116.30499999
    },
    {
        "T": "2026-09-04T12:00:00+12:00",
        "Max": 33331.331,
        "Sum": 47997116.30099999
    },
    {
        "T": "2026-09-05T12:00:00+12:00",
        "Max": 33331.331,
        "Sum": 47997116.30499999
    },
    {
        "T": "2026-09-06T12:00:00+12:00",
        "Max": 33331.331,
        "Sum": 47997116.30499999
    },
    {
        "T": "2026-09-07T12:00:00+12:00",
        "Max": 33331.331,
        "Sum": 47997116.30499999
    },
    {
        "T": "2026-09-08T12:00:00+12:00",
        "Max": 33331.331,
        "Sum": 47997116.30499999
    },
    {
        "T": "2026-09-09T12:00:00+12:00",
        "Max": 33331.331,
        "Sum": 47963784.96599999
    },
    {
        "T": "2026-09-10T12:00:00+12:00",
        "Max": 33331.331,
        "Sum": 47997116.30499999
    },
    {
        "T": "2026-09-11T12:00:00+12:00",
        "Max": 33331.331,
        "Sum": 47997116.30499999
    },
    {
        "T": "2026-09-12T12:00:00+12:00",
        "Max": 33331.331,
        "Sum": 47997116.30499999
    },
    {
        "T": "2026-09-13T12:00:00+12:00",
        "Max": 33331.331,
        "Sum": 47997116.30499999
    },
    {
        "T": "2026-09-14T12:00:00+12:00",
        "Max": 33331.331,
        "Sum": 47997116.30099999
    },
    {
        "T": "2026-09-15T12:00:00+12:00",
        "Max": 33331.331,
        "Sum": 47997116.30499999
    },
    {
        "T": "2026-09-16T12:00:00+12:00",
        "Max": 33331.331,
        "Sum": 47997116.30499999
    },
    {
        "T": "2026-09-17T12:00:00+12:00",
        "Max": 33331.331,
        "Sum": 47997116.30499999
    },
    {
        "T": "2026-09-18T12:00:00+12:00",
        "Max": 33331.331,
        "Sum": 47963784.97399999
    },
    {
        "T": "2026-09-19T12:00:00+12:00",
        "Max": 33331.331,
        "Sum": 47997116.30499999
    },
    {
        "T": "2026-09-20T12:00:00+12:00",
        "Max": 33331.331,
        "Sum": 47997116.30499999
    }
]
```

### Metric SearchRate: nzshm22-toshi-api-es-prod

```
$ aws cloudwatch get-metric-statistics --namespace AWS/ES --metric-name SearchRate --dimensions Name=DomainName,Value=nzshm22-toshi-api-es-prod Name=ClientId,Value=<AWS-ACCOUNT-ID> --start-time 2026-05-24T00:00:00Z --end-time 2026-09-21T00:00:00Z --period 86400 --statistics Maximum Sum --region ap-southeast-2 --query sort_by(Datapoints, &Timestamp)[].{T:Timestamp,Max:Maximum,Sum:Sum}
[
    {
        "T": "2026-05-24T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-05-25T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-05-26T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-05-27T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-05-28T12:00:00+12:00",
        "Max": 5.0,
        "Sum": 55.0
    },
    {
        "T": "2026-05-29T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-05-30T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-05-31T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-01T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-02T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-03T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-04T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-05T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-06T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-07T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-08T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-09T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-10T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-11T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-12T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-13T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-14T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-15T12:00:00+12:00",
        "Max": 10.0,
        "Sum": 60.0
    },
    {
        "T": "2026-06-16T12:00:00+12:00",
        "Max": 40.0,
        "Sum": 165.0
    },
    {
        "T": "2026-06-17T12:00:00+12:00",
        "Max": 30.0,
        "Sum": 100.0
    },
    {
        "T": "2026-06-18T12:00:00+12:00",
        "Max": 5.0,
        "Sum": 55.0
    },
    {
        "T": "2026-06-19T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-20T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-21T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-22T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-23T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-24T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-25T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-26T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-27T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-28T12:00:00+12:00",
        "Max": 10.0,
        "Sum": 60.0
    },
    {
        "T": "2026-06-29T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-30T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-01T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-02T12:00:00+12:00",
        "Max": 5.0,
        "Sum": 55.0
    },
    {
        "T": "2026-07-03T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-04T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-05T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-06T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-07T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-08T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-09T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-10T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-11T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-12T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-13T12:00:00+12:00",
        "Max": 15.0,
        "Sum": 70.0
    },
    {
        "T": "2026-07-14T12:00:00+12:00",
        "Max": 5.0,
        "Sum": 70.0
    },
    {
        "T": "2026-07-15T12:00:00+12:00",
        "Max": 5.0,
        "Sum": 80.0
    },
    {
        "T": "2026-07-16T12:00:00+12:00",
        "Max": 5.0,
        "Sum": 55.0
    },
    {
        "T": "2026-07-17T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-18T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-19T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-20T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-21T12:00:00+12:00",
        "Max": 5.0,
        "Sum": 60.0
    },
    {
        "T": "2026-07-22T12:00:00+12:00",
        "Max": 35.0,
        "Sum": 145.0
    },
    {
        "T": "2026-07-23T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-24T12:00:00+12:00",
        "Max": 5.0,
        "Sum": 55.0
    },
    {
        "T": "2026-07-25T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-26T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-27T12:00:00+12:00",
        "Max": 2.0,
        "Sum": -17690.0
    },
    {
        "T": "2026-07-28T12:00:00+12:00",
        "Max": 5.0,
        "Sum": 55.0
    },
    {
        "T": "2026-07-29T12:00:00+12:00",
        "Max": 5.0,
        "Sum": 60.0
    },
    {
        "T": "2026-07-30T12:00:00+12:00",
        "Max": 5.0,
        "Sum": 55.0
    },
    {
        "T": "2026-07-31T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-01T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-02T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-03T12:00:00+12:00",
        "Max": 15.0,
        "Sum": 115.0
    },
    {
        "T": "2026-08-04T12:00:00+12:00",
        "Max": 15.0,
        "Sum": 80.0
    },
    {
        "T": "2026-08-05T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-06T12:00:00+12:00",
        "Max": 5.0,
        "Sum": 55.0
    },
    {
        "T": "2026-08-07T12:00:00+12:00",
        "Max": 6.0,
        "Sum": 60.0
    },
    {
        "T": "2026-08-08T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-09T12:00:00+12:00",
        "Max": 5.0,
        "Sum": 55.0
    },
    {
        "T": "2026-08-10T12:00:00+12:00",
        "Max": 10.0,
        "Sum": 95.0
    },
    {
        "T": "2026-08-11T12:00:00+12:00",
        "Max": 15.0,
        "Sum": 65.0
    },
    {
        "T": "2026-08-12T12:00:00+12:00",
        "Max": 15.0,
        "Sum": 110.0
    },
    {
        "T": "2026-08-13T12:00:00+12:00",
        "Max": 5.0,
        "Sum": 55.0
    },
    {
        "T": "2026-08-14T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-15T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-16T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-17T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-18T12:00:00+12:00",
        "Max": 6.0,
        "Sum": 60.0
    },
    {
        "T": "2026-08-19T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-20T12:00:00+12:00",
        "Max": 15.0,
        "Sum": 90.0
    },
    {
        "T": "2026-08-21T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-22T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-23T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-24T12:00:00+12:00",
        "Max": 5.0,
        "Sum": 55.0
    },
    {
        "T": "2026-08-25T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-26T12:00:00+12:00",
        "Max": 15.0,
        "Sum": 70.0
    },
    {
        "T": "2026-08-27T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-28T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-29T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-30T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-31T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 49.0
    },
    {
        "T": "2026-09-01T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-02T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-03T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-04T12:00:00+12:00",
        "Max": 5.0,
        "Sum": 55.0
    },
    {
        "T": "2026-09-05T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-06T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-07T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-08T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-09T12:00:00+12:00",
        "Max": 25.0,
        "Sum": 120.0
    },
    {
        "T": "2026-09-10T12:00:00+12:00",
        "Max": 15.0,
        "Sum": 65.0
    },
    {
        "T": "2026-09-11T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-12T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-13T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-14T12:00:00+12:00",
        "Max": 59.0,
        "Sum": 242.0
    },
    {
        "T": "2026-09-15T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-16T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-17T12:00:00+12:00",
        "Max": 5.0,
        "Sum": 55.0
    },
    {
        "T": "2026-09-18T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-19T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-20T12:00:00+12:00",
        "Max": 2.0,
        "Sum": 50.0
    }
]
```

### Metric IndexingRate: nzshm22-toshi-api-es-prod

```
$ aws cloudwatch get-metric-statistics --namespace AWS/ES --metric-name IndexingRate --dimensions Name=DomainName,Value=nzshm22-toshi-api-es-prod Name=ClientId,Value=<AWS-ACCOUNT-ID> --start-time 2026-05-24T00:00:00Z --end-time 2026-09-21T00:00:00Z --period 86400 --statistics Maximum Sum --region ap-southeast-2 --query sort_by(Datapoints, &Timestamp)[].{T:Timestamp,Max:Maximum,Sum:Sum}
[
    {
        "T": "2026-05-24T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-05-25T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-05-26T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-05-27T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-05-28T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-05-29T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-05-30T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-05-31T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-01T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-02T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-03T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-04T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-05T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-06T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-07T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-08T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-09T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-10T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-11T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-12T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-13T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-14T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-15T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-16T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-17T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-18T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-19T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-20T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-21T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-22T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-23T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-24T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-25T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-26T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-27T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-28T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-29T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-06-30T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-01T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-02T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-03T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-04T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-05T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-06T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-07T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-08T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-09T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-10T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-11T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-12T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-13T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-14T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-15T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-16T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-17T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-18T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-19T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-20T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-21T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-22T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-23T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-24T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-25T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-26T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-27T12:00:00+12:00",
        "Max": 8.0,
        "Sum": -3073.0
    },
    {
        "T": "2026-07-28T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-29T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-30T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-07-31T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-01T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-02T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-03T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-04T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-05T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-06T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-07T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-08T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-09T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-10T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-11T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-12T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-13T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-14T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-15T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-16T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-17T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-18T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-19T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-20T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-21T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-22T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-23T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-24T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-25T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-26T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-27T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-28T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-29T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-30T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-08-31T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-09-01T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-09-02T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-09-03T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-09-04T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-09-05T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-09-06T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-09-07T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-09-08T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-09-09T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-09-10T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-09-11T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-09-12T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-09-13T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-09-14T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-09-15T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-09-16T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-09-17T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-09-18T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-09-19T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    },
    {
        "T": "2026-09-20T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 8.0
    }
]
```

### Index state /_cluster/health: nzshm22-toshi-api-es-prod

```
HTTP 200
{"cluster_name":"<AWS-ACCOUNT-ID>:nzshm22-toshi-api-es-prod","status":"yellow","timed_out":false,"number_of_nodes":1,"number_of_data_nodes":1,"discovered_master":true,"active_primary_shards":6,"active_shards":6,"relocating_shards":0,"initializing_shards":0,"unassigned_shards":5,"delayed_unassigned_shards":0,"number_of_pending_tasks":0,"number_of_in_flight_fetch":0,"task_max_waiting_in_queue_millis":0,"active_shards_percent_as_number":54.54545454545454}
```

### Index state /_cat/indices?v: nzshm22-toshi-api-es-prod

```
HTTP 200
health status index              uuid                   pri rep docs.count docs.deleted store.size pri.store.size
yellow open   toshi_index_mapped xSzfx-euR6uwGVkFNgduvg   5   1   11452379          410      4.1gb          4.1gb
green  open   .kibana_1          vnNxacemQoyXoFsDQcT5bA   1   0         15            0      8.8kb          8.8kb

```

### Index state /_all/_settings: nzshm22-toshi-api-es-prod

```
HTTP 200
{".kibana_1":{"settings":{"index":{"number_of_shards":"1","auto_expand_replicas":"0-1","provided_name":".kibana_1","creation_date":"1741937375782","number_of_replicas":"0","uuid":"vnNxacemQoyXoFsDQcT5bA","version":{"created":"7100299"}}}},"toshi_index_mapped":{"settings":{"index":{"creation_date":"1715824211546","number_of_shards":"5","number_of_replicas":"1","uuid":"xSzfx-euR6uwGVkFNgduvg","version":{"created":"7100299"},"provided_name":"toshi_index_mapped"}}}}
```

### Index state /toshi_index_mapped/_mapping: nzshm22-toshi-api-es-prod

```
HTTP 200
{"toshi_index_mapped":{"mappings":{"properties":{"agent_name":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"aggregation_fn":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"argument_lists":{"properties":{"k":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"v":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}}}},"arguments":{"properties":{"k":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"v":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}}}},"children":{"properties":{"child_clazz":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"child_id":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}}}},"clazz_name":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"column_headers":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"column_types":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"common_rupture_set":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"config":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"created":{"type":"date"},"csv_archive":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"description":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"duration":{"type":"float"},"environment":{"properties":{"k":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"v":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}}}},"executor":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"fault_models":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"file_name":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"file_size":{"type":"long"},"files":{"properties":{"file_id":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"file_role":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}}}},"general_task_id":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"gmcm_logic_tree":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"hazard_solution":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"hdf5_archive":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"id":{"type":"long"},"md5_digest":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"meta":{"properties":{"k":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"v":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}}}},"metrics":{"properties":{"k":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"v":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}}}},"model_type":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"modified_config":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"name":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"object_id":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"openquake_config":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"parents":{"properties":{"parent_clazz":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"parent_id":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}}}},"predecessors":{"properties":{"depth":{"type":"long"},"id":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}}}},"produced_by":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"produced_by_id":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"relations":{"properties":{"id":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"role":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}}}},"result":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"rows":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"source_models":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"source_solution":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"source_solutions":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"srm_logic_tree":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"state":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"subtask_count":{"type":"long"},"subtask_type":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"table_type":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"tables":{"properties":{"created":{"type":"date"},"dimensions":{"properties":{"k":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"v":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}}}},"identity":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"label":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"table_id":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"table_type":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}}}},"task_args":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"task_type":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"template_archive":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"title":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}}}}}}
```

### Index state /toshi_index_mapped/_count: nzshm22-toshi-api-es-prod

```
HTTP 200
{"count":11452379,"_shards":{"total":5,"successful":5,"skipped":0,"failed":0}}
```

### Domain status: nzshm22-toshi-api-es-test

```
$ aws opensearch describe-domain --domain-name nzshm22-toshi-api-es-test --region ap-southeast-2
{
    "DomainStatus": {
        "DomainId": "<AWS-ACCOUNT-ID>/nzshm22-toshi-api-es-test",
        "DomainName": "nzshm22-toshi-api-es-test",
        "ARN": "arn:aws:es:ap-southeast-2:<AWS-ACCOUNT-ID>:domain/nzshm22-toshi-api-es-test",
        "Created": true,
        "Deleted": false,
        "Endpoint": "search-nzshm22-toshi-api-es-test-<REDACTED>.ap-southeast-2.es.amazonaws.com",
        "Processing": false,
        "UpgradeProcessing": false,
        "EngineVersion": "Elasticsearch_7.10",
        "ClusterConfig": {
            "InstanceType": "t3.small.search",
            "InstanceCount": 1,
            "DedicatedMasterEnabled": false,
            "ZoneAwarenessEnabled": false,
            "WarmEnabled": false,
            "ColdStorageOptions": {
                "Enabled": false
            },
            "MultiAZWithStandbyEnabled": false
        },
        "EBSOptions": {
            "EBSEnabled": true,
            "VolumeType": "gp3",
            "VolumeSize": 10,
            "Iops": 3000,
            "Throughput": 125
        },
        "AccessPolicies": "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"AWS\":\"*\"},\"Action\":[\"es:*\",\"es:ESHttpGet\"],\"Resource\":\"arn:aws:es:ap-southeast-2:<AWS-ACCOUNT-ID>:domain/nzshm22-toshi-api-es-prod/*\",\"Condition\":{\"IpAddress\":{\"aws:SourceIp\":\"<REDACTED-IP>\"}}}]}",
        "IPAddressType": "ipv4",
        "SnapshotOptions": {},
        "CognitoOptions": {
            "Enabled": false
        },
        "EncryptionAtRestOptions": {
            "Enabled": false
        },
        "NodeToNodeEncryptionOptions": {
            "Enabled": false
        },
        "AdvancedOptions": {
            "indices.fielddata.cache.size": "20",
            "override_main_response_version": "false",
            "indices.query.bool.max_clause_count": "1024",
            "rest.action.multi.allow_explicit_index": "true"
        },
        "ServiceSoftwareOptions": {
            "CurrentVersion": "Elasticsearch_7_10_R20251106",
            "NewVersion": "Elasticsearch_7_10_R20260720",
            "UpdateAvailable": true,
            "Cancellable": false,
            "UpdateStatus": "ELIGIBLE",
            "Description": "A newer release Elasticsearch_7_10_R20260720 is available.",
            "AutomatedUpdateDate": "1970-01-01T12:00:00+12:00",
            "OptionalDeployment": true
        },
        "DomainEndpointOptions": {
            "EnforceHTTPS": true,
            "TLSSecurityPolicy": "Policy-Min-TLS-1-2-2019-07",
            "CustomEndpointEnabled": false
        },
        "AdvancedSecurityOptions": {
            "Enabled": false,
            "InternalUserDatabaseEnabled": false,
            "AnonymousAuthEnabled": false
        },
        "IdentityCenterOptions": {},
        "AutoTuneOptions": {
            "State": "DISABLED",
            "UseOffPeakWindow": false
        },
        "ChangeProgressDetails": {
            "ChangeId": "81a426a1-1625-45e4-9f5c-a9a8a43f0a38",
            "ConfigChangeStatus": "Completed",
            "InitiatedBy": "CUSTOMER",
            "StartTime": "2026-02-04T15:26:42.051000+13:00",
            "LastUpdatedTime": "2026-02-04T15:26:59.688000+13:00"
        },
        "OffPeakWindowOptions": {
            "Enabled": true,
            "OffPeakWindow": {
                "WindowStartTime": {
                    "Hours": 0,
                    "Minutes": 0
                }
            }
        },
        "SoftwareUpdateOptions": {
            "AutoSoftwareUpdateEnabled": false,
            "UseLatestServiceSoftwareForBlueGreen": true
        },
        "DomainProcessingStatus": "Active",
        "ModifyingProperties": [],
        "AIMLOptions": {
            "NaturalLanguageQueryGenerationOptions": {
                "DesiredState": "DISABLED",
                "CurrentState": "NOT_ENABLED"
            },
            "S3VectorsEngine": {
                "Enabled": false
            },
            "ServerlessVectorAcceleration": {
                "Enabled": false
            }
        },
        "DeploymentStrategyOptions": {
            "DeploymentStrategy": "CapacityOptimized"
        },
        "AutomatedSnapshotPauseOptions": {
            "Enabled": false,
            "State": "Disabled"
        },
        "UseCase": "MIXED",
        "EngineMode": "GENERAL"
    }
}
```

### Domain config (includes access policies): nzshm22-toshi-api-es-test

```
$ aws opensearch describe-domain-config --domain-name nzshm22-toshi-api-es-test --region ap-southeast-2 --query DomainConfig.{Engine:EngineVersion.Options,Cluster:ClusterConfig.Options,EBS:EBSOptions.Options,Access:AccessPolicies.Options,Advanced:AdvancedOptions.Options}
{
    "Engine": "Elasticsearch_7.10",
    "Cluster": {
        "InstanceType": "t3.small.search",
        "InstanceCount": 1,
        "DedicatedMasterEnabled": false,
        "ZoneAwarenessEnabled": false,
        "WarmEnabled": false,
        "ColdStorageOptions": {
            "Enabled": false
        },
        "MultiAZWithStandbyEnabled": false
    },
    "EBS": {
        "EBSEnabled": true,
        "VolumeType": "gp3",
        "VolumeSize": 10,
        "Iops": 3000,
        "Throughput": 125
    },
    "Access": "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"AWS\":\"*\"},\"Action\":[\"es:*\",\"es:ESHttpGet\"],\"Resource\":\"arn:aws:es:ap-southeast-2:<AWS-ACCOUNT-ID>:domain/nzshm22-toshi-api-es-prod/*\",\"Condition\":{\"IpAddress\":{\"aws:SourceIp\":\"<REDACTED-IP>\"}}}]}",
    "Advanced": {
        "indices.fielddata.cache.size": "20",
        "override_main_response_version": "false",
        "indices.query.bool.max_clause_count": "1024",
        "rest.action.multi.allow_explicit_index": "true"
    }
}
```

### Metric ClusterIndexWritesBlocked: nzshm22-toshi-api-es-test

```
$ aws cloudwatch get-metric-statistics --namespace AWS/ES --metric-name ClusterIndexWritesBlocked --dimensions Name=DomainName,Value=nzshm22-toshi-api-es-test Name=ClientId,Value=<AWS-ACCOUNT-ID> --start-time 2026-05-24T00:00:00Z --end-time 2026-09-21T00:00:00Z --period 86400 --statistics Maximum Sum --region ap-southeast-2 --query sort_by(Datapoints, &Timestamp)[].{T:Timestamp,Max:Maximum,Sum:Sum}
[
    {
        "T": "2026-05-24T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-05-25T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-05-26T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-05-27T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-05-28T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-05-29T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-05-30T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-05-31T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-01T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-02T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-03T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-04T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-05T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-06T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-07T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-08T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-09T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-10T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-11T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-12T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-13T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-14T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-15T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-16T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-17T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-18T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-19T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-20T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-21T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-22T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-23T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-24T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-25T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-26T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-27T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-28T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-29T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-30T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-01T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-02T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-03T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-04T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-05T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-06T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-07T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-08T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-09T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-10T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-11T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-12T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-13T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-14T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-15T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-16T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-17T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-18T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-19T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-20T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-21T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-22T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-23T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-24T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-25T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-26T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-27T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-28T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-29T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-30T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-31T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-01T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-02T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-03T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-04T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-05T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-06T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-07T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-08T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-09T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-10T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-11T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-12T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-13T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-14T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-15T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-16T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-17T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-18T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-19T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-20T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-21T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-22T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-23T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-24T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-25T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-26T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-27T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-28T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-29T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-30T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-31T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-01T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-02T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-03T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-04T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-05T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-06T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-07T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-08T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-09T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-10T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-11T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-12T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-13T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-14T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-15T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-16T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-17T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-18T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-19T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-20T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    }
]
```

### Metric FreeStorageSpace: nzshm22-toshi-api-es-test

```
$ aws cloudwatch get-metric-statistics --namespace AWS/ES --metric-name FreeStorageSpace --dimensions Name=DomainName,Value=nzshm22-toshi-api-es-test Name=ClientId,Value=<AWS-ACCOUNT-ID> --start-time 2026-05-24T00:00:00Z --end-time 2026-09-21T00:00:00Z --period 86400 --statistics Maximum Sum --region ap-southeast-2 --query sort_by(Datapoints, &Timestamp)[].{T:Timestamp,Max:Maximum,Sum:Sum}
[
    {
        "T": "2026-05-24T12:00:00+12:00",
        "Max": 7400.817,
        "Sum": 10649702.13
    },
    {
        "T": "2026-05-25T12:00:00+12:00",
        "Max": 7401.364,
        "Sum": 10657568.894
    },
    {
        "T": "2026-05-26T12:00:00+12:00",
        "Max": 7400.793,
        "Sum": 10656779.540000003
    },
    {
        "T": "2026-05-27T12:00:00+12:00",
        "Max": 7400.473,
        "Sum": 10656681.120000003
    },
    {
        "T": "2026-05-28T12:00:00+12:00",
        "Max": 7400.473,
        "Sum": 10656681.120000003
    },
    {
        "T": "2026-05-29T12:00:00+12:00",
        "Max": 7401.43,
        "Sum": 10656777.112999998
    },
    {
        "T": "2026-05-30T12:00:00+12:00",
        "Max": 7400.414,
        "Sum": 10656596.159999998
    },
    {
        "T": "2026-05-31T12:00:00+12:00",
        "Max": 7400.414,
        "Sum": 10656596.159999998
    },
    {
        "T": "2026-06-01T12:00:00+12:00",
        "Max": 7400.414,
        "Sum": 10656596.159999998
    },
    {
        "T": "2026-06-02T12:00:00+12:00",
        "Max": 7400.414,
        "Sum": 10656596.159999998
    },
    {
        "T": "2026-06-03T12:00:00+12:00",
        "Max": 7400.414,
        "Sum": 10656596.159999998
    },
    {
        "T": "2026-06-04T12:00:00+12:00",
        "Max": 7400.414,
        "Sum": 10656596.159999998
    },
    {
        "T": "2026-06-05T12:00:00+12:00",
        "Max": 7400.414,
        "Sum": 10656596.159999998
    },
    {
        "T": "2026-06-06T12:00:00+12:00",
        "Max": 7400.414,
        "Sum": 10656596.159999998
    },
    {
        "T": "2026-06-07T12:00:00+12:00",
        "Max": 7401.34,
        "Sum": 10656701.27
    },
    {
        "T": "2026-06-08T12:00:00+12:00",
        "Max": 7401.157,
        "Sum": 10657031.666000003
    },
    {
        "T": "2026-06-09T12:00:00+12:00",
        "Max": 7401.055,
        "Sum": 10649991.932000004
    },
    {
        "T": "2026-06-10T12:00:00+12:00",
        "Max": 7401.055,
        "Sum": 10657282.007
    },
    {
        "T": "2026-06-11T12:00:00+12:00",
        "Max": 7400.887,
        "Sum": 10657246.819999998
    },
    {
        "T": "2026-06-12T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.155999998
    },
    {
        "T": "2026-06-13T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-06-14T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-06-15T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-06-16T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-06-17T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-06-18T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-06-19T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-06-20T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-06-21T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-06-22T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-06-23T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-06-24T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-06-25T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-06-26T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-06-27T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-06-28T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10649843.295999998
    },
    {
        "T": "2026-06-29T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-06-30T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-07-01T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-07-02T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.155999998
    },
    {
        "T": "2026-07-03T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-07-04T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-07-05T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-07-06T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-07-07T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-07-08T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-07-09T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-07-10T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-07-11T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-07-12T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-07-13T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.155999998
    },
    {
        "T": "2026-07-14T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-07-15T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-07-16T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-07-17T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-07-18T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-07-19T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.155999998
    },
    {
        "T": "2026-07-20T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-07-21T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-07-22T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-07-23T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-07-24T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-07-25T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-07-26T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999996
    },
    {
        "T": "2026-07-27T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-07-28T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-07-29T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.155999998
    },
    {
        "T": "2026-07-30T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-07-31T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-08-01T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-08-02T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-08-03T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.155999998
    },
    {
        "T": "2026-08-04T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-08-05T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-08-06T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-08-07T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-08-08T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-08-09T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-08-10T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-08-11T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-08-12T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-08-13T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.155999998
    },
    {
        "T": "2026-08-14T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-08-15T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-08-16T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-08-17T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-08-18T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-08-19T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-08-20T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-08-21T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-08-22T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.155999998
    },
    {
        "T": "2026-08-23T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-08-24T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657244.159999998
    },
    {
        "T": "2026-08-25T12:00:00+12:00",
        "Max": 7400.864,
        "Sum": 10657208.447999997
    },
    {
        "T": "2026-08-26T12:00:00+12:00",
        "Max": 7400.828,
        "Sum": 10657192.319999997
    },
    {
        "T": "2026-08-27T12:00:00+12:00",
        "Max": 7400.828,
        "Sum": 10657192.319999997
    },
    {
        "T": "2026-08-28T12:00:00+12:00",
        "Max": 7400.828,
        "Sum": 10657192.319999997
    },
    {
        "T": "2026-08-29T12:00:00+12:00",
        "Max": 7400.828,
        "Sum": 10657192.319999997
    },
    {
        "T": "2026-08-30T12:00:00+12:00",
        "Max": 7400.828,
        "Sum": 10657192.319999997
    },
    {
        "T": "2026-08-31T12:00:00+12:00",
        "Max": 7400.828,
        "Sum": 10657192.319999997
    },
    {
        "T": "2026-09-01T12:00:00+12:00",
        "Max": 7400.828,
        "Sum": 10657192.319999997
    },
    {
        "T": "2026-09-02T12:00:00+12:00",
        "Max": 7400.828,
        "Sum": 10657192.319999997
    },
    {
        "T": "2026-09-03T12:00:00+12:00",
        "Max": 7400.828,
        "Sum": 10657192.319999997
    },
    {
        "T": "2026-09-04T12:00:00+12:00",
        "Max": 7400.828,
        "Sum": 10657192.319999997
    },
    {
        "T": "2026-09-05T12:00:00+12:00",
        "Max": 7400.828,
        "Sum": 10657192.319999997
    },
    {
        "T": "2026-09-06T12:00:00+12:00",
        "Max": 7400.828,
        "Sum": 10657192.319999997
    },
    {
        "T": "2026-09-07T12:00:00+12:00",
        "Max": 7400.828,
        "Sum": 10657192.319999997
    },
    {
        "T": "2026-09-08T12:00:00+12:00",
        "Max": 7400.828,
        "Sum": 10657192.319999997
    },
    {
        "T": "2026-09-09T12:00:00+12:00",
        "Max": 7400.828,
        "Sum": 10657192.319999997
    },
    {
        "T": "2026-09-10T12:00:00+12:00",
        "Max": 7400.828,
        "Sum": 10657192.319999998
    },
    {
        "T": "2026-09-11T12:00:00+12:00",
        "Max": 7400.828,
        "Sum": 10657192.319999997
    },
    {
        "T": "2026-09-12T12:00:00+12:00",
        "Max": 7400.828,
        "Sum": 10657192.319999998
    },
    {
        "T": "2026-09-13T12:00:00+12:00",
        "Max": 7400.828,
        "Sum": 10657192.319999997
    },
    {
        "T": "2026-09-14T12:00:00+12:00",
        "Max": 7400.828,
        "Sum": 10657192.319999998
    },
    {
        "T": "2026-09-15T12:00:00+12:00",
        "Max": 7400.828,
        "Sum": 10657192.319999997
    },
    {
        "T": "2026-09-16T12:00:00+12:00",
        "Max": 7400.828,
        "Sum": 10657192.319999997
    },
    {
        "T": "2026-09-17T12:00:00+12:00",
        "Max": 7400.828,
        "Sum": 10634989.835999997
    },
    {
        "T": "2026-09-18T12:00:00+12:00",
        "Max": 7400.828,
        "Sum": 10657192.319999997
    },
    {
        "T": "2026-09-19T12:00:00+12:00",
        "Max": 7400.828,
        "Sum": 10657192.319999997
    },
    {
        "T": "2026-09-20T12:00:00+12:00",
        "Max": 7400.828,
        "Sum": 10657192.319999998
    }
]
```

### Metric SearchRate: nzshm22-toshi-api-es-test

```
$ aws cloudwatch get-metric-statistics --namespace AWS/ES --metric-name SearchRate --dimensions Name=DomainName,Value=nzshm22-toshi-api-es-test Name=ClientId,Value=<AWS-ACCOUNT-ID> --start-time 2026-05-24T00:00:00Z --end-time 2026-09-21T00:00:00Z --period 86400 --statistics Maximum Sum --region ap-southeast-2 --query sort_by(Datapoints, &Timestamp)[].{T:Timestamp,Max:Maximum,Sum:Sum}
[
    {
        "T": "2026-05-24T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-05-25T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-05-26T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-05-27T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-05-28T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-05-29T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-05-30T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-05-31T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-01T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-02T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-03T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-04T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-05T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-06T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-07T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-08T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-09T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-10T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-11T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-12T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-13T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-14T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-15T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-16T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-17T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-18T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-19T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-20T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-21T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-22T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-23T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-24T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-25T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-26T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-27T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-28T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-29T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-06-30T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-01T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-02T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-03T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-04T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-05T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-06T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-07T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-08T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-09T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-10T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-11T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-12T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-13T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-14T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-15T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-16T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-17T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-18T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-19T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-20T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-21T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-22T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-23T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-24T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-25T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-26T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-27T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-28T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-29T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-30T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-07-31T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-01T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-02T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-03T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-04T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-05T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-06T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-07T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-08T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-09T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-10T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-11T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-12T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-13T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-14T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-15T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-16T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-17T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-18T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-19T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-20T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-21T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-22T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-23T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-24T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-25T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-26T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-27T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-28T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-29T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-30T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-08-31T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-01T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-02T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-03T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-04T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-05T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-06T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-07T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-08T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-09T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-10T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-11T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-12T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-13T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-14T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-15T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-16T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-17T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-18T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-19T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    },
    {
        "T": "2026-09-20T12:00:00+12:00",
        "Max": 3.0,
        "Sum": 50.0
    }
]
```

### Metric IndexingRate: nzshm22-toshi-api-es-test

```
$ aws cloudwatch get-metric-statistics --namespace AWS/ES --metric-name IndexingRate --dimensions Name=DomainName,Value=nzshm22-toshi-api-es-test Name=ClientId,Value=<AWS-ACCOUNT-ID> --start-time 2026-05-24T00:00:00Z --end-time 2026-09-21T00:00:00Z --period 86400 --statistics Maximum Sum --region ap-southeast-2 --query sort_by(Datapoints, &Timestamp)[].{T:Timestamp,Max:Maximum,Sum:Sum}
[
    {
        "T": "2026-05-24T12:00:00+12:00",
        "Max": 12.0,
        "Sum": 64.0
    },
    {
        "T": "2026-05-25T12:00:00+12:00",
        "Max": 18.0,
        "Sum": 192.0
    },
    {
        "T": "2026-05-26T12:00:00+12:00",
        "Max": 10.0,
        "Sum": 28.0
    },
    {
        "T": "2026-05-27T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-05-28T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-05-29T12:00:00+12:00",
        "Max": 10.0,
        "Sum": 235.0
    },
    {
        "T": "2026-05-30T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-05-31T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-01T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-02T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-03T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-04T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-05T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-06T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-07T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 100.0
    },
    {
        "T": "2026-06-08T12:00:00+12:00",
        "Max": 10.0,
        "Sum": 136.0
    },
    {
        "T": "2026-06-09T12:00:00+12:00",
        "Max": 9.0,
        "Sum": 90.0
    },
    {
        "T": "2026-06-10T12:00:00+12:00",
        "Max": 8.0,
        "Sum": 19.0
    },
    {
        "T": "2026-06-11T12:00:00+12:00",
        "Max": 10.0,
        "Sum": 47.0
    },
    {
        "T": "2026-06-12T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-13T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-14T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-15T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-16T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-17T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-18T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-19T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-20T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-21T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-22T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-23T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-24T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-25T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-26T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-27T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-28T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-29T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-06-30T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-01T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-02T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-03T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-04T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-05T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-06T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-07T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-08T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-09T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-10T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-11T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-12T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-13T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-14T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-15T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-16T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-17T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-18T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-19T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-20T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-21T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-22T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-23T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-24T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-25T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-26T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-27T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-28T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-29T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-30T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-07-31T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-01T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-02T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-03T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-04T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-05T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-06T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-07T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-08T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-09T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-10T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-11T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-12T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-13T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-14T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-15T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-16T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-17T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-18T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-19T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-20T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-21T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-22T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-23T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-24T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-25T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-26T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-27T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-28T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-29T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-30T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-08-31T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-01T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-02T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-03T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-04T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-05T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-06T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-07T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-08T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-09T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-10T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-11T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-12T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-13T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-14T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-15T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-16T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-17T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-18T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-19T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    },
    {
        "T": "2026-09-20T12:00:00+12:00",
        "Max": 0.0,
        "Sum": 0.0
    }
]
```

### Index state /_cluster/health: nzshm22-toshi-api-es-test

```
HTTP 200
{"cluster_name":"<AWS-ACCOUNT-ID>:nzshm22-toshi-api-es-test","status":"yellow","timed_out":false,"number_of_nodes":1,"number_of_data_nodes":1,"discovered_master":true,"active_primary_shards":6,"active_shards":6,"relocating_shards":0,"initializing_shards":0,"unassigned_shards":5,"delayed_unassigned_shards":0,"number_of_pending_tasks":0,"number_of_in_flight_fetch":0,"task_max_waiting_in_queue_millis":0,"active_shards_percent_as_number":54.54545454545454}
```

### Index state /_cat/indices?v: nzshm22-toshi-api-es-test

```
HTTP 200
health status index              uuid                   pri rep docs.count docs.deleted store.size pri.store.size
yellow open   toshi_index_mapped I-LXqTQwR6qJjE7MI03-Rw   5   1       1405           33      2.2mb          2.2mb
green  open   .kibana_1          uMlnmrtERKGQvQ5Q9PHatA   1   0          1            0        5kb            5kb

```

### Index state /_all/_settings: nzshm22-toshi-api-es-test

```
HTTP 200
{".kibana_1":{"settings":{"index":{"number_of_shards":"1","auto_expand_replicas":"0-1","provided_name":".kibana_1","creation_date":"1770171116484","number_of_replicas":"0","uuid":"uMlnmrtERKGQvQ5Q9PHatA","version":{"created":"7100299"}}}},"toshi_index_mapped":{"settings":{"index":{"creation_date":"1770172063087","number_of_shards":"5","number_of_replicas":"1","uuid":"I-LXqTQwR6qJjE7MI03-Rw","version":{"created":"7100299"},"provided_name":"toshi_index_mapped"}}}}
```

### Index state /toshi_index_mapped/_mapping: nzshm22-toshi-api-es-test

```
HTTP 200
{"toshi_index_mapped":{"mappings":{"properties":{"agent_name":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"argument_lists":{"properties":{"k":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"v":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}}}},"arguments":{"properties":{"k":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"v":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}}}},"children":{"properties":{"child_clazz":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"child_id":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}}}},"clazz_name":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"column_headers":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"column_types":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"created":{"type":"date"},"csv_archive":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"description":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"duration":{"type":"float"},"environment":{"properties":{"k":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"v":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}}}},"executor":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"fault_models":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"file_name":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"file_size":{"type":"long"},"files":{"properties":{"file_id":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"file_role":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}}}},"gmcm_logic_tree":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"hazard_solution":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"hdf5_archive":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"id":{"type":"long"},"md5_digest":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"meta":{"properties":{"k":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"v":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}}}},"metrics":{"properties":{"k":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"v":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}}}},"model_type":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"name":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"object_id":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"openquake_config":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"parents":{"properties":{"parent_clazz":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"parent_id":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}}}},"predecessors":{"properties":{"depth":{"type":"long"},"id":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}}}},"produced_by":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"relations":{"properties":{"id":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"role":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}}}},"relations_compressed":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"result":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"rows":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"source_solution":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"srm_logic_tree":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"state":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"subtask_count":{"type":"long"},"subtask_type":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"table_type":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"tables":{"properties":{"created":{"type":"date"},"identity":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"label":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"table_id":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"table_type":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}}}},"task_args":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"task_type":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}},"title":{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}}}}}}
```

### Index state /toshi_index_mapped/_count: nzshm22-toshi-api-es-test

```
HTTP 200
{"count":1405,"_shards":{"total":5,"successful":5,"skipped":0,"failed":0}}
```

## OpenSearch Serverless collection

Exists nowhere in the repo. Billing 744 SearchOCU-hours/month (one OCU pinned continuously, ~USD 209) plus any IndexingOCU.

### Collections

```
$ aws opensearchserverless list-collections --region ap-southeast-2
{
    "collectionSummaries": [
        {
            "id": "05dg7fpjnz61wzk9jad5",
            "name": "nshm-model-serverless-poc",
            "status": "ACTIVE",
            "arn": "arn:aws:aoss:ap-southeast-2:<AWS-ACCOUNT-ID>:collection/05dg7fpjnz61wzk9jad5",
            "kmsKeyArn": "auto"
        }
    ]
}
```

### Collection detail: nshm-model-serverless-poc

```
$ aws opensearchserverless batch-get-collection --names nshm-model-serverless-poc --region ap-southeast-2
{
    "collectionDetails": [
        {
            "id": "05dg7fpjnz61wzk9jad5",
            "name": "nshm-model-serverless-poc",
            "status": "ACTIVE",
            "type": "SEARCH",
            "description": "",
            "arn": "arn:aws:aoss:ap-southeast-2:<AWS-ACCOUNT-ID>:collection/05dg7fpjnz61wzk9jad5",
            "kmsKeyArn": "auto",
            "standbyReplicas": "ENABLED",
            "deletionProtection": "DISABLED",
            "createdDate": 1693971414747,
            "lastModifiedDate": 1693972074302,
            "collectionEndpoint": "https://<REDACTED>.ap-southeast-2.aoss.amazonaws.com",
            "dashboardEndpoint": "https://<REDACTED>.ap-southeast-2.aoss.amazonaws.com/_dashboards"
        }
    ],
    "collectionErrorDetails": []
}
```

### Metric SearchRequestRate: nshm-model-serverless-poc

```
$ aws cloudwatch get-metric-statistics --namespace AWS/AOSS --metric-name SearchRequestRate --dimensions Name=CollectionName,Value=nshm-model-serverless-poc Name=CollectionId,Value=05dg7fpjnz61wzk9jad5 --start-time 2026-05-24T00:00:00Z --end-time 2026-09-21T00:00:00Z --period 86400 --statistics Maximum Sum --region ap-southeast-2 --query sort_by(Datapoints, &Timestamp)[].{T:Timestamp,Max:Maximum,Sum:Sum}
[]
```

### Metric IngestionRequestRate: nshm-model-serverless-poc

```
$ aws cloudwatch get-metric-statistics --namespace AWS/AOSS --metric-name IngestionRequestRate --dimensions Name=CollectionName,Value=nshm-model-serverless-poc Name=CollectionId,Value=05dg7fpjnz61wzk9jad5 --start-time 2026-05-24T00:00:00Z --end-time 2026-09-21T00:00:00Z --period 86400 --statistics Maximum Sum --region ap-southeast-2 --query sort_by(Datapoints, &Timestamp)[].{T:Timestamp,Max:Maximum,Sum:Sum}
[]
```

### Metric SearchRequestErrors: nshm-model-serverless-poc

```
$ aws cloudwatch get-metric-statistics --namespace AWS/AOSS --metric-name SearchRequestErrors --dimensions Name=CollectionName,Value=nshm-model-serverless-poc Name=CollectionId,Value=05dg7fpjnz61wzk9jad5 --start-time 2026-05-24T00:00:00Z --end-time 2026-09-21T00:00:00Z --period 86400 --statistics Maximum Sum --region ap-southeast-2 --query sort_by(Datapoints, &Timestamp)[].{T:Timestamp,Max:Maximum,Sum:Sum}
[]
```

OCU metrics are account-wide. Each OCU-hour here corresponds to an OCU-hour on the bill, so these should drop to zero once the collections holding that capacity are gone.

### Metric SearchOCU: account-wide

```
$ aws cloudwatch get-metric-statistics --namespace AWS/AOSS --metric-name SearchOCU --dimensions Name=ClientId,Value=<AWS-ACCOUNT-ID> --start-time 2026-05-24T00:00:00Z --end-time 2026-09-21T00:00:00Z --period 86400 --statistics Maximum Average --region ap-southeast-2 --query sort_by(Datapoints, &Timestamp)[].{T:Timestamp,Max:Maximum,Avg:Average}
[
    {
        "T": "2026-05-24T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-05-25T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-05-26T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-05-27T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-05-28T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-05-29T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-05-30T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-05-31T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-01T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-02T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-03T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-04T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-05T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-06T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-07T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-08T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-09T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-10T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-11T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-12T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-13T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-14T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-15T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-16T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-17T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-18T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-19T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-20T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-21T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-22T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-23T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-24T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-25T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-26T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-27T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-28T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-29T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-30T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-01T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-02T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-03T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-04T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-05T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-06T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-07T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-08T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-09T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-10T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-11T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-12T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-13T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-14T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-15T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-16T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-17T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-18T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-19T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-20T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-21T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-22T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-23T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-24T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-25T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-26T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-27T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-28T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-29T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-30T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-31T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-01T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-02T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-03T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-04T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-05T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-06T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-07T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-08T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-09T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-10T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-11T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-12T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-13T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-14T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-15T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-16T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-17T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-18T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-19T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-20T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-21T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-22T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-23T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-24T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-25T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-26T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-27T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-28T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-29T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-30T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-31T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-01T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-02T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-03T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-04T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-05T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-06T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-07T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-08T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-09T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-10T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-11T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-12T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-13T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-14T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-15T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-16T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-17T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-18T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-19T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-20T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    }
]
```

### Metric IndexingOCU: account-wide

```
$ aws cloudwatch get-metric-statistics --namespace AWS/AOSS --metric-name IndexingOCU --dimensions Name=ClientId,Value=<AWS-ACCOUNT-ID> --start-time 2026-05-24T00:00:00Z --end-time 2026-09-21T00:00:00Z --period 86400 --statistics Maximum Average --region ap-southeast-2 --query sort_by(Datapoints, &Timestamp)[].{T:Timestamp,Max:Maximum,Avg:Average}
[
    {
        "T": "2026-05-24T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-05-25T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-05-26T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-05-27T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-05-28T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-05-29T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-05-30T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-05-31T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-01T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-02T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-03T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-04T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-05T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-06T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-07T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-08T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-09T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-10T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-11T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-12T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-13T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-14T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-15T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-16T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-17T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-18T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-19T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-20T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-21T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-22T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-23T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-24T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-25T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-26T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-27T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-28T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-29T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-06-30T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-01T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-02T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-03T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-04T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-05T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-06T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-07T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-08T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-09T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-10T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-11T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-12T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-13T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-14T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-15T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-16T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-17T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-18T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-19T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-20T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-21T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-22T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-23T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-24T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-25T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-26T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-27T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-28T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-29T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-30T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-07-31T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-01T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-02T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-03T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-04T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-05T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-06T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-07T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-08T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-09T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-10T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-11T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-12T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-13T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-14T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-15T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-16T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-17T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-18T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-19T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-20T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-21T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-22T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-23T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-24T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-25T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-26T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-27T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-28T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-29T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-30T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-08-31T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-01T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-02T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-03T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-04T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-05T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-06T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-07T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-08T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-09T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-10T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-11T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-12T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-13T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-14T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-15T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-16T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-17T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-18T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-19T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    },
    {
        "T": "2026-09-20T12:00:00+12:00",
        "Max": 1.0,
        "Avg": 1.0
    }
]
```

### Encryption policies

```
$ aws opensearchserverless list-security-policies --type encryption --region ap-southeast-2
{
    "securityPolicySummaries": [
        {
            "type": "encryption",
            "name": "auto-nshm-model-serverless-poc",
            "policyVersion": "MTY5Mzk3MTQxNDYyNV8x",
            "description": "nshm-model-serverless-poc",
            "createdDate": 1693971414625,
            "lastModifiedDate": 1693971414625
        }
    ]
}
```

### Network policies

```
$ aws opensearchserverless list-security-policies --type network --region ap-southeast-2
{
    "securityPolicySummaries": [
        {
            "type": "network",
            "name": "auto-nshm-model-poc-dev",
            "policyVersion": "MTY5Mzg2NDkxNTU2MV8x",
            "description": "nshm-model-poc-dev",
            "createdDate": 1693864915561,
            "lastModifiedDate": 1693864915561
        },
        {
            "type": "network",
            "name": "auto-nshm-model-serverless-poc",
            "policyVersion": "MTY5Mzk3MTQxNDYyNl8x",
            "description": "nshm-model-serverless-poc",
            "createdDate": 1693971414626,
            "lastModifiedDate": 1693971414626
        }
    ]
}
```

### Data access policies

```
$ aws opensearchserverless list-access-policies --type data --region ap-southeast-2
{
    "accessPolicySummaries": []
}
```

## Spend by usage type

'Amazon OpenSearch Service' covers both products — managed instance hours and serverless OCU hours appear under different usage types.

### Monthly cost by usage type

```
$ aws ce get-cost-and-usage --time-period Start=2026-05-01,End=2026-09-21 --granularity MONTHLY --metrics UnblendedCost --filter {"Dimensions":{"Key":"SERVICE","Values":["Amazon OpenSearch Service"]}} --group-by Type=DIMENSION,Key=USAGE_TYPE --region us-east-1
{
    "GroupDefinitions": [
        {
            "Type": "DIMENSION",
            "Key": "USAGE_TYPE"
        }
    ],
    "ResultsByTime": [
        {
            "TimePeriod": {
                "Start": "2026-05-01",
                "End": "2026-06-01"
            },
            "Total": {},
            "Groups": [
                {
                    "Keys": [
                        "APS2-APN1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APN1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0003285649",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APN2-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APS1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APS1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000511768",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APS3-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APS3-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000041772",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APS9-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APS9-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000004847",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-CAN1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-CAN1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000502672",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-DFW1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-DFW1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000307",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-DataTransfer-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-DataTransfer-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0220970763",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-DataTransfer-Regional-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0399958261",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-ES:GP2-Storage"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.2220967686",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-ES:GP3-Storage"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "8.7839998416",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-ESInstance:m7g.medium"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "63.24",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-ESInstance:t2.small"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "5.712",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-ESInstance:t3.small"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "41.664",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EU-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EU-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000036943",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUC1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUC1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000652844",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUN1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUN1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000011339",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUS1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUW2-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUW2-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.000062202",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUW3-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUW3-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000111021",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-IAH1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-IndexingOCU"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "209.064",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-NYC1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-NYC1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000004961",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-OpenSearchExtendedSupport"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.8364",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-QRO1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-QRO1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000146",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-SAE1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-SAE1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000004843",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-SearchOCU"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "209.064",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-UGW1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USE1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USE1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0006442671",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USE2-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USE2-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0011065444",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USW1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USW1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.000033274",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USW2-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USW2-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0034244549",
                            "Unit": "USD"
                        }
                    }
                }
            ],
            "Estimated": false
        },
        {
            "TimePeriod": {
                "Start": "2026-06-01",
                "End": "2026-07-01"
            },
            "Total": {},
            "Groups": [
                {
                    "Keys": [
                        "APS2-APN1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APN1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000023414",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APN2-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APN2-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.000027351",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APS1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APS1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000414917",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APS3-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APS3-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000011628",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APS6-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APS6-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.000000895",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-CAN1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-CAN1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0001269228",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-DataTransfer-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-DataTransfer-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0346134525",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-DataTransfer-Regional-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0373723862",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-ES:GP2-Storage"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.00225",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-ES:GP3-Storage"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "8.783999784",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-ESInstance:m7g.medium"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "61.2",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-ESInstance:t2.small"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.056",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-ESInstance:t3.small"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "40.32",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EU-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EU-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000018533",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUC1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUC1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000496917",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUN1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUN1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000172575",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUW2-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUW2-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000439441",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUW3-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUW3-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000001171",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-IndexingOCU"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "202.32",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-NYC1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-NYC1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000012744",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-OpenSearchExtendedSupport"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0082",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-PHX1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-PHX1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000146",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-SearchOCU"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "202.32",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-UGW1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USE1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USE1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0014851528",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USE2-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USE2-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0010214135",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USW1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USW1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000214927",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USW2-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USW2-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0026772649",
                            "Unit": "USD"
                        }
                    }
                }
            ],
            "Estimated": false
        },
        {
            "TimePeriod": {
                "Start": "2026-07-01",
                "End": "2026-08-01"
            },
            "Total": {},
            "Groups": [
                {
                    "Keys": [
                        "APS2-APN1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APN1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000032744",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APS1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APS1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000531741",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APS3-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APS3-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000019614",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-CAN1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-CAN1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000535813",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-DataTransfer-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-DataTransfer-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0206877304",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-DataTransfer-Regional-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0392055327",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-ES:GP3-Storage"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "8.7839998416",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-ESInstance:m7g.medium"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "63.24",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-ESInstance:t3.small"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "41.664",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EU-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EU-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000120462",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUC1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUC1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000501764",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUN1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUN1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000005589",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUW2-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUW2-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000512615",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUW3-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUW3-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000015671",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-IndexingOCU"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "209.064",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-SAE1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-SAE1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000005518",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-SearchOCU"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "209.064",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USE1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USE1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0016129516",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USE2-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USE2-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0009987788",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USW1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USW1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000100397",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USW2-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USW2-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0027099192",
                            "Unit": "USD"
                        }
                    }
                }
            ],
            "Estimated": false
        },
        {
            "TimePeriod": {
                "Start": "2026-08-01",
                "End": "2026-09-01"
            },
            "Total": {},
            "Groups": [
                {
                    "Keys": [
                        "APS2-APN1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APN1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.000000004",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APS1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APS1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000441875",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APS3-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APS3-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000103113",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-CAN1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-CAN1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000489827",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-DEL1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-DEL1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000161",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-DataTransfer-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-DataTransfer-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0222705389",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-DataTransfer-Regional-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0381186423",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-ES:GP3-Storage"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "8.7839998416",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-ESInstance:m7g.medium"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "63.24",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-ESInstance:t3.small"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "41.664",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EU-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EU-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000061051",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUC1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUC1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.000096629",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUN1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUN1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.000000016",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUW2-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUW2-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000422067",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUW3-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUW3-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000001898",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-IndexingOCU"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "209.064",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-QRO1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-QRO1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000292",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-SearchOCU"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "209.064",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USE1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USE1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.027014796",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USE2-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USE2-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0011295313",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USW1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USW1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000200698",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USW2-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USW2-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0025317971",
                            "Unit": "USD"
                        }
                    }
                }
            ],
            "Estimated": false
        },
        {
            "TimePeriod": {
                "Start": "2026-09-01",
                "End": "2026-09-21"
            },
            "Total": {},
            "Groups": [
                {
                    "Keys": [
                        "APS2-AFS1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-AFS1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.000000008",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APE1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APE1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000772",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APN1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APN1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000117",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APN2-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APN2-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000161",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APN3-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APN3-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.000000008",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APS1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APS1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000282003",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APS3-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APS3-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000116299",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APS4-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-APS4-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.000000008",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-ATL1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-ATL1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000161",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-BKK1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-BKK1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000161",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-BOS1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-BOS1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000161",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-BUE1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-BUE1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000161",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-CAN1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-CAN1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000341649",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-CCU1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-CCU1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000161",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-CHI1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-CHI1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000161",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-DEL1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-DEL1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000322",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-DEN1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-DEN1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000161",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-DFW1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-DFW1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000483",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-DataTransfer-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-DataTransfer-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0122584599",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-DataTransfer-Regional-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0260161909",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-ES:GP3-Storage"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "5.8193998569",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-ESInstance:m7g.medium"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "40.545",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-ESInstance:t3.small"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "26.712",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EU-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EU-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000008628",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUC1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUC1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000348047",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUN1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUN1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.000000689",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUW2-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUW2-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000328354",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUW3-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-EUW3-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000161",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-HAM1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-HAM1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000161",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-IAH1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-IAH1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000161",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-ILC1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-ILC1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000017512",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-IndexingOCU"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "134.318",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-LAS1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-LAS1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000161",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-LAX1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-LAX1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.000000004",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-LIM1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-LIM1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000161",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-LOS1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-LOS1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000161",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-MCI2-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-MCI2-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000161",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-MIA1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-MIA1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000161",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-MNL1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-MNL1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000161",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-NYC1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-NYC1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000161",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-PDX1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-PDX1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000161",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-PHL1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-PHL1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000161",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-PHX1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-PHX1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000161",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-QRO1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-QRO1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000161",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-SAE1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-SAE1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000009105",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-SCL1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-SCL1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000161",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-SEA1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-SEA1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000161",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-SearchOCU"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "134.318",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-TPE1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-TPE1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000161",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USE1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USE1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0007237674",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USE2-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USE2-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.00064717",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USW1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USW1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000076945",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USW2-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-USW2-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0013012662",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-WAW1-AWS-In-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0",
                            "Unit": "USD"
                        }
                    }
                },
                {
                    "Keys": [
                        "APS2-WAW1-AWS-Out-Bytes"
                    ],
                    "Metrics": {
                        "UnblendedCost": {
                            "Amount": "0.0000000161",
                            "Unit": "USD"
                        }
                    }
                }
            ],
            "Estimated": true
        }
    ],
    "DimensionValueAttributes": []
}
```

## Not captured here

- **Manual snapshot.** Automated snapshots are destroyed with the domain. Take one to a bucket you own before deleting: see the OpenSearch `_snapshot` API.
- **Consumers.** Which clients call the `search` query (toshi-ui, runzi, ad-hoc `scripts/elastic_cli.py` use) is a team question, not an API call.
- **Mapping drift.** Diff the captured `_mapping` against the `mapping()` definition in `scripts/elastic_cli.py:193`.
