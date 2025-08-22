from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime
from strands import Agent
import logging
import os
import boto3 
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Set up logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure AWS credentials for Bedrock access
# This ensures the agent can access AWS Bedrock models
os.environ.setdefault('AWS_DEFAULT_REGION', 'us-east-1')

# Verify AWS credentials are available
try:
    # Test if we can create a Bedrock client
    bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
    logger.info("✅ AWS credentials configured successfully")
except Exception as e:
    logger.warning(f"⚠️ AWS credentials issue: {e}")
    logger.info("💡 Make sure you have AWS credentials configured via:")
    logger.info("   - AWS CLI: aws configure")
    logger.info("   - Environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
    logger.info("   - IAM role (if running on EC2/ECS)")

app = FastAPI(title="Strands Agent Server", version="1.0.0")

# Initialize Strands agent with AWS Bedrock model
# Using Mistral Large since we have access to it
strands_agent = Agent(
    model="anthropic.claude-3-5-sonnet-20240620-v1:0",
    system_prompt="You are a helpful AI assistant. Provide clear, accurate, and helpful responses to user queries."
)

class InvocationRequest(BaseModel):
    input: Dict[str, Any]

class InvocationResponse(BaseModel):
    output: Dict[str, Any]

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests for debugging"""
    logger.info(f"🔍 Incoming request: {request.method} {request.url}")
    logger.info(f"🔍 Headers: {dict(request.headers)}")
    
    # Log request body if it exists
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.body()
            if body:
                logger.info(f"🔍 Request body: {body.decode()}")
        except Exception as e:
            logger.info(f"🔍 Could not read request body: {e}")
    
    response = await call_next(request)
    logger.info(f"🔍 Response status: {response.status_code}")
    return response

@app.post("/invocations", response_model=InvocationResponse)
async def invoke_agent(request: InvocationRequest):
    """
    REQUIRED endpoint for Bedrock AgentCore service contract
    Must handle: {"input": {"prompt": "..."}}
    """
    logger.info(f"🎯 /invocations endpoint called with: {request}")
    return await invoke_agent_logic(request)

@app.post("/", response_model=InvocationResponse)
async def invoke_agent_root(request: InvocationRequest):
    """
    Root endpoint that Bedrock AgentCore might be calling
    """
    logger.info(f"🎯 / (root) endpoint called with: {request}")
    return await invoke_agent_logic(request)

@app.post("/invoke", response_model=InvocationResponse)
async def invoke_agent_alt(request: InvocationRequest):
    """
    Alternative endpoint for Bedrock AgentCore service contract
    """
    logger.info(f"🎯 /invoke endpoint called with: {request}")
    return await invoke_agent_logic(request)

async def invoke_agent_logic(request: InvocationRequest):
    """
    Common logic for all invocation endpoints
    """
    try:
        # Extract prompt from the correct format: {"input": {"prompt": "..."}}
        user_message = request.input.get("prompt", "")
        if not user_message:
            raise HTTPException(
                status_code=400, 
                detail="No prompt found in input. Please provide a 'prompt' key in the input."
            )

        logger.info(f"🤖 Processing message: {user_message}")
        result = strands_agent(user_message)
        logger.info(f"🤖 Strands result: {result}")
        
        # Extract the actual text content from the strands response
        # The response structure is: {'role': 'assistant', 'content': [{'text': 'actual message'}]}
        if isinstance(result.message, dict) and 'content' in result.message:
            # Extract text from content array
            content = result.message['content']
            if content and isinstance(content[0], dict) and 'text' in content[0]:
                message_text = content[0]['text']
            else:
                message_text = str(content)
        else:
            message_text = str(result.message)
        
        logger.info(f"📝 Extracted message: {message_text}")
        
        # Follow EXACT Bedrock AgentCore response format from AWS documentation
        response = {
            "message": {
                "role": "assistant", 
                "content": [{"text": message_text}]
            },
            "timestamp": datetime.utcnow().isoformat(),
            "model": "strands-agent"
        }

        logger.info(f"✅ Returning response: {response}")
        return InvocationResponse(output=response)

    except Exception as e:
        logger.error(f"❌ Error in invoke_agent_logic: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")

@app.get("/ping")
async def ping():
    """
    REQUIRED health check endpoint for Bedrock AgentCore service contract
    """
    logger.info("🏓 /ping endpoint called")
    return {"status": "healthy"}

@app.get("/health")
async def health_check():
    """Health check endpoint for Bedrock AgentCore"""
    logger.info("🏥 /health endpoint called")
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "strands-agent",
        "version": "1.0.0"
    }

@app.get("/healthz")
async def healthz():
    """Alternative health check endpoint (common in containerized apps)"""
    logger.info("🏥 /healthz endpoint called")
    return {"status": "ok"}

@app.get("/info")
async def info():
    """Info endpoint for basic connectivity test"""
    logger.info("🏠 /info endpoint called")
    return {
        "message": "Strands Agent Server is running",
        "endpoints": {
            "health": "/health",
            "healthz": "/healthz",
            "ping": "/ping",
            "invocations": "/invocations (REQUIRED)",
            "invoke": "/invoke",
            "root": "/ (POST)"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)