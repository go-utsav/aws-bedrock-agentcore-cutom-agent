from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime
from strands import Agent

app = FastAPI(title="Strands Agent Server", version="1.0.0")

# Initialize Strands agent with AWS Bedrock model
# The model parameter should be a string representing the model-id for Bedrock
strands_agent = Agent(
    model="anthropic.claude-3-sonnet-20240229-v1:0",
    system_prompt="You are a helpful AI assistant. Provide clear, accurate, and helpful responses to user queries."
)

class InvocationRequest(BaseModel):
    input: Dict[str, Any]

class InvocationResponse(BaseModel):
    output: Dict[str, Any]

@app.post("/invocations", response_model=InvocationResponse)
async def invoke_agent(request: InvocationRequest):
    try:
        user_message = request.input.get("prompt", "")
        if not user_message:
            raise HTTPException(
                status_code=400, 
                detail="No prompt found in input. Please provide a 'prompt' key in the input."
            )

        result = strands_agent(user_message)
        
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
        
        response = {
            "message": message_text,
            "timestamp": datetime.utcnow().isoformat(),
            "model": "anthropic.claude-3-sonnet-20240229-v1:0",
        }

        return InvocationResponse(output=response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")

@app.get("/ping")
async def ping():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)