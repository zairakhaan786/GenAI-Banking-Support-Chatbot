/**
 * BankBot – Frontend Application Logic
 * Handles: session management, chat API calls, file upload, UI state
 */

/* ── Configuration ───────────────────────────────────────────────────────────── */
const CONFIG = {
  API_BASE: window.location.origin + '/api',
  SESSION_KEY: 'bankbot_session_id',
  MAX_INPUT_LENGTH: 2000,
};

/* ── State ───────────────────────────────────────────────────────────────────── */
const state = {
  sessionId: null,
  isLoading: false,
  messageCount: 0,
  currentSources: [],
};

/* ── DOM References ──────────────────────────────────────────────────────────── */
const els = {
  messagesContainer: document.getElementById('messages-container'),
  welcomeScreen:     document.getElementById('welcome-screen'),
  messageInput:      document.getElementById('message-input'),
  sendBtn:           document.getElementById('send-btn'),
  charCount:         document.getElementById('char-count'),
  typingIndicator:   document.getElementById('typing-indicator'),
  clearBtn:          document.getElementById('clear-btn'),
  sidebarToggle:     document.getElementById('sidebar-toggle'),
  sidebar:           document.querySelector('.sidebar'),
  uploadZone:        document.getElementById('upload-zone'),
  uploadTrigger:     document.getElementById('upload-trigger'),
  fileInput:         document.getElementById('file-input'),
  uploadProgress:    document.getElementById('upload-progress'),
  progressFill:      document.getElementById('progress-fill'),
  progressText:      document.getElementById('progress-text'),
  sourceModal:       document.getElementById('source-modal'),
  modalBody:         document.getElementById('modal-body'),
  modalClose:        document.getElementById('modal-close'),
  toastContainer:    document.getElementById('toast-container'),
  statusDot:         document.getElementById('status-dot'),
  sessionLabel:      document.getElementById('session-label'),
  modelBadge:        document.getElementById('model-badge'),
  headerSub:         document.getElementById('header-sub'),
  quickActions:      document.getElementById('quick-actions'),
};

/* ── Session ─────────────────────────────────────────────────────────────────── */
function initSession() {
  let sid = sessionStorage.getItem(CONFIG.SESSION_KEY);
  if (!sid) {
    sid = 'session_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8);
    sessionStorage.setItem(CONFIG.SESSION_KEY, sid);
  }
  state.sessionId = sid;
  els.sessionLabel.textContent = 'Session: ' + sid.slice(-8);
}

/* ── API Helpers ─────────────────────────────────────────────────────────────── */
async function apiChat(query) {
  const resp = await fetch(`${CONFIG.API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, session_id: state.sessionId, top_k: 5 }),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: 'Server error' }));
    throw new Error(err.detail || `HTTP ${resp.status}`);
  }
  return resp.json();
}

async function apiHealth() {
  const resp = await fetch(`${CONFIG.API_BASE}/health`);
  return resp.ok ? resp.json() : null;
}

async function apiUpload(file, onProgress) {
  const form = new FormData();
  form.append('file', file);

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${CONFIG.API_BASE}/upload`);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100));
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        const body = JSON.parse(xhr.responseText || '{}');
        reject(new Error(body.detail || `Upload failed (${xhr.status})`));
      }
    };
    xhr.onerror = () => reject(new Error('Network error during upload'));
    xhr.send(form);
  });
}

/* ── Message Rendering ───────────────────────────────────────────────────────── */
function renderMessage(role, content, sources = [], timestamp = new Date()) {
  state.messageCount++;

  // Hide welcome screen on first message
  if (state.messageCount === 1) {
    els.welcomeScreen.style.display = 'none';
  }

  const timeStr = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const isUser = role === 'user';

  const group = document.createElement('div');
  group.className = 'message-group';

  const row = document.createElement('div');
  row.className = `message-row ${isUser ? 'user' : 'bot'}`;

  const avatar = document.createElement('div');
  avatar.className = isUser ? 'avatar-user' : 'avatar-xs';
  avatar.textContent = isUser ? '👤' : '🤖';

  const bubble = document.createElement('div');
  bubble.className = `bubble ${isUser ? 'bubble-user' : 'bubble-bot'}`;

  // Render content (simple markdown-like parsing)
  bubble.innerHTML = formatContent(content);

  // Metadata (time + sources button)
  const meta = document.createElement('div');
  meta.className = 'bubble-meta';

  const time = document.createElement('span');
  time.className = 'bubble-time';
  time.textContent = timeStr;
  meta.appendChild(time);

  if (!isUser && sources.length > 0) {
    const srcBtn = document.createElement('button');
    srcBtn.className = 'sources-btn';
    srcBtn.textContent = `📚 ${sources.length} source${sources.length > 1 ? 's' : ''}`;
    srcBtn.addEventListener('click', () => openSourceModal(sources));
    meta.appendChild(srcBtn);
  }

  bubble.appendChild(meta);
  row.appendChild(avatar);
  row.appendChild(bubble);
  group.appendChild(row);

  els.messagesContainer.appendChild(group);
  scrollToBottom();

  return group;
}

function formatContent(text) {
  // Basic markdown: bold, bullets, line breaks
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/^[-•]\s+(.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
    .replace(/\n{2,}/g, '</p><p>')
    .replace(/\n/g, '<br>')
    .replace(/^(.+)$/, '<p>$1</p>');
}

function scrollToBottom() {
  setTimeout(() => {
    els.messagesContainer.scrollTop = els.messagesContainer.scrollHeight;
  }, 50);
}

/* ── Chat Flow ───────────────────────────────────────────────────────────────── */
async function sendMessage(query) {
  if (!query.trim() || state.isLoading) return;

  state.isLoading = true;
  setInputEnabled(false);

  // Render user message
  renderMessage('user', query);

  // Clear input
  els.messageInput.value = '';
  updateCharCount();
  autoResizeInput();

  // Show typing indicator
  els.typingIndicator.classList.remove('hidden');
  scrollToBottom();

  try {
    const data = await apiChat(query);

    // Update model badge
    if (data.model_used) {
      els.modelBadge.textContent = data.model_used.split('/').pop() || 'RAG';
    }

    // Render bot response
    renderMessage('assistant', data.answer, data.sources || []);

  } catch (err) {
    renderMessage('assistant', `⚠️ **Sorry, I encountered an issue.**\n\n${err.message}\n\nPlease try again or contact support.`);
    showToast('error', '❌ Request failed — ' + err.message);
  } finally {
    els.typingIndicator.classList.add('hidden');
    state.isLoading = false;
    setInputEnabled(true);
    els.messageInput.focus();
  }
}

/* ── Input Handling ──────────────────────────────────────────────────────────── */
function setInputEnabled(enabled) {
  els.messageInput.disabled = !enabled;
  els.sendBtn.disabled = !enabled || els.messageInput.value.trim().length === 0;
}

function updateCharCount() {
  const len = els.messageInput.value.length;
  els.charCount.textContent = `${len}/${CONFIG.MAX_INPUT_LENGTH}`;
  els.sendBtn.disabled = len === 0 || state.isLoading;
}

function autoResizeInput() {
  const el = els.messageInput;
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 140) + 'px';
}

els.messageInput.addEventListener('input', () => {
  updateCharCount();
  autoResizeInput();
});

els.messageInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    const q = els.messageInput.value.trim();
    if (q) sendMessage(q);
  }
});

els.sendBtn.addEventListener('click', () => {
  const q = els.messageInput.value.trim();
  if (q) sendMessage(q);
});

/* ── Quick Actions & Chips ───────────────────────────────────────────────────── */
els.quickActions.querySelectorAll('.quick-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const q = btn.dataset.query;
    if (q) sendMessage(q);
    // Close sidebar on mobile
    els.sidebar.classList.remove('open');
  });
});

document.querySelectorAll('.chip').forEach(chip => {
  chip.addEventListener('click', () => {
    const q = chip.dataset.query;
    if (q) sendMessage(q);
  });
});

/* ── Clear Conversation ──────────────────────────────────────────────────────── */
els.clearBtn.addEventListener('click', () => {
  // Reset session
  sessionStorage.removeItem(CONFIG.SESSION_KEY);
  initSession();

  // Clear chat
  state.messageCount = 0;
  state.isLoading = false;
  els.messagesContainer.innerHTML = '';
  els.messagesContainer.appendChild(els.welcomeScreen);
  els.welcomeScreen.style.display = '';
  els.typingIndicator.classList.add('hidden');

  showToast('info', '🔄 Conversation cleared — new session started');
});

/* ── Sidebar Toggle (mobile) ─────────────────────────────────────────────────── */
els.sidebarToggle.addEventListener('click', () => {
  els.sidebar.classList.toggle('open');
});

document.addEventListener('click', (e) => {
  if (!els.sidebar.contains(e.target) && !els.sidebarToggle.contains(e.target)) {
    els.sidebar.classList.remove('open');
  }
});

/* ── File Upload ─────────────────────────────────────────────────────────────── */
els.uploadTrigger.addEventListener('click', () => els.fileInput.click());
els.uploadZone.addEventListener('click', (e) => {
  if (e.target === els.uploadZone || e.target.classList.contains('upload-icon') || e.target.classList.contains('upload-text')) {
    els.fileInput.click();
  }
});

// Drag & Drop
els.uploadZone.addEventListener('dragover', (e) => { e.preventDefault(); els.uploadZone.classList.add('drag-over'); });
els.uploadZone.addEventListener('dragleave',() => els.uploadZone.classList.remove('drag-over'));
els.uploadZone.addEventListener('drop', (e) => {
  e.preventDefault();
  els.uploadZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) handleUpload(file);
});

els.fileInput.addEventListener('change', () => {
  if (els.fileInput.files[0]) handleUpload(els.fileInput.files[0]);
  els.fileInput.value = '';
});

async function handleUpload(file) {
  const allowed = ['pdf', 'txt', 'docx'];
  const ext = file.name.split('.').pop().toLowerCase();
  if (!allowed.includes(ext)) {
    showToast('error', `❌ Unsupported file type: .${ext}`);
    return;
  }
  if (file.size > 20 * 1024 * 1024) {
    showToast('error', '❌ File exceeds 20 MB limit');
    return;
  }

  els.uploadProgress.classList.remove('hidden');
  els.uploadZone.style.pointerEvents = 'none';
  els.progressFill.style.width = '0%';
  els.progressText.textContent = `Uploading ${file.name}…`;

  try {
    const result = await apiUpload(file, (pct) => {
      els.progressFill.style.width = pct + '%';
      els.progressText.textContent = `Processing… ${pct}%`;
    });

    els.progressFill.style.width = '100%';
    els.progressText.textContent = `✅ ${result.chunks_indexed} chunks indexed`;
    showToast('success', `✅ "${file.name}" indexed — ${result.chunks_indexed} chunks added`);

    // Notify in chat
    renderMessage('assistant',
      `📄 **Document uploaded successfully!**\n\n` +
      `**File:** ${file.name}\n` +
      `**Chunks indexed:** ${result.chunks_indexed}\n` +
      `**Total knowledge base size:** ${result.collection_size} chunks\n\n` +
      `You can now ask questions about the uploaded document.`
    );

    setTimeout(() => {
      els.uploadProgress.classList.add('hidden');
      els.uploadZone.style.pointerEvents = '';
    }, 3000);

  } catch (err) {
    els.progressText.textContent = `❌ Upload failed`;
    els.progressFill.style.width = '0%';
    showToast('error', '❌ Upload failed — ' + err.message);
    setTimeout(() => {
      els.uploadProgress.classList.add('hidden');
      els.uploadZone.style.pointerEvents = '';
    }, 2500);
  }
}

/* ── Source Modal ────────────────────────────────────────────────────────────── */
function openSourceModal(sources) {
  els.modalBody.innerHTML = '';
  sources.forEach((src, i) => {
    const item = document.createElement('div');
    item.className = 'source-item';
    const score = typeof src.score === 'number' ? (src.score * 100).toFixed(1) + '%' : 'N/A';
    item.innerHTML = `
      <div class="source-header">
        <span class="source-name">📄 ${src.source || 'knowledge_base'} · Chunk ${i + 1}</span>
        <span class="source-score">Relevance: ${score}</span>
      </div>
      <div class="source-content">${escapeHtml(src.content)}</div>
    `;
    els.modalBody.appendChild(item);
  });
  els.sourceModal.classList.remove('hidden');
}

els.modalClose.addEventListener('click', () => els.sourceModal.classList.add('hidden'));
els.sourceModal.addEventListener('click', (e) => {
  if (e.target === els.sourceModal) els.sourceModal.classList.add('hidden');
});

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') els.sourceModal.classList.add('hidden');
});

function escapeHtml(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

/* ── Toast ───────────────────────────────────────────────────────────────────── */
function showToast(type, message, duration = 4000) {
  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${message}</span>`;
  els.toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = 'none';
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(40px)';
    toast.style.transition = 'opacity 0.3s, transform 0.3s';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

/* ── Health Check ────────────────────────────────────────────────────────────── */
async function checkHealth() {
  try {
    const h = await apiHealth();
    if (h && h.status === 'healthy') {
      els.statusDot.classList.add('active');
      els.sessionLabel.textContent = `${h.collection_documents} docs indexed`;

      const llmComp = h.components?.llm;
      if (llmComp?.details) {
        const modelPart = llmComp.details.replace('Provider: ', '');
        els.modelBadge.textContent = modelPart.split('/').pop() || 'RAG';
      }
    } else if (h) {
      els.statusDot.style.background = '#f59e0b';
      showToast('info', '⚠️ Some services degraded — chatbot may have limited functionality');
    }
  } catch {
    els.statusDot.style.background = '#ef4444';
  }
}

/* ── Init ────────────────────────────────────────────────────────────────────── */
function init() {
  initSession();
  updateCharCount();
  checkHealth();

  // Focus input on desktop
  if (window.innerWidth > 768) {
    setTimeout(() => els.messageInput.focus(), 300);
  }
}

init();
