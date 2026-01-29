# 🚀 Frontend Integration Guide for AppBank AI Twins API

## 📋 **Step-by-Step Integration Plan**

### **Phase 1: Foundation Setup ✅ (COMPLETED)**
- [x] **Ping API** - System health check
- [x] **List Agents** - Get available AI agents

### **Phase 2: Core Chat Implementation (NEXT)**
- [ ] **Agent Selection UI** - Create agent picker component
- [ ] **Basic Conversation** - Implement chat with individual agents
- [ ] **Message History** - Store and display conversation history

### **Phase 3: Advanced Features**
- [ ] **Multi-Agent Collaboration** - Twin system orchestration
- [ ] **Real-time Messaging** - WebSocket integration
- [ ] **Learning Features** - Agent personality and memory

### **Phase 4: Production Features**
- [ ] **User Management** - User authentication and profiles
- [ ] **Advanced Memory** - Enhanced memory and context
- [ ] **Analytics Dashboard** - Learning insights and metrics

---

## 🎯 **Phase 2: Core Chat Implementation (CURRENT FOCUS)**

### **Step 1: Create Agent Selection Component**

```jsx
// components/AgentSelector.jsx
import React, { useState, useEffect } from 'react';

const AgentSelector = ({ onAgentSelect, selectedAgent }) => {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async () => {
    try {
      const response = await fetch('http://localhost:8080/agents');
      const data = await response.json();
      
      if (data.status === 'success') {
        setAgents(data.data.agents);
      }
    } catch (error) {
      console.error('Failed to fetch agents:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="agent-selector">
      <h3>Choose Your AI Agent</h3>
      {loading ? (
        <p>Loading agents...</p>
      ) : (
        <div className="agent-grid">
          {agents.map(agent => (
            <div 
              key={agent.id}
              className={`agent-card ${selectedAgent?.id === agent.id ? 'selected' : ''}`}
              onClick={() => onAgentSelect(agent)}
            >
              <h4>{agent.name}</h4>
              <p>{agent.role}</p>
              <div className="expertise">
                {agent.expertise.map(skill => (
                  <span key={skill} className="skill-tag">{skill}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AgentSelector;
```

### **Step 2: Create Chat Interface Component**

```jsx
// components/ChatInterface.jsx
import React, { useState, useRef, useEffect } from 'react';

const ChatInterface = ({ selectedAgent, userId }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!inputMessage.trim() || !selectedAgent) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8080/conversation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputMessage,
          agent_id: selectedAgent.id,
          user_id: userId || 'anonymous',
          conversation_id: `conv_${Date.now()}`
        })
      });

      const data = await response.json();

      if (data.status === 'success') {
        const agentMessage = {
          id: Date.now() + 1,
          type: 'agent',
          content: data.data.message.content[0].text,
          agent: data.data.agent,
          timestamp: data.data.timestamp
        };
        setMessages(prev => [...prev, agentMessage]);
      } else {
        throw new Error(data.message);
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: `Error: ${error.message}`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h3>Chat with {selectedAgent?.name}</h3>
        <p>{selectedAgent?.role}</p>
      </div>
      
      <div className="messages-container">
        {messages.map(message => (
          <div key={message.id} className={`message ${message.type}`}>
            <div className="message-content">
              {message.type === 'user' && <strong>You:</strong>}
              {message.type === 'agent' && <strong>{message.agent}:</strong>}
              {message.type === 'error' && <strong>Error:</strong>}
              <p>{message.content}</p>
            </div>
            <div className="message-timestamp">
              {new Date(message.timestamp).toLocaleTimeString()}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message agent">
            <div className="message-content">
              <strong>{selectedAgent?.name}:</strong>
              <p>Thinking...</p>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-container">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={`Ask ${selectedAgent?.name} anything...`}
          disabled={isLoading}
        />
        <button onClick={sendMessage} disabled={isLoading || !inputMessage.trim()}>
          Send
        </button>
      </div>
    </div>
  );
};

export default ChatInterface;
```

### **Step 3: Create Main App Component**

```jsx
// App.jsx
import React, { useState } from 'react';
import AgentSelector from './components/AgentSelector';
import ChatInterface from './components/ChatInterface';
import './App.css';

function App() {
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [userId] = useState(`user_${Date.now()}`); // Generate unique user ID

  return (
    <div className="app">
      <header className="app-header">
        <h1>AppBank AI Twins</h1>
        <p>Chat with your AI team members</p>
      </header>

      <main className="app-main">
        {!selectedAgent ? (
          <AgentSelector onAgentSelect={setSelectedAgent} />
        ) : (
          <div className="chat-container">
            <div className="agent-info">
              <h2>Chatting with {selectedAgent.name}</h2>
              <button 
                className="change-agent-btn"
                onClick={() => setSelectedAgent(null)}
              >
                Change Agent
              </button>
            </div>
            <ChatInterface 
              selectedAgent={selectedAgent} 
              userId={userId}
            />
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
```

### **Step 4: Add Basic Styling**

```css
/* App.css */
.app {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: Arial, sans-serif;
}

.app-header {
  text-align: center;
  margin-bottom: 30px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 10px;
}

.agent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.agent-card {
  padding: 20px;
  border: 2px solid #e0e0e0;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: white;
}

.agent-card:hover {
  border-color: #667eea;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.agent-card.selected {
  border-color: #667eea;
  background: #f0f4ff;
}

.agent-card h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.agent-card p {
  margin: 0 0 15px 0;
  color: #666;
  font-style: italic;
}

.skill-tag {
  display: inline-block;
  background: #e3f2fd;
  color: #1976d2;
  padding: 4px 8px;
  margin: 2px;
  border-radius: 12px;
  font-size: 12px;
}

.chat-interface {
  display: flex;
  flex-direction: column;
  height: 600px;
  border: 1px solid #e0e0e0;
  border-radius: 10px;
  overflow: hidden;
}

.chat-header {
  background: #f5f5f5;
  padding: 15px 20px;
  border-bottom: 1px solid #e0e0e0;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #fafafa;
}

.message {
  margin-bottom: 15px;
  padding: 10px 15px;
  border-radius: 10px;
  max-width: 80%;
}

.message.user {
  background: #667eea;
  color: white;
  margin-left: auto;
}

.message.agent {
  background: white;
  border: 1px solid #e0e0e0;
}

.message.error {
  background: #ffebee;
  border: 1px solid #f44336;
  color: #d32f2f;
}

.message-content strong {
  display: block;
  margin-bottom: 5px;
}

.message-timestamp {
  font-size: 12px;
  color: #666;
  margin-top: 5px;
}

.input-container {
  display: flex;
  padding: 15px 20px;
  background: white;
  border-top: 1px solid #e0e0e0;
}

.input-container input {
  flex: 1;
  padding: 10px 15px;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  outline: none;
  margin-right: 10px;
}

.input-container button {
  padding: 10px 20px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  transition: background 0.3s ease;
}

.input-container button:hover:not(:disabled) {
  background: #5a6fd8;
}

.input-container button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.agent-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f5f5;
  border-radius: 10px;
}

.change-agent-btn {
  padding: 8px 16px;
  background: #ff6b6b;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}
```

---

## 🎯 **Phase 3: Advanced Features (NEXT STEPS)**

### **Step 5: Multi-Agent Collaboration**

```jsx
// components/TwinSystemChat.jsx
const TwinSystemChat = ({ userId }) => {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const sendToTwinSystem = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8080/twin-system', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_message: message,
          target_agent: null, // Let team coordinator decide
          collaboration_mode: 'orchestrator',
          context: {
            project_type: 'general_inquiry',
            user_id: userId
          },
          user_id: userId,
          enable_learning: true
        })
      });

      const data = await response.json();
      if (data.status === 'success') {
        setResponse(data.data);
      }
    } catch (error) {
      console.error('Twin system error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="twin-system-chat">
      <h3>Multi-Agent Collaboration</h3>
      <p>Ask a complex question and let the team coordinate the response</p>
      
      <div className="input-group">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Describe your project or ask a complex question..."
          rows={4}
        />
        <button onClick={sendToTwinSystem} disabled={isLoading}>
          {isLoading ? 'Coordinating...' : 'Ask Team'}
        </button>
      </div>

      {response && (
        <div className="team-response">
          <h4>Team Response:</h4>
          <p>{response.message.content[0].text}</p>
          <div className="response-meta">
            <span>Agent: {response.agent}</span>
            <span>Mode: {response.collaboration_mode}</span>
          </div>
        </div>
      )}
    </div>
  );
};
```

### **Step 6: WebSocket Real-time Chat**

```jsx
// hooks/useWebSocket.js
import { useState, useEffect, useRef } from 'react';

export const useWebSocket = (userId) => {
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8080/ws/${userId}`);
    
    ws.onopen = () => {
      setIsConnected(true);
      setSocket(ws);
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages(prev => [...prev, data]);
    };
    
    ws.onclose = () => {
      setIsConnected(false);
      setSocket(null);
    };
    
    return () => ws.close();
  }, [userId]);

  const sendMessage = (message, agentId = 'team_coordinator') => {
    if (socket && isConnected) {
      socket.send(JSON.stringify({
        message,
        agent_id: agentId
      }));
    }
  };

  return { socket, isConnected, messages, sendMessage };
};
```

---

## 🎯 **Phase 4: Production Features**

### **Step 7: Agent Memory & Learning**

```jsx
// components/AgentMemory.jsx
const AgentMemory = ({ agentId }) => {
  const [memory, setMemory] = useState(null);
  const [personality, setPersonality] = useState(null);

  useEffect(() => {
    fetchAgentData();
  }, [agentId]);

  const fetchAgentData = async () => {
    try {
      // Fetch enhanced memory
      const memoryResponse = await fetch(`http://localhost:8080/agent/${agentId}/enhanced-memory`);
      const memoryData = await memoryResponse.json();
      if (memoryData.status === 'success') {
        setMemory(memoryData.data);
      }

      // Fetch personality
      const personalityResponse = await fetch(`http://localhost:8080/agent/${agentId}/personality`);
      const personalityData = await personalityResponse.json();
      if (personalityData.status === 'success') {
        setPersonality(personalityData.data);
      }
    } catch (error) {
      console.error('Failed to fetch agent data:', error);
    }
  };

  return (
    <div className="agent-memory">
      <h3>Agent Memory & Learning</h3>
      
      {memory && (
        <div className="memory-section">
          <h4>Memory Entries: {memory.memory_entries}</h4>
          <div className="memory-list">
            {memory.memories.slice(0, 5).map(mem => (
              <div key={mem.id} className="memory-item">
                <p>{mem.content.substring(0, 100)}...</p>
                <span className="memory-type">{mem.type}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {personality && personality.personality !== "No personality data available yet" && (
        <div className="personality-section">
          <h4>Learned Personality</h4>
          <div className="personality-data">
            <p><strong>Communication Style:</strong> {JSON.stringify(personality.personality.communication_style)}</p>
            <p><strong>Technical Preferences:</strong> {JSON.stringify(personality.personality.technical_preferences)}</p>
            <p><strong>Learned Phrases:</strong> {personality.personality.learned_phrases.join(', ')}</p>
          </div>
        </div>
      )}
    </div>
  );
};
```

---

## 📝 **Implementation Checklist**

### **Phase 2 (Current Focus)**
- [ ] Create `AgentSelector` component
- [ ] Create `ChatInterface` component  
- [ ] Create main `App` component
- [ ] Add basic CSS styling
- [ ] Test individual agent conversations
- [ ] Add message history persistence

### **Phase 3 (Next)**
- [ ] Implement `TwinSystemChat` component
- [ ] Add WebSocket support with `useWebSocket` hook
- [ ] Create real-time messaging interface
- [ ] Add agent switching during conversation

### **Phase 4 (Advanced)**
- [ ] Implement `AgentMemory` component
- [ ] Add learning insights dashboard
- [ ] Create user profile management
- [ ] Add conversation analytics

---

## 🚀 **Quick Start Commands**

```bash
# 1. Start the backend server
cd my-custom-agent
source venv/bin/activate
python twin_system.py

# 2. Test the API
curl http://localhost:8080/ping
curl http://localhost:8080/agents

# 3. Test a conversation
curl -X POST http://localhost:8080/conversation \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "agent_id": "nayeem_mobile", "user_id": "test123"}'
```

---

## 🎯 **Next Immediate Steps for Your Frontend AI Agent**

1. **Start with Phase 2** - Create the basic chat interface
2. **Test each component** individually before integrating
3. **Use the provided code examples** as starting points
4. **Test with the Postman collection** to understand API responses
5. **Implement error handling** for all API calls
6. **Add loading states** for better UX

The standardized response format makes frontend integration much easier - every API call returns the same structure with `status`, `message`, `data`, and `timestamp` fields!
