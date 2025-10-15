from aws_cdk import (
    Stack,
    aws_appsync as appsync,
    aws_dynamodb as dynamodb,
    RemovalPolicy,
)
from constructs import Construct


class AppsyncStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        # Tag all resources with "team"="foxes"
        self.tags.set_tag("team", "foxes")
        # Create DynamoDB table for widgets
        widgets_table = dynamodb.Table(
            self, "WidgetsTable",
            table_name="widgets",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,  # Use RETAIN for production
        )

        # Create AppSync GraphQL API
        api = appsync.GraphqlApi(
            self, "WidgetApi",
            name="widget-api",
            schema=appsync.SchemaFile.from_asset("schema.graphql"),
            authorization_config=appsync.AuthorizationConfig(
                default_authorization=appsync.AuthorizationMode(
                    authorization_type=appsync.AuthorizationType.API_KEY
                )
            )
        )

        # Create DynamoDB data source
        widgets_data_source = api.add_dynamo_db_data_source(
            "WidgetsDataSource",
            table=widgets_table
        )

        # Create resolvers for queries
        widgets_data_source.create_resolver(
            "GetWidgetResolver",
            type_name="Query",
            field_name="getWidget",
            request_mapping_template=appsync.MappingTemplate.from_string("""
{
    "version": "2017-02-28",
    "operation": "GetItem",
    "key": {
        "id": {"S": "$ctx.args.id"}
    }
}
            """),
            response_mapping_template=appsync.MappingTemplate.dynamo_db_result_item()
        )

        widgets_data_source.create_resolver(
            "ListWidgetsResolver",
            type_name="Query",
            field_name="listWidgets",
            request_mapping_template=appsync.MappingTemplate.dynamo_db_scan_table(),
            response_mapping_template=appsync.MappingTemplate.dynamo_db_result_list()
        )

        # Create resolvers for mutations
        widgets_data_source.create_resolver(
            "CreateWidgetResolver",
            type_name="Mutation",
            field_name="createWidget",
            request_mapping_template=appsync.MappingTemplate.from_string("""
{
    "version": "2017-02-28",
    "operation": "PutItem",
    "key": {
        "id": {"S": "$util.autoId()"}
    },
    "attributeValues": {
        "name": {"S": "$ctx.args.input.name"},
        "price": {"N": "$ctx.args.input.price"}
    }
}
            """),
            response_mapping_template=appsync.MappingTemplate.dynamo_db_result_item()
        )

        widgets_data_source.create_resolver(
            "UpdateWidgetResolver",
            type_name="Mutation",
            field_name="updateWidget",
            request_mapping_template=appsync.MappingTemplate.from_string("""
#set($updateExpression = "")
#set($expressionNames = {})
#set($expressionValues = {})
#set($first = true)

#if($ctx.args.input.name)
    #if($first)
        #set($updateExpression = "SET #name = :name")
        #set($first = false)
    #else
        #set($updateExpression = "$updateExpression, #name = :name")
    #end
    $util.qr($expressionNames.put("#name", "name"))
    $util.qr($expressionValues.put(":name", {"S": "$ctx.args.input.name"}))
#end

#if($ctx.args.input.price)
    #if($first)
        #set($updateExpression = "SET #price = :price")
        #set($first = false)
    #else
        #set($updateExpression = "$updateExpression, #price = :price")
    #end
    $util.qr($expressionNames.put("#price", "price"))
    $util.qr($expressionValues.put(":price", {"N": "$ctx.args.input.price"}))
#end

#if($first)
    $util.error("At least one field must be provided for update")
#end

{
    "version": "2017-02-28",
    "operation": "UpdateItem",
    "key": {
        "id": {"S": "$ctx.args.input.id"}
    },
    "update": {
        "expression": "$updateExpression",
        "expressionNames": $util.toJson($expressionNames),
        "expressionValues": $util.toJson($expressionValues)
    }
}
            """),
            response_mapping_template=appsync.MappingTemplate.dynamo_db_result_item()
        )

        widgets_data_source.create_resolver(
            "DeleteWidgetResolver",
            type_name="Mutation",
            field_name="deleteWidget",
            request_mapping_template=appsync.MappingTemplate.from_string("""
{
    "version": "2017-02-28",
    "operation": "DeleteItem",
    "key": {
        "id": {"S": "$ctx.args.id"}
    }
}
            """),
            response_mapping_template=appsync.MappingTemplate.dynamo_db_result_item()
        )
