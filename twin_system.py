from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
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
from agent_learning import MemoryManager, LearningEngine

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure AWS credentials
os.environ.setdefault('AWS_DEFAULT_REGION', 'us-east-1')

app = FastAPI(title="AppBank Twin System", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, OPTIONS, etc.)
    allow_headers=["*"],  # Allows all headers
)

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

# Initialize enhanced memory and learning systems
memory_manager = MemoryManager(use_aws_memory=True)
learning_engine = LearningEngine(memory_manager)

# Legacy memory store for backward compatibility
agent_memories = {agent_id: [] for agent_id in AGENT_REGISTRY.keys()}

class InvocationRequest(BaseModel):
    input: Dict[str, Any]

class StandardResponse(BaseModel):
    status: str  # "success" or "error"
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str = None

class InvocationResponse(BaseModel):
    output: Dict[str, Any]

class TwinSystemRequest(BaseModel):
    user_message: str
    target_agent: Optional[str] = None  # If None, use team coordinator
    collaboration_mode: Optional[str] = "orchestrator"  # "orchestrator" or "direct"
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None  # For learning and personalization
    enable_learning: Optional[bool] = True  # Enable learning from conversation

class ConversationRequest(BaseModel):
    message: str
    agent_id: str
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None

def create_success_response(message: str, data: Optional[Dict[str, Any]] = None) -> StandardResponse:
    """Create a standardized success response"""
    return StandardResponse(
        status="success",
        message=message,
        data=data,
        timestamp=datetime.utcnow().isoformat()
    )

def create_error_response(message: str, data: Optional[Dict[str, Any]] = None) -> StandardResponse:
    """Create a standardized error response"""
    return StandardResponse(
        status="error",
        message=message,
        data=data,
        timestamp=datetime.utcnow().isoformat()
    )

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

@app.post("/twin-system", response_model=StandardResponse)
async def twin_system_invoke(request: TwinSystemRequest):
    """Twin system endpoint for multi-agent collaboration"""
    try:
        result = await handle_twin_system_request(request)
        return create_success_response(
            message=f"Twin system collaboration completed",
            data=result.output
        )
    except Exception as e:
        logger.error(f"❌ Twin system endpoint error: {e}", exc_info=True)
        return create_error_response(
            message=f"Twin system collaboration failed: {str(e)}",
            data={"target_agent": request.target_agent, "collaboration_mode": request.collaboration_mode}
        )

@app.post("/conversation", response_model=StandardResponse)
async def conversation_endpoint(request: ConversationRequest):
    """Enhanced conversation endpoint with learning"""
    try:
        import asyncio
        
        # Add timeout to prevent hanging
        result = await asyncio.wait_for(
            handle_conversation_request(request),
            timeout=45.0  # 45 second timeout
        )
        return create_success_response(
            message=f"Conversation completed with {result.output.get('agent', 'Unknown Agent')}",
            data=result.output
        )
    except asyncio.TimeoutError:
        logger.error(f"❌ Conversation timeout for agent {request.agent_id}")
        return create_error_response(
            message="Conversation timeout - please try again",
            data={"agent_id": request.agent_id, "user_id": request.user_id}
        )
    except Exception as e:
        logger.error(f"❌ Conversation endpoint error: {e}", exc_info=True)
        return create_error_response(
            message=f"Conversation failed: {str(e)}",
            data={"agent_id": request.agent_id, "user_id": request.user_id}
        )

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket for real-time messaging"""
    await websocket.accept()
    logger.info(f"🔌 WebSocket connected for user: {user_id}")
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process message through twin system
            response = await handle_conversation_request(ConversationRequest(
                message=message_data.get("message", ""),
                agent_id=message_data.get("agent_id", "team_coordinator"),
                user_id=user_id,
                conversation_id=message_data.get("conversation_id")
            ))
            
            # Send response back
            await websocket.send_text(json.dumps(response.output))
            
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected for user: {user_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        await websocket.close()

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

async def handle_conversation_request(request: ConversationRequest):
    """Handle enhanced conversation with learning capabilities"""
    try:
        agent_id = request.agent_id
        user_message = request.message
        user_id = request.user_id
        
        if agent_id not in agents:
            raise HTTPException(status_code=400, detail=f"Agent {agent_id} not found")
        
        agent = agents[agent_id]
        agent_config = AGENT_REGISTRY[agent_id]
        
        # Get enhanced system prompt with learning
        base_prompt = agent_config["system_prompt"]
        enhanced_prompt = learning_engine.get_enhanced_system_prompt(
            agent_id=agent_id,
            base_prompt=base_prompt,
            user_id=user_id
        )
        
        # Create temporary agent with enhanced prompt
        enhanced_agent = Agent(
            model="anthropic.claude-3-5-sonnet-20240620-v1:0",
            system_prompt=enhanced_prompt
        )
        
        logger.info(f"🤖 Enhanced conversation with {agent_config['name']}: {user_message}")
        
        # Get agent response
        result = enhanced_agent(user_message)
        message_text = extract_response_text(result)
        
        # Learn from the conversation if enabled
        if request.user_id:  # Only learn if we have a user_id
            learning_engine.learn_from_conversation(
                agent_id=agent_id,
                user_message=user_message,
                agent_response=message_text,
                user_id=user_id,
                conversation_context={
                    "conversation_id": request.conversation_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Store in both new and legacy memory systems
        store_in_memory(agent_id, user_message, message_text)
        
        response = {
            "message": {
                "role": "assistant",
                "content": [{"text": message_text}]
            },
            "timestamp": datetime.utcnow().isoformat(),
            "model": f"twin-system-{agent_id}",
            "agent": agent_config['name'],
            "role": agent_config['role'],
            "conversation_id": request.conversation_id or str(uuid.uuid4()),
            "learning_enabled": bool(request.user_id)
        }
        
        return InvocationResponse(output=response)
        
    except Exception as e:
        logger.error(f"❌ Error in conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Conversation failed: {str(e)}")

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

@app.get("/ping", response_model=StandardResponse)
async def ping():
    """Health check endpoint"""
    return create_success_response(
        message="AppBank AI Twins API is healthy and running",
        data={"service": "AppBank AI Twins", "version": "1.0.0"}
    )

@app.get("/agents", response_model=StandardResponse)
async def list_agents():
    """List all available agents"""
    agents_data = [
        {
            "id": agent_id,
            "name": config["name"],
            "role": config["role"],
            "expertise": config["expertise"],
            "memory_entries": len(agent_memories[agent_id])
        }
        for agent_id, config in AGENT_REGISTRY.items()
    ]
    
    return create_success_response(
        message=f"Retrieved {len(agents_data)} available agents",
        data={"agents": agents_data, "total_count": len(agents_data)}
    )

@app.get("/agent/{agent_id}/memory", response_model=StandardResponse)
async def get_agent_memory(agent_id: str):
    """Get memory for a specific agent"""
    if agent_id not in agent_memories:
        return create_error_response(
            message=f"Agent '{agent_id}' not found",
            data={"agent_id": agent_id}
        )
    
    memory_data = {
        "agent_id": agent_id,
        "agent_name": AGENT_REGISTRY[agent_id]["name"],
        "memory_entries": len(agent_memories[agent_id]),
        "recent_memory": agent_memories[agent_id][-10:] if agent_memories[agent_id] else []
    }
    
    return create_success_response(
        message=f"Retrieved memory for agent '{AGENT_REGISTRY[agent_id]['name']}'",
        data=memory_data
    )

@app.get("/agent/{agent_id}/enhanced-memory", response_model=StandardResponse)
async def get_enhanced_memory(agent_id: str, user_id: Optional[str] = None, limit: int = 50):
    """Get enhanced memory for a specific agent"""
    if agent_id not in AGENT_REGISTRY:
        return create_error_response(
            message=f"Agent '{agent_id}' not found",
            data={"agent_id": agent_id}
        )
    
    memories = memory_manager.retrieve_memories(
        agent_id=agent_id,
        user_id=user_id,
        limit=limit
    )
    
    memory_data = {
        "agent_id": agent_id,
        "agent_name": AGENT_REGISTRY[agent_id]["name"],
        "memory_entries": len(memories),
        "memories": [
            {
                "id": memory.id,
                "content": memory.content,
                "type": memory.memory_type,
                "importance": memory.importance,
                "timestamp": memory.timestamp.isoformat(),
                "tags": memory.tags
            }
            for memory in memories
        ]
    }
    
    return create_success_response(
        message=f"Retrieved enhanced memory for agent '{AGENT_REGISTRY[agent_id]['name']}'",
        data=memory_data
    )

@app.get("/agent/{agent_id}/personality", response_model=StandardResponse)
async def get_agent_personality(agent_id: str):
    """Get agent's learned personality"""
    if agent_id not in AGENT_REGISTRY:
        return create_error_response(
            message=f"Agent '{agent_id}' not found",
            data={"agent_id": agent_id}
        )
    
    personality = learning_engine._get_agent_personality(agent_id)
    
    if not personality:
        personality_data = {
            "agent_id": agent_id,
            "agent_name": AGENT_REGISTRY[agent_id]["name"],
            "personality": "No personality data available yet"
        }
        return create_success_response(
            message=f"No personality data available for agent '{AGENT_REGISTRY[agent_id]['name']}'",
            data=personality_data
        )
    
    personality_data = {
        "agent_id": agent_id,
        "agent_name": AGENT_REGISTRY[agent_id]["name"],
        "personality": {
            "communication_style": personality.communication_style,
            "technical_preferences": personality.technical_preferences,
            "learned_phrases": personality.learned_phrases[-10:],  # Last 10 phrases
            "expertise_areas": personality.expertise_areas,
            "last_updated": personality.last_updated.isoformat()
        }
    }
    
    return create_success_response(
        message=f"Retrieved personality data for agent '{AGENT_REGISTRY[agent_id]['name']}'",
        data=personality_data
    )

@app.get("/agent/{agent_id}/context", response_model=StandardResponse)
async def get_agent_context(agent_id: str, user_id: Optional[str] = None):
    """Get context window for agent"""
    if agent_id not in AGENT_REGISTRY:
        return create_error_response(
            message=f"Agent '{agent_id}' not found",
            data={"agent_id": agent_id}
        )
    
    context_window = memory_manager.get_context_window(agent_id, user_id)
    
    context_data = {
        "agent_id": agent_id,
        "agent_name": AGENT_REGISTRY[agent_id]["name"],
        "context": {
            "recent_conversations": len(context_window.recent_conversations),
            "relevant_knowledge": len(context_window.relevant_knowledge),
            "user_preferences": context_window.user_preferences,
            "current_topic": context_window.current_topic
        }
    }
    
    return create_success_response(
        message=f"Retrieved context for agent '{AGENT_REGISTRY[agent_id]['name']}'",
        data=context_data
    )

@app.post("/agent/{agent_id}/learn", response_model=StandardResponse)
async def trigger_learning(agent_id: str, user_id: Optional[str] = None):
    """Trigger learning analysis for an agent"""
    if agent_id not in AGENT_REGISTRY:
        return create_error_response(
            message=f"Agent '{agent_id}' not found",
            data={"agent_id": agent_id}
        )
    
    # Get recent conversations for learning
    conversations = memory_manager.retrieve_memories(
        agent_id=agent_id,
        memory_type='conversation',
        user_id=user_id,
        limit=100
    )
    
    if not conversations:
        return create_success_response(
            message="No conversations found for learning analysis",
            data={"agent_id": agent_id, "conversations_analyzed": 0}
        )
    
    # Extract conversation texts
    conversation_texts = [conv.content for conv in conversations]
    
    # Analyze style patterns
    insights = learning_engine.style_analyzer.extract_learning_insights(conversation_texts)
    
    # Store learning insights
    memory_manager.store_memory(
        agent_id=agent_id,
        content=json.dumps(insights),
        memory_type='learning_insights',
        user_id=user_id,
        importance=0.9
    )
    
    learning_data = {
        "agent_id": agent_id,
        "agent_name": AGENT_REGISTRY[agent_id]["name"],
        "learning_insights": insights,
        "conversations_analyzed": len(conversations)
    }
    
    return create_success_response(
        message=f"Learning analysis completed for agent '{AGENT_REGISTRY[agent_id]['name']}'",
        data=learning_data
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
