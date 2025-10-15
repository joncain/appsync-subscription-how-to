#!/bin/bash

# Deploy the AppSync stack
echo "Deploying AppSync stack..."
cdk deploy

# Get the API details after deployment
echo "Getting API details..."
aws appsync list-graphql-apis --query 'graphqlApis[?name==`widget-api`].[name,apiId,uris.GRAPHQL]' --output table

echo "Deployment complete!"
echo "You can now use the GraphQL endpoint to manage widgets."
