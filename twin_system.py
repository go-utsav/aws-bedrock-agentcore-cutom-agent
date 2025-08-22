from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
from strands import Agent
import logging
import os
import boto3
from dotenv import load_dotenv
import json
import uuid

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure AWS credentials
os.environ.setdefault('AWS_DEFAULT_REGION', 'us-east-1')

app = FastAPI(title="AppBank Twin System", version="1.0.0")

# Agent Registry
AGENT_REGISTRY = {
    "nayeem_mobile": {
        "name": "Nayeem",
        "role": "Mobile App Developer",
        "expertise": ["iOS", "Android", "React Native", "App Store"],
        "system_prompt": "You are Nayeem, a mobile app developer at AppBank. You specialize in iOS, Android, and React Native development. You have deep knowledge of mobile app architecture, performance optimization, and app store guidelines. Always provide practical, code-focused solutions."
    },
    "karti_database": {
        "name": "Karti", 
        "role": "Database Developer",
        "expertise": ["PostgreSQL", "MongoDB", "Redis", "Data Modeling"],
        "system_prompt": "You are Karti, a database developer at AppBank. You specialize in database design, optimization, and data modeling. You have expertise in PostgreSQL, MongoDB, Redis, and data architecture. Always provide database-focused solutions with performance considerations."
    },
    "niyas_ai": {
        "name": "Niyas",
        "role": "AI Developer", 
        "expertise": ["Machine Learning", "NLP", "Computer Vision", "MLOps"],
        "system_prompt": "You are Niyas, an AI developer at AppBank. You specialize in machine learning, NLP, computer vision, and MLOps. You have deep knowledge of AI model development, deployment, and optimization. Always provide AI-focused solutions with best practices."
    },
    "utsav_fullstack": {
        "name": "Utsav",
        "role": "Full Stack & Cloud Ops",
        "expertise": ["AWS", "DevOps", "Backend", "Infrastructure"],
        "system_prompt": "You are Utsav, a full stack developer and cloud operations specialist at AppBank. You specialize in AWS, DevOps, backend development, and infrastructure management. Always provide cloud-focused solutions with scalability and security in mind."
    },
    "owner_ceo": {
        "name": "Owner/CEO",
        "role": "Business Decision Maker",
        "expertise": ["Strategy", "Product", "Business", "Leadership"],
        "system_prompt": "You are the Owner/CEO of AppBank. You make strategic business decisions and provide leadership guidance. You focus on business strategy, product direction, and company growth. Always provide business-focused insights and strategic recommendations."
    },
    "team_coordinator": {
        "name": "Team Coordinator",
        "role": "Orchestrator",
        "expertise": ["Task Routing", "Collaboration", "Project Management"],
        "system_prompt": "You are the Team Coordinator at AppBank. You route tasks to the appropriate specialists and coordinate collaboration between team members. You understand each team member's expertise and can orchestrate complex multi-agent workflows."
    }
}

# Initialize agents with their own memories
agents = {}
for agent_id, config in AGENT_REGISTRY.items():
    try:
        agents[agent_id] = Agent(
            model="anthropic.claude-3-5-sonnet-20240620-v1:0",
            system_prompt=config["system_prompt"]
        )
        logger.info(f"✅ Initialized agent: {config['name']} ({agent_id})")
    except Exception as e:
        logger.error(f"❌ Failed to initialize agent {agent_id}: {e}")

# Memory store for each agent (in production, use AWS Bedrock Memory)
agent_memories = {agent_id: [] for agent_id in AGENT_REGISTRY.keys()}

class InvocationRequest(BaseModel):
    input: Dict[str, Any]

class InvocationResponse(BaseModel):
    output: Dict[str, Any]

class TwinSystemRequest(BaseModel):
    user_message: str
    target_agent: Optional[str] = None  # If None, use team coordinator
    collaboration_mode: Optional[str] = "orchestrator"  # "orchestrator" or "direct"
    context: Optional[Dict[str, Any]] = None

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests for debugging"""
    logger.info(f"🔍 Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"🔍 Response status: {response.status_code}")
    return response

@app.post("/invocations", response_model=InvocationResponse)
async def invoke_agent(request: InvocationRequest):
    """Main endpoint for Bedrock AgentCore compatibility"""
    return await invoke_agent_logic(request)

@app.post("/twin-system", response_model=InvocationResponse)
async def twin_system_invoke(request: TwinSystemRequest):
    """Twin system endpoint for multi-agent collaboration"""
    return await handle_twin_system_request(request)

async def invoke_agent_logic(request: InvocationRequest):
    """Handle standard agent invocations"""
    try:
        user_message = request.input.get("prompt", "")
        if not user_message:
            raise HTTPException(status_code=400, detail="No prompt found in input")
        
        # Default to team coordinator for general requests
        agent_id = "team_coordinator"
        agent = agents.get(agent_id)
        
        if not agent:
            raise HTTPException(status_code=500, detail=f"Agent {agent_id} not available")
        
        logger.info(f"🤖 {AGENT_REGISTRY[agent_id]['name']} processing: {user_message}")
        result = agent(user_message)
        
        # Extract response text
        message_text = extract_response_text(result)
        
        # Store in agent memory
        store_in_memory(agent_id, user_message, message_text)
        
        response = {
            "message": {
                "role": "assistant",
                "content": [{"text": message_text}]
            },
            "timestamp": datetime.utcnow().isoformat(),
            "model": f"twin-system-{agent_id}"
        }
        
        return InvocationResponse(output=response)
        
    except Exception as e:
        logger.error(f"❌ Error in invoke_agent_logic: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")

async def handle_twin_system_request(request: TwinSystemRequest):
    """Handle twin system requests with multi-agent collaboration"""
    try:
        user_message = request.user_message
        target_agent = request.target_agent
        collaboration_mode = request.collaboration_mode
        
        logger.info(f"🤖 Twin System Request: {user_message}")
        logger.info(f"🎯 Target Agent: {target_agent or 'Team Coordinator'}")
        logger.info(f"🔗 Collaboration Mode: {collaboration_mode}")
        
        if collaboration_mode == "direct" and target_agent:
            # Direct agent-to-agent communication
            response = await direct_agent_communication(target_agent, user_message, request.context)
        else:
            # Use team coordinator for orchestration
            response = await orchestrated_collaboration(user_message, request.context)
        
        return InvocationResponse(output=response)
        
    except Exception as e:
        logger.error(f"❌ Error in twin system: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Twin system failed: {str(e)}")

async def direct_agent_communication(agent_id: str, message: str, context: Optional[Dict] = None):
    """Direct communication with a specific agent"""
    if agent_id not in agents:
        raise HTTPException(status_code=400, detail=f"Agent {agent_id} not found")
    
    agent = agents[agent_id]
    agent_config = AGENT_REGISTRY[agent_id]
    
    # Add context to the message if provided
    if context:
        enhanced_message = f"{message}\n\nContext: {json.dumps(context, indent=2)}"
    else:
        enhanced_message = message
    
    logger.info(f"🤖 Direct communication with {agent_config['name']}: {enhanced_message}")
    
    try:
        result = agent(enhanced_message)
        message_text = extract_response_text(result)
        
        # Store in agent memory
        store_in_memory(agent_id, enhanced_message, message_text)
        
        response = {
            "message": {
                "role": "assistant",
                "content": [{"text": message_text}]
            },
            "timestamp": datetime.utcnow().isoformat(),
            "model": f"twin-system-{agent_id}",
            "agent": agent_config['name'],
            "role": agent_config['role']
        }
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Direct communication failed: {e}")
        raise HTTPException(status_code=500, detail=f"Direct communication failed: {str(e)}")

async def orchestrated_collaboration(message: str, context: Optional[Dict] = None):
    """Use team coordinator to orchestrate multi-agent collaboration"""
    coordinator = agents.get("team_coordinator")
    if not coordinator:
        raise HTTPException(status_code=500, detail="Team coordinator not available")
    
    # Create orchestration prompt
    orchestration_prompt = f"""
    As the Team Coordinator at AppBank, analyze this request and determine the best approach:
    
    User Request: {message}
    
    Available Team Members:
    - Nayeem (Mobile App Developer): iOS, Android, React Native
    - Karti (Database Developer): PostgreSQL, MongoDB, Redis, Data Modeling
    - Niyas (AI Developer): Machine Learning, NLP, Computer Vision, MLOps
    - Utsav (Full Stack & Cloud Ops): AWS, DevOps, Backend, Infrastructure
    - Owner/CEO: Business Strategy, Product Direction, Leadership
    
    Context: {context or 'No additional context provided'}
    
    Please:
    1. Analyze the request
    2. Identify which team member(s) should handle this
    3. Provide a coordinated response
    4. Suggest next steps if multiple agents need to collaborate
    
    Respond as the Team Coordinator coordinating the team.
    """
    
    try:
        result = coordinator(orchestration_prompt)
        message_text = extract_response_text(result)
        
        # Store in coordinator memory
        store_in_memory("team_coordinator", orchestration_prompt, message_text)
        
        response = {
            "message": {
                "role": "assistant",
                "content": [{"text": message_text}]
            },
            "timestamp": datetime.utcnow().isoformat(),
            "model": "twin-system-coordinator",
            "agent": "Team Coordinator",
            "role": "Orchestrator",
            "collaboration_mode": "orchestrated"
        }
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Orchestration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Orchestration failed: {str(e)}")

def extract_response_text(result):
    """Extract text from strands response"""
    if isinstance(result.message, dict) and 'content' in result.message:
        content = result.message['content']
        if content and isinstance(content[0], dict) and 'text' in content[0]:
            return content[0]['text']
        else:
            return str(content)
    else:
        return str(result.message)

def store_in_memory(agent_id: str, input_message: str, response_message: str):
    """Store conversation in agent memory"""
    memory_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "input": input_message,
        "response": response_message,
        "session_id": str(uuid.uuid4())
    }
    
    agent_memories[agent_id].append(memory_entry)
    
    # Keep only last 100 entries per agent (in production, use AWS Bedrock Memory)
    if len(agent_memories[agent_id]) > 100:
        agent_memories[agent_id] = agent_memories[agent_id][-100:]
    
    logger.info(f"💾 Stored in {agent_id} memory: {len(agent_memories[agent_id])} entries")

@app.get("/ping")
async def ping():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/agents")
async def list_agents():
    """List all available agents"""
    return {
        "agents": [
            {
                "id": agent_id,
                "name": config["name"],
                "role": config["role"],
                "expertise": config["expertise"],
                "memory_entries": len(agent_memories[agent_id])
            }
            for agent_id, config in AGENT_REGISTRY.items()
        ]
    }

@app.get("/agent/{agent_id}/memory")
async def get_agent_memory(agent_id: str):
    """Get memory for a specific agent"""
    if agent_id not in agent_memories:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "agent_id": agent_id,
        "agent_name": AGENT_REGISTRY[agent_id]["name"],
        "memory_entries": len(agent_memories[agent_id]),
        "recent_memory": agent_memories[agent_id][-10:] if agent_memories[agent_id] else []
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
