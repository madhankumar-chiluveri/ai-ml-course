// ==========================================================================
// AI & ML COURSE STUDIO - WORKSPACE INTERACTION LOGIC
// ==========================================================================

let workspaceTree = [];
let openTabs = [];
let activeFilePath = null;
let viewMode = 'rendered'; // 'rendered' or 'code'

document.addEventListener('DOMContentLoaded', () => {
  initWorkspace();
  initResizers();
  initChat();
  initSearch();
});

// Fetch workspace tree on load
async function initWorkspace() {
  const treeContainer = document.getElementById('tree-container');
  try {
    const res = await fetch('/api/tree');
    if (!res.ok) throw new Error('Failed to load tree');
    workspaceTree = await res.json();
    renderTree(workspaceTree, treeContainer);
    updateStats(workspaceTree);
  } catch (err) {
    // Fallback to local offline index if API is unreachable
    fetch('file-tree.json')
      .then(r => r.json())
      .then(data => {
        workspaceTree = data;
        renderTree(workspaceTree, treeContainer);
        updateStats(workspaceTree);
      })
      .catch(e => {
        treeContainer.innerHTML = `<div class="error-msg" style="padding:16px; color:#ef4444;"><i class="fa-solid fa-triangle-exclamation"></i> Error loading workspace tree</div>`;
      });
  }

  document.getElementById('refresh-tree-btn').addEventListener('click', initWorkspace);
  document.getElementById('view-mode-btn').addEventListener('click', toggleViewMode);
  document.getElementById('copy-file-btn').addEventListener('click', copyActiveFileContent);
}

// Render folder hierarchy
function renderTree(items, container, isRoot = true) {
  if (isRoot) container.innerHTML = '';
  
  items.forEach(item => {
    const itemEl = document.createElement('div');
    
    if (item.type === 'directory') {
      const folderHeader = document.createElement('div');
      folderHeader.className = 'tree-item folder-item';
      folderHeader.innerHTML = `
        <i class="fa-solid fa-chevron-right toggle-icon"></i>
        <i class="fa-solid fa-folder item-icon icon-folder"></i>
        <span>${item.name}</span>
      `;

      const childrenContainer = document.createElement('div');
      childrenContainer.className = 'tree-children hidden';
      
      folderHeader.addEventListener('click', (e) => {
        e.stopPropagation();
        const isHidden = childrenContainer.classList.contains('hidden');
        const icon = folderHeader.querySelector('.toggle-icon');
        if (isHidden) {
          childrenContainer.classList.remove('hidden');
          icon.className = 'fa-solid fa-chevron-down toggle-icon';
        } else {
          childrenContainer.classList.add('hidden');
          icon.className = 'fa-solid fa-chevron-right toggle-icon';
        }
      });

      itemEl.appendChild(folderHeader);
      itemEl.appendChild(childrenContainer);
      if (item.children && item.children.length > 0) {
        renderTree(item.children, childrenContainer, false);
      }
    } else {
      itemEl.className = 'tree-item file-item';
      itemEl.dataset.path = item.path;

      let iconClass = 'fa-solid fa-file icon-file';
      if (item.name.endsWith('.py')) iconClass = 'fa-brands fa-python icon-python';
      else if (item.name.endsWith('.md')) iconClass = 'fa-solid fa-file-lines icon-markdown';
      else if (item.name.endsWith('.docx')) iconClass = 'fa-solid fa-file-word icon-docx';

      itemEl.innerHTML = `
        <i class="${iconClass} item-icon"></i>
        <span>${item.name}</span>
      `;

      itemEl.addEventListener('click', (e) => {
        e.stopPropagation();
        openFileFromPath(item.path, item.name);
      });
    }

    container.appendChild(itemEl);
  });
}

// Calculate total file & directory statistics
function updateStats(tree) {
  let files = 0;
  let folders = 0;

  function count(items) {
    items.forEach(item => {
      if (item.type === 'directory') {
        folders++;
        if (item.children) count(item.children);
      } else {
        files++;
      }
    });
  }

  count(tree);
  document.getElementById('file-count-badge').innerHTML = `<i class="fa-solid fa-file"></i> ${files} files`;
  document.getElementById('dir-count-badge').innerHTML = `<i class="fa-solid fa-folder"></i> ${folders} folders`;
}

// Open file and display content in middle pane
async function openFileFromPath(filePath, fileName = null) {
  if (!fileName) fileName = filePath.split('/').pop();

  activeFilePath = filePath;
  document.getElementById('active-context-file').innerText = fileName;

  // Manage Tabs
  if (!openTabs.includes(filePath)) {
    openTabs.push(filePath);
  }
  renderTabs();

  // Highlight active tree item
  document.querySelectorAll('.tree-item').forEach(el => el.classList.remove('active'));
  const activeTreeEl = document.querySelector(`.tree-item[data-path="${filePath}"]`);
  if (activeTreeEl) activeTreeEl.classList.add('active');

  // Breadcrumb
  document.getElementById('breadcrumb-text').innerText = filePath;

  // Show Editor
  document.getElementById('welcome-screen').classList.add('hidden');
  const codeViewer = document.getElementById('code-viewer-wrapper');
  const markdownViewer = document.getElementById('markdown-viewer-wrapper');

  try {
    const res = await fetch(`/api/file?path=${encodeURIComponent(filePath)}`);
    const data = await res.json();
    const content = data.content || '';

    if (filePath.endsWith('.md') && viewMode === 'rendered') {
      markdownViewer.classList.remove('hidden');
      codeViewer.classList.add('hidden');
      document.getElementById('markdown-content').innerHTML = marked.parse(content);
    } else {
      codeViewer.classList.remove('hidden');
      markdownViewer.classList.add('hidden');
      
      const codeBlock = document.getElementById('code-block');
      let langClass = 'language-markdown';
      if (filePath.endsWith('.py')) langClass = 'language-python';
      else if (filePath.endsWith('.json')) langClass = 'language-json';

      codeBlock.className = langClass;
      codeBlock.textContent = content;
      Prism.highlightElement(codeBlock);
    }
  } catch (err) {
    console.error('Error fetching file content:', err);
  }
}

// Tab Bar Renderer
function renderTabs() {
  const tabBar = document.getElementById('tab-bar');
  tabBar.innerHTML = '';

  openTabs.forEach(filePath => {
    const fileName = filePath.split('/').pop();
    const tab = document.createElement('div');
    tab.className = `tab-item ${filePath === activeFilePath ? 'active' : ''}`;
    tab.innerHTML = `
      <span>${fileName}</span>
      <i class="fa-solid fa-xmark tab-close"></i>
    `;

    tab.addEventListener('click', () => openFileFromPath(filePath));
    tab.querySelector('.tab-close').addEventListener('click', (e) => {
      e.stopPropagation();
      openTabs = openTabs.filter(p => p !== filePath);
      if (activeFilePath === filePath) {
        activeFilePath = openTabs[openTabs.length - 1] || null;
        if (activeFilePath) openFileFromPath(activeFilePath);
        else {
          document.getElementById('welcome-screen').classList.remove('hidden');
          document.getElementById('code-viewer-wrapper').classList.add('hidden');
          document.getElementById('markdown-viewer-wrapper').classList.add('hidden');
          document.getElementById('breadcrumb-text').innerText = 'Select a file from left panel';
          document.getElementById('active-context-file').innerText = 'None';
        }
      }
      renderTabs();
    });

    tabBar.appendChild(tab);
  });
}

function toggleViewMode() {
  viewMode = viewMode === 'rendered' ? 'code' : 'rendered';
  if (activeFilePath) openFileFromPath(activeFilePath);
}

function copyActiveFileContent() {
  if (!activeFilePath) return;
  const content = document.getElementById('code-block').textContent;
  navigator.clipboard.writeText(content).then(() => {
    alert('File content copied to clipboard!');
  });
}

// Dynamic Resizable Panels
function initResizers() {
  const resizerLeft = document.getElementById('resizer-left');
  const resizerRight = document.getElementById('resizer-right');
  const paneLeft = document.getElementById('pane-left');
  const paneRight = document.getElementById('pane-right');

  let isDraggingLeft = false;
  let isDraggingRight = false;

  resizerLeft.addEventListener('mousedown', () => { isDraggingLeft = true; resizerLeft.classList.add('resizing'); });
  resizerRight.addEventListener('mousedown', () => { isDraggingRight = true; resizerRight.classList.add('resizing'); });

  document.addEventListener('mousemove', (e) => {
    if (isDraggingLeft) {
      const newWidth = Math.max(200, Math.min(e.clientX, 450));
      paneLeft.style.width = `${newWidth}px`;
    }
    if (isDraggingRight) {
      const newWidth = Math.max(260, Math.min(window.innerWidth - e.clientX, 500));
      paneRight.style.width = `${newWidth}px`;
    }
  });

  document.addEventListener('mouseup', () => {
    isDraggingLeft = false;
    isDraggingRight = false;
    resizerLeft.classList.remove('resizing');
    resizerRight.classList.remove('resizing');
  });

  // Collapse Left Panel
  document.getElementById('collapse-left-btn').addEventListener('click', () => {
    if (paneLeft.style.width === '0px' || paneLeft.classList.contains('collapsed')) {
      paneLeft.style.width = '280px';
      paneLeft.classList.remove('collapsed');
    } else {
      paneLeft.style.width = '0px';
      paneLeft.classList.add('collapsed');
    }
  });
}

// Search Filter in Tree
function initSearch() {
  const searchInput = document.getElementById('file-search-input');
  searchInput.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();
    document.querySelectorAll('.file-item').forEach(item => {
      const name = item.querySelector('span').innerText.toLowerCase();
      if (name.includes(query)) {
        item.style.display = 'flex';
      } else {
        item.style.display = 'none';
      }
    });
  });
}

// AI Chatbot Integration
function initChat() {
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const msg = input.value.trim();
    if (!msg) return;

    appendChatMessage('user', msg);
    input.value = '';

    // Show bot typing indicator
    const typingId = appendTypingIndicator();

    fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg, currentFile: activeFilePath })
    })
      .then(res => res.json())
      .then(data => {
        removeTypingIndicator(typingId);
        appendChatMessage('bot', data.reply);
      })
      .catch(err => {
        removeTypingIndicator(typingId);
        appendChatMessage('bot', 'Sorry, I ran into an error generating a response.');
      });
  });

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      form.dispatchEvent(new Event('submit'));
    }
  });
}

function sendPromptPill(text) {
  const input = document.getElementById('chat-input');
  input.value = text;
  document.getElementById('chat-form').dispatchEvent(new Event('submit'));
}

function appendChatMessage(role, text) {
  const container = document.getElementById('chat-messages');
  const msgDiv = document.createElement('div');
  msgDiv.className = `chat-message ${role}-message`;

  const avatar = role === 'bot' 
    ? `<div class="avatar"><i class="fa-solid fa-robot"></i></div>` 
    : `<div class="avatar"><i class="fa-solid fa-user"></i></div>`;

  const parsedText = role === 'bot' ? marked.parse(text) : `<p>${escapeHtml(text)}</p>`;

  msgDiv.innerHTML = `
    ${avatar}
    <div class="msg-content">${parsedText}</div>
  `;

  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;
}

function appendTypingIndicator() {
  const container = document.getElementById('chat-messages');
  const id = 'typing-' + Date.now();
  const typingDiv = document.createElement('div');
  typingDiv.id = id;
  typingDiv.className = 'chat-message bot-message';
  typingDiv.innerHTML = `
    <div class="avatar"><i class="fa-solid fa-robot"></i></div>
    <div class="msg-content"><i class="fa-solid fa-ellipsis fa-bounce"></i> Thinking...</div>
  `;
  container.appendChild(typingDiv);
  container.scrollTop = container.scrollHeight;
  return id;
}

function removeTypingIndicator(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function clearChat() {
  document.getElementById('chat-messages').innerHTML = `
    <div class="chat-message bot-message">
      <div class="avatar"><i class="fa-solid fa-robot"></i></div>
      <div class="msg-content"><p>Chat history cleared. How can I assist you with your AI/ML Course repository?</p></div>
    </div>
  `;
}

function escapeHtml(string) {
  return String(string).replace(/[&<>"']/g, function (s) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[s];
  });
}
