from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Simple Mock Agent Server", version="1.0.0")

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
    Simple mock agent logic that doesn't require Bedrock
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
        
        # Simple mock response - replace this with actual AI logic later
        if "hello" in user_message.lower():
            response_text = "Hello! I'm a mock AI agent. I'm working perfectly and ready to help you!"
        elif "how are you" in user_message.lower():
            response_text = "I'm doing great! I'm a simple mock agent that's working without any external dependencies."
        else:
            response_text = f"I received your message: '{user_message}'. This is a mock response from a working agent!"
        
        logger.info(f"📝 Mock response: {response_text}")
        
        # Follow EXACT Bedrock AgentCore response format from AWS documentation
        response = {
            "message": {
                "role": "assistant", 
                "content": [{"text": response_text}]
            },
            "timestamp": datetime.utcnow().isoformat(),
            "model": "mock-agent"
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
        "service": "mock-agent",
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
        "message": "Simple Mock Agent Server is running",
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
