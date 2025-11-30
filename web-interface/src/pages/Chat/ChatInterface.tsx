import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Avatar,
  Chip,
  Fab,
  Tooltip,
  Card,
  CardContent,
  Grid,
  CircularProgress,
} from '@mui/material';
import {
  Send as SendIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
  Clear as ClearIcon,
  Mic as MicIcon,
  AttachFile as AttachIcon,
} from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../../store/store';
import {
  addMessage,
  setTyping,
  clearMessages,
  ChatMessage,
} from '../../store/slices/chatSlice';
import ReactMarkdown from 'react-markdown';

const ChatInterface: React.FC = () => {
  const dispatch = useDispatch();
  const { messages, isTyping, connectionStatus } = useSelector(
    (state: RootState) => state.chat
  );
  const [inputMessage, setInputMessage] = useState('');
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const agents = [
    { id: 'auto', name: 'Auto-Select', color: '#667eea', icon: '🤖' },
    { id: 'athena', name: 'Athena (PM)', color: '#4caf50', icon: '📋' },
    { id: 'hephaestus', name: 'Hephaestus (Cloud)', color: '#ff9800', icon: '☁️' },
    { id: 'apollo', name: 'Apollo (Consultant)', color: '#9c27b0', icon: '💼' },
    { id: 'hermes', name: 'Hermes (Sales)', color: '#2196f3', icon: '💰' },
    { id: 'vulcan', name: 'Vulcan (DevOps)', color: '#f44336', icon: '⚙️' },
    { id: 'ares', name: 'Ares (Security)', color: '#795548', icon: '🛡️' },
  ];

  const quickActions = [
    'Tạo Jira ticket mới',
    'Deploy ứng dụng lên OpenShift',
    'Phân tích kiến trúc hệ thống',
    'Tối ưu chi phí cloud',
    'Kiểm tra bảo mật',
    'Tư vấn chiến lược',
  ];

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    // Add user message
    const userMessage: Omit<ChatMessage, 'id' | 'timestamp'> = {
      type: 'user',
      content: inputMessage,
      status: 'sent',
    };

    dispatch(addMessage(userMessage));
    setInputMessage('');
    dispatch(setTyping(true));

    try {
      // Call Zeus Master Agent API
      const response = await fetch('/api/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: 'web-user',
          query: inputMessage,
          priority: 'medium',
          require_agents: selectedAgent && selectedAgent !== 'auto' ? [selectedAgent] : undefined,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to process message');
      }

      const result = await response.json();

      // Add agent response
      const agentMessage: Omit<ChatMessage, 'id' | 'timestamp'> = {
        type: 'agent',
        content: result.results ? formatAgentResponse(result) : 'Xin lỗi, tôi không thể xử lý yêu cầu này ngay bây giờ.',
        agent: result.reasoning ? 'Zeus Master' : 'System',
        metadata: {
          reasoning: result.reasoning,
          confidence: result.confidence,
          agent_used: Object.keys(result.results || {}).join(', '),
          execution_time: Date.now() - Date.parse(result.timestamp || new Date().toISOString()),
        },
      };

      dispatch(addMessage(agentMessage));
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: Omit<ChatMessage, 'id' | 'timestamp'> = {
        type: 'system',
        content: 'Có lỗi xảy ra khi xử lý tin nhắn. Vui lòng thử lại.',
        status: 'error',
      };
      dispatch(addMessage(errorMessage));
    } finally {
      dispatch(setTyping(false));
    }
  };

  const formatAgentResponse = (result: any) => {
    let response = '';
    
    if (result.reasoning) {
      response += `**Phân tích:** ${result.reasoning}\n\n`;
    }

    if (result.results) {
      Object.entries(result.results).forEach(([agent, data]: [string, any]) => {
        response += `**${agent.toUpperCase()}:**\n`;
        
        if (data.output) {
          if (typeof data.output === 'object') {
            if (data.output.actions) {
              data.output.actions.forEach((action: any) => {
                response += `- ${action.type}: ${JSON.stringify(action, null, 2)}\n`;
              });
            } else {
              response += `${JSON.stringify(data.output, null, 2)}\n`;
            }
          } else {
            response += `${data.output}\n`;
          }
        }

        if (data.execution_time_ms) {
          response += `*Thời gian xử lý: ${data.execution_time_ms}ms*\n`;
        }

        response += '\n';
      });
    }

    return response || 'Đã xử lý yêu cầu thành công.';
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const handleQuickAction = (action: string) => {
    setInputMessage(action);
  };

  const handleClearChat = () => {
    dispatch(clearMessages());
  };

  const getMessageAvatar = (message: ChatMessage) => {
    if (message.type === 'user') {
      return (
        <Avatar sx={{ bgcolor: '#667eea', width: 40, height: 40 }}>
          <PersonIcon />
        </Avatar>
      );
    } else {
      const agent = agents.find(a => a.name.toLowerCase().includes(message.agent?.toLowerCase() || ''));
      return (
        <Avatar sx={{ bgcolor: agent?.color || '#764ba2', width: 40, height: 40 }}>
          {agent?.icon || <BotIcon />}
        </Avatar>
      );
    }
  };

  return (
    <Box sx={{ height: 'calc(100vh - 100px)', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5" component="h1">
            💬 Zeus Chat Interface
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Chip
              label={connectionStatus === 'connected' ? 'Connected' : 'Disconnected'}
              color={connectionStatus === 'connected' ? 'success' : 'error'}
              size="small"
            />
            <Tooltip title="Clear Chat">
              <IconButton onClick={handleClearChat} size="small">
                <ClearIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Agent Selection */}
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Typography variant="body2" sx={{ alignSelf: 'center', mr: 1 }}>
            Select Agent:
          </Typography>
          {agents.map((agent) => (
            <Chip
              key={agent.id}
              label={`${agent.icon} ${agent.name}`}
              onClick={() => setSelectedAgent(agent.id)}
              variant={selectedAgent === agent.id ? 'filled' : 'outlined'}
              sx={{
                backgroundColor: selectedAgent === agent.id ? agent.color : 'transparent',
                borderColor: agent.color,
                color: selectedAgent === agent.id ? 'white' : agent.color,
                '&:hover': {
                  backgroundColor: `${agent.color}33`,
                },
              }}
            />
          ))}
        </Box>
      </Paper>

      {/* Quick Actions */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="body2" sx={{ mb: 1, color: 'text.secondary' }}>
          Quick Actions:
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {quickActions.map((action, index) => (
            <Chip
              key={index}
              label={action}
              onClick={() => handleQuickAction(action)}
              variant="outlined"
              size="small"
              sx={{ '&:hover': { backgroundColor: 'rgba(102, 126, 234, 0.1)' } }}
            />
          ))}
        </Box>
      </Paper>

      {/* Chat Messages */}
      <Paper sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
          {messages.map((message) => (
            <Box
              key={message.id}
              sx={{
                display: 'flex',
                mb: 2,
                alignItems: 'flex-start',
                justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start',
              }}
            >
              {message.type !== 'user' && (
                <Box sx={{ mr: 1 }}>
                  {getMessageAvatar(message)}
                </Box>
              )}
              
              <Card
                sx={{
                  maxWidth: '70%',
                  minWidth: '200px',
                  backgroundColor: message.type === 'user' ? '#667eea' : 'rgba(255,255,255,0.1)',
                  color: message.type === 'user' ? 'white' : 'inherit',
                }}
              >
                <CardContent sx={{ pb: '16px !important' }}>
                  {message.type !== 'user' && (
                    <Typography variant="caption" sx={{ display: 'block', mb: 1, opacity: 0.8 }}>
                      {message.agent || 'System'} • {new Date(message.timestamp).toLocaleTimeString()}
                    </Typography>
                  )}
                  
                  <ReactMarkdown
                    components={{
                      p: ({ children }) => <Typography variant="body1" paragraph>{children}</Typography>,
                      code: ({ children }) => (
                        <Box
                          component="code"
                          sx={{
                            backgroundColor: 'rgba(0,0,0,0.2)',
                            padding: '2px 6px',
                            borderRadius: 1,
                            fontSize: '0.875em',
                          }}
                        >
                          {children}
                        </Box>
                      ),
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>

                  {message.metadata && (
                    <Box sx={{ mt: 1, pt: 1, borderTop: '1px solid rgba(255,255,255,0.2)' }}>
                      {message.metadata.confidence && (
                        <Typography variant="caption" sx={{ display: 'block', opacity: 0.7 }}>
                          Confidence: {(message.metadata.confidence * 100).toFixed(1)}%
                        </Typography>
                      )}
                      {message.metadata.execution_time && (
                        <Typography variant="caption" sx={{ display: 'block', opacity: 0.7 }}>
                          Execution Time: {message.metadata.execution_time}ms
                        </Typography>
                      )}
                    </Box>
                  )}
                </CardContent>
              </Card>

              {message.type === 'user' && (
                <Box sx={{ ml: 1 }}>
                  {getMessageAvatar(message)}
                </Box>
              )}
            </Box>
          ))}

          {isTyping && (
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Avatar sx={{ bgcolor: '#764ba2', width: 40, height: 40, mr: 1 }}>
                <BotIcon />
              </Avatar>
              <Card sx={{ backgroundColor: 'rgba(255,255,255,0.1)' }}>
                <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                  <CircularProgress size={16} sx={{ mr: 2 }} />
                  <Typography variant="body2">Zeus đang suy nghĩ...</Typography>
                </CardContent>
              </Card>
            </Box>
          )}

          <div ref={messagesEndRef} />
        </Box>

        {/* Input Area */}
        <Box sx={{ p: 2, borderTop: '1px solid rgba(255,255,255,0.1)' }}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              variant="outlined"
              placeholder="Nhập tin nhắn... (Shift+Enter để xuống dòng)"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              multiline
              maxRows={4}
              disabled={isTyping}
            />
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Tooltip title="Send Message">
                <IconButton
                  color="primary"
                  onClick={handleSendMessage}
                  disabled={!inputMessage.trim() || isTyping}
                  sx={{ backgroundColor: '#667eea', color: 'white', '&:hover': { backgroundColor: '#5a6fd8' } }}
                >
                  <SendIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Voice Input">
                <IconButton color="secondary" size="small">
                  <MicIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Attach File">
                <IconButton color="secondary" size="small">
                  <AttachIcon />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default ChatInterface;