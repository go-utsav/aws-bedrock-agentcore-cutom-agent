/**
 * Frontend Integration Examples for AppBank AI Twins API
 * 
 * Standard Response Format:
 * {
 *   "status": "success" | "error",
 *   "message": "Human readable message",
 *   "data": { /* Response data */ },
 *   "timestamp": "2024-01-01T00:00:00Z"
 * }
 */

class AppBankAITwinsAPI {
    constructor(baseURL = 'http://localhost:8080') {
        this.baseURL = baseURL;
    }

    /**
     * Generic API call handler with standardized response format
     */
    async apiCall(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            const data = await response.json();
            
            // Check if the response follows our standard format
            if (data.status === 'error') {
                throw new Error(data.message);
            }
            
            return data;
        } catch (error) {
            console.error('API Call failed:', error);
            throw error;
        }
    }

    // ==================== HEALTH & STATUS ====================

    /**
     * Check if the API is healthy
     */
    async healthCheck() {
        return await this.apiCall('/ping');
    }

    /**
     * Get list of all available agents
     */
    async getAgents() {
        return await this.apiCall('/agents');
    }

    // ==================== CONVERSATION ENDPOINTS ====================

    /**
     * Start a conversation with a specific agent
     */
    async startConversation(message, agentId, userId = null, conversationId = null) {
        return await this.apiCall('/conversation', {
            method: 'POST',
            body: JSON.stringify({
                message,
                agent_id: agentId,
                user_id: userId,
                conversation_id: conversationId
            })
        });
    }

    /**
     * Use twin system for multi-agent collaboration
     */
    async twinSystemCollaboration(userMessage, targetAgent = null, collaborationMode = 'orchestrator', context = null, userId = null) {
        return await this.apiCall('/twin-system', {
            method: 'POST',
            body: JSON.stringify({
                user_message: userMessage,
                target_agent: targetAgent,
                collaboration_mode: collaborationMode,
                context,
                user_id: userId,
                enable_learning: true
            })
        });
    }

    // ==================== AGENT-SPECIFIC METHODS ====================

    /**
     * Chat with Nayeem (Mobile Developer)
     */
    async chatWithNayeem(message, userId = null) {
        return await this.startConversation(message, 'nayeem_mobile', userId);
    }

    /**
     * Chat with Karti (Database Developer)
     */
    async chatWithKarti(message, userId = null) {
        return await this.startConversation(message, 'karti_database', userId);
    }

    /**
     * Chat with Niyas (AI Developer)
     */
    async chatWithNiyas(message, userId = null) {
        return await this.startConversation(message, 'niyas_ai', userId);
    }

    /**
     * Chat with Utsav (Full Stack & Cloud)
     */
    async chatWithUtsav(message, userId = null) {
        return await this.startConversation(message, 'utsav_fullstack', userId);
    }

    /**
     * Chat with Owner/CEO (Business Strategy)
     */
    async chatWithCEO(message, userId = null) {
        return await this.startConversation(message, 'owner_ceo', userId);
    }

    // ==================== MEMORY & LEARNING ====================

    /**
     * Get agent memory (legacy)
     */
    async getAgentMemory(agentId) {
        return await this.apiCall(`/agent/${agentId}/memory`);
    }

    /**
     * Get enhanced memory for an agent
     */
    async getEnhancedMemory(agentId, userId = null, limit = 50) {
        const params = new URLSearchParams();
        if (userId) params.append('user_id', userId);
        if (limit) params.append('limit', limit);
        
        return await this.apiCall(`/agent/${agentId}/enhanced-memory?${params}`);
    }

    /**
     * Get agent personality data
     */
    async getAgentPersonality(agentId) {
        return await this.apiCall(`/agent/${agentId}/personality`);
    }

    /**
     * Get agent context
     */
    async getAgentContext(agentId, userId = null) {
        const params = userId ? `?user_id=${userId}` : '';
        return await this.apiCall(`/agent/${agentId}/context${params}`);
    }

    /**
     * Trigger learning analysis for an agent
     */
    async triggerLearning(agentId, userId = null) {
        const params = userId ? `?user_id=${userId}` : '';
        return await this.apiCall(`/agent/${agentId}/learn${params}`, {
            method: 'POST'
        });
    }

    // ==================== WEBSOCKET SUPPORT ====================

    /**
     * Create WebSocket connection for real-time messaging
     */
    createWebSocketConnection(userId) {
        const ws = new WebSocket(`ws://localhost:8080/ws/${userId}`);
        
        ws.onopen = () => {
            console.log('WebSocket connected');
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Received message:', data);
            return data;
        };
        
        ws.onclose = () => {
            console.log('WebSocket disconnected');
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        return ws;
    }

    /**
     * Send message via WebSocket
     */
    sendWebSocketMessage(ws, message, agentId = 'team_coordinator', conversationId = null) {
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                message,
                agent_id: agentId,
                conversation_id: conversationId
            }));
        } else {
            console.error('WebSocket is not open');
        }
    }
}

// ==================== USAGE EXAMPLES ====================

// Initialize the API client
const api = new AppBankAITwinsAPI();

// Example 1: Health Check
async function checkHealth() {
    try {
        const response = await api.healthCheck();
        console.log('API Status:', response.status);
        console.log('Message:', response.message);
        console.log('Data:', response.data);
    } catch (error) {
        console.error('Health check failed:', error);
    }
}

// Example 2: Get All Agents
async function loadAgents() {
    try {
        const response = await api.getAgents();
        if (response.status === 'success') {
            console.log('Available agents:', response.data.agents);
            return response.data.agents;
        }
    } catch (error) {
        console.error('Failed to load agents:', error);
    }
}

// Example 3: Chat with Mobile Developer
async function askMobileQuestion(question, userId = 'user123') {
    try {
        const response = await api.chatWithNayeem(question, userId);
        if (response.status === 'success') {
            console.log('Nayeem says:', response.data.message.content[0].text);
            return response.data;
        }
    } catch (error) {
        console.error('Chat failed:', error);
    }
}

// Example 4: Multi-Agent Collaboration
async function startProject(projectDescription, userId = 'pm123') {
    try {
        const response = await api.twinSystemCollaboration(
            projectDescription,
            null, // Let team coordinator decide
            'orchestrator',
            {
                project_type: 'mobile_app',
                timeline: '3_months',
                budget: '$50k'
            },
            userId
        );
        
        if (response.status === 'success') {
            console.log('Team coordination response:', response.data.message.content[0].text);
            return response.data;
        }
    } catch (error) {
        console.error('Project coordination failed:', error);
    }
}

// Example 5: WebSocket Real-time Chat
function setupRealTimeChat(userId) {
    const ws = api.createWebSocketConnection(userId);
    
    // Send a message
    setTimeout(() => {
        api.sendWebSocketMessage(ws, 'Hello team!', 'team_coordinator');
    }, 1000);
    
    return ws;
}

// Example 6: Get Agent Learning Insights
async function analyzeAgentLearning(agentId, userId = null) {
    try {
        const response = await api.triggerLearning(agentId, userId);
        if (response.status === 'success') {
            console.log('Learning insights:', response.data.learning_insights);
            return response.data;
        }
    } catch (error) {
        console.error('Learning analysis failed:', error);
    }
}

// ==================== REACT HOOKS EXAMPLE ====================

// Custom React hook for AI Twins API
function useAITwinsAPI() {
    const [agents, setAgents] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const api = new AppBankAITwinsAPI();

    const loadAgents = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await api.getAgents();
            if (response.status === 'success') {
                setAgents(response.data.agents);
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const sendMessage = async (message, agentId, userId) => {
        setLoading(true);
        setError(null);
        try {
            const response = await api.startConversation(message, agentId, userId);
            if (response.status === 'success') {
                return response.data;
            }
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    };

    return {
        agents,
        loading,
        error,
        loadAgents,
        sendMessage
    };
}

// ==================== EXPORT FOR USE ====================

// For Node.js/CommonJS
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AppBankAITwinsAPI;
}

// For ES6 modules
if (typeof window !== 'undefined') {
    window.AppBankAITwinsAPI = AppBankAITwinsAPI;
}
