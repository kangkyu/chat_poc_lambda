import json
import boto3
import os

def lambda_handler(event, context):
    try:
        # Parse the incoming message
        body = json.loads(event['body'])
        user_message = body['message']
        file_key = body.get('file_key')

        # Initialize Bedrock agent client
        bedrock_agent = boto3.client('bedrock-agent-runtime')

        # Handle file content if provided
        enhanced_message = user_message
        if file_key:
            file_content = get_file_content(file_key)
            enhanced_message = f"File content:\n{file_content}\n\nUser question: {user_message}"

        # Invoke Bedrock Agent
        ai_response = invoke_bedrock_agent(bedrock_agent, enhanced_message)

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'response': ai_response
            })
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_file_content(file_key: str) -> str:
    """Download and read file content from S3"""
    try:
        s3 = boto3.client('s3')
        response = s3.get_object(
            Bucket=os.environ['S3_BUCKET'],
            Key=file_key
        )
        return response['Body'].read().decode('utf-8')
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        return f"Error reading file: {str(e)}"

def invoke_bedrock_agent(bedrock_agent, message: str) -> str:
    """Invoke Bedrock Agent"""
    try:
        agent_id = os.environ['BEDROCK_AGENT_ID']
        agent_alias_id = os.environ.get('BEDROCK_AGENT_ALIAS_ID', 'TSTALIASID')
        session_id = os.environ.get('SESSION_ID', 'default-session')

        response = bedrock_agent.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            inputText=message
        )

        # Parse the streaming response
        event_stream = response['completion']
        full_response = ""

        for event in event_stream:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    full_response += chunk['bytes'].decode('utf-8')

        return full_response.strip()

    except Exception as e:
        print(f"Error invoking Bedrock Agent: {str(e)}")
        raise e
