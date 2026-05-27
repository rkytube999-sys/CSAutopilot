/**
 * Customer Support Autopilot Widget
 * Embeddable chat widget for any website
 */
(function() {
  // Configuration
  let config = {
    backendUrl: 'http://localhost:8000',
    sessionId: null,
  };

  // Generate session ID if not provided
  function getSessionId() {
    let id = localStorage.getItem('csa_session_id');
    if (!id) {
      id = 'session-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('csa_session_id', id);
    }
    return id;
  }

  // Create widget container
  function createWidget() {
    // Check if already exists
    if (document.getElementById('csa-widget-container')) {
      return;
    }

    // Create container
    const container = document.createElement('div');
    container.id = 'csa-widget-container';
    container.style.cssText = 'position:fixed;bottom:20px;right:20px;z-index:9999;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;';
    document.body.appendChild(container);

    // Create chat bubble button
    const bubble = document.createElement('button');
    bubble.id = 'csa-chat-bubble';
    bubble.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>';
    bubble.style.cssText = 'width:60px;height:60px;border-radius:50%;background:#3b82f6;border:none;color:white;cursor:pointer;box-shadow:0 4px 6px rgba(0,0,0,0.1);transition:transform 0.2s;display:flex;align-items:center;justify-content:center;';
    bubble.onclick = toggleChat;
    bubble.onmouseover = () => bubble.style.transform = 'scale(1.1)';
    bubble.onmouseout = () => bubble.style.transform = 'scale(1)';
    container.appendChild(bubble);

    // Create chat window (hidden by default)
    const chatWindow = document.createElement('div');
    chatWindow.id = 'csa-chat-window';
    chatWindow.style.cssText = 'display:none;width:380px;height:500px;background:white;border-radius:12px;box-shadow:0 10px 25px rgba(0,0,0,0.15);flex-direction:column;overflow:hidden;';
    container.appendChild(chatWindow);

    // Build chat window content
    buildChatWindow(chatWindow);
  }

  function buildChatWindow(window) {
    // Header
    const header = document.createElement('div');
    header.style.cssText = 'padding:16px;background:#3b82f6;color:white;display:flex;justify-content:space-between;align-items:center;';
    header.innerHTML = '<strong style="font-size:16px;">Customer Support</strong><button id="csa-close-btn" style="background:none;border:none;color:white;cursor:pointer;font-size:20px;">&times;</button>';
    window.appendChild(header);

    // Messages area
    const messages = document.createElement('div');
    messages.id = 'csa-messages';
    messages.style.cssText = 'flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:12px;background:#f9fafb;';
    window.appendChild(messages);

    // Welcome message
    messages.innerHTML = '<div style="text-align:center;color:#6b7280;margin-top:40px;">Hi! How can I help you today?</div>';

    // Input area
    const inputArea = document.createElement('form');
    inputArea.style.cssText = 'padding:16px;border-top:1px solid #e5e7eb;display:flex;gap:8px;background:white;';
    inputArea.innerHTML = '<input type="text" id="csa-input" placeholder="Type your message..." style="flex:1;padding:12px;border:1px solid #e5e7eb;border-radius:8px;outline:none;" /><button type="submit" style="padding:12px 20px;background:#3b82f6;color:white;border:none;border-radius:8px;cursor:pointer;">Send</button>';
    window.appendChild(inputArea);

    // Close button handler
    document.getElementById('csa-close-btn').onclick = toggleChat;

    // Form submit handler
    inputArea.onsubmit = async (e) => {
      e.preventDefault();
      const input = document.getElementById('csa-input');
      const message = input.value.trim();
      if (!message) return;

      // Add user message
      addMessage(messages, message, 'user');
      input.value = '';

      // Send to backend
      try {
        const response = await fetch(config.backendUrl + '/api/chat/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: message,
            session_id: getSessionId(),
          }),
        });

        const data = await response.json();
        addMessage(messages, data.response || 'Sorry, I could not process your request.', 'assistant');
      } catch (error) {
        addMessage(messages, 'Sorry, there was an error. Please try again.', 'assistant');
      }
    };
  }

  function addMessage(container, content, role) {
    // Remove welcome message if present
    const welcome = container.querySelector('div[style*="text-align:center"]');
    if (welcome) welcome.remove();

    const message = document.createElement('div');
    message.style.cssText = 'max-width:80%;padding:12px 16px;border-radius:12px;' + 
      (role === 'user' 
        ? 'background:#3b82f6;color:white;align-self:flex-end;' 
        : 'background:#e5e7eb;color:#1f2937;align-self:flex-start;');
    message.textContent = content;
    container.appendChild(message);
    container.scrollTop = container.scrollHeight;
  }

  function toggleChat() {
    const window = document.getElementById('csa-chat-window');
    const bubble = document.getElementById('csa-chat-bubble');
    
    if (window.style.display === 'none') {
      window.style.display = 'flex';
      bubble.style.display = 'none';
    } else {
      window.style.display = 'none';
      bubble.style.display = 'flex';
    }
  }

  // Initialize widget
  window.CSA = {
    init: function(userConfig) {
      if (userConfig) {
        config = { ...config, ...userConfig };
      }
      createWidget();
    },
  };

  // Auto-initialize if script loaded with data attributes
  const script = document.currentScript;
  if (script) {
    const autoInit = script.getAttribute('data-auto-init');
    if (autoInit !== 'false') {
      setTimeout(() => {
        window.CSA.init({
          backendUrl: script.getAttribute('data-backend-url') || config.backendUrl,
        });
      }, 100);
    }
  }
})();
