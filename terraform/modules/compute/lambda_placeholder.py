# Placeholder Lambda function for ${environment} environment
# This will be replaced with the actual FastAPI application during deployment

import json
import logging
import os

# Configure logging
log_level = os.environ.get('LOG_LEVEL', 'INFO')
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger(__name__)

def handler(event, context):
    """
    Placeholder Lambda handler
    This function serves as a placeholder until the actual FastAPI application is deployed
    """
    logger.info(f"Received event: {json.dumps(event, default=str)}")
    
    # Extract request information
    http_method = event.get('httpMethod', 'UNKNOWN')
    path = event.get('path', '/')
    
    # Health check endpoint
    if path == '/api/v1/health' and http_method == 'GET':
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS'
            },
            'body': json.dumps({
                'status': 'healthy',
                'environment': '${environment}',
                'message': 'AI Assistant CLI API is running',
                'timestamp': context.aws_request_id
            })
        }
    
    # Default response for other endpoints
    return {
        'statusCode': 501,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS'
        },
        'body': json.dumps({
            'error': 'Not Implemented',
            'message': 'This endpoint is not yet implemented. Please deploy the full FastAPI application.',
            'path': path,
            'method': http_method,
            'environment': '${environment}'
        })
    }

# WebSocket handler placeholder
def websocket_handler(event, context):
    """
    Placeholder WebSocket handler
    """
    logger.info(f"WebSocket event: {json.dumps(event, default=str)}")
    
    route_key = event.get('requestContext', {}).get('routeKey', 'UNKNOWN')
    connection_id = event.get('requestContext', {}).get('connectionId', 'UNKNOWN')
    
    if route_key == '$connect':
        logger.info(f"WebSocket connection established: {connection_id}")
        return {'statusCode': 200}
    elif route_key == '$disconnect':
        logger.info(f"WebSocket connection closed: {connection_id}")
        return {'statusCode': 200}
    else:
        logger.info(f"WebSocket message received on route {route_key}")
        return {'statusCode': 200}

# JWT Authorizer placeholder
def jwt_authorizer_handler(event, context):
    """
    Placeholder JWT authorizer
    """
    logger.info(f"JWT Authorizer event: {json.dumps(event, default=str)}")
    
    # For development, allow all requests
    # In production, this should validate JWT tokens from Identity Center
    token = event.get('authorizationToken', '')
    
    if not token:
        raise Exception('Unauthorized')
    
    # Placeholder policy - allows all resources
    policy = {
        'principalId': 'placeholder-user',
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Action': 'execute-api:Invoke',
                    'Effect': 'Allow',
                    'Resource': event['methodArn']
                }
            ]
        },
        'context': {
            'userId': 'placeholder-user',
            'environment': '${environment}'
        }
    }
    
    return policy