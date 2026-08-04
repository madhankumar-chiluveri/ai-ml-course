const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

const PORT = 3000;
const ROOT_DIR = __dirname;

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.md': 'text/markdown; charset=utf-8',
  '.py': 'text/plain; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8'
};

function getFileTree(dir, baseDir = dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const result = [];
  for (const entry of entries) {
    if (entry.name === '.git' || entry.name === 'node_modules' || entry.name === 'file-tree.json' || entry.name === 'server.js') continue;
    const fullPath = path.join(dir, entry.name);
    const relPath = path.relative(baseDir, fullPath).replace(/\\/g, '/');
    if (entry.isDirectory()) {
      result.push({
        name: entry.name,
        path: relPath,
        type: 'directory',
        children: getFileTree(fullPath, baseDir)
      });
    } else {
      result.push({
        name: entry.name,
        path: relPath,
        type: 'file',
        size: fs.statSync(fullPath).size
      });
    }
  }
  return result;
}

const server = http.createServer((req, res) => {
  const parsedUrl = url.parse(req.url, true);
  const pathname = parsedUrl.pathname;

  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  if (pathname === '/api/tree') {
    try {
      const tree = getFileTree(ROOT_DIR);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(tree));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: err.message }));
    }
    return;
  }

  if (pathname === '/api/file') {
    const filePath = parsedUrl.query.path;
    if (!filePath) {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Missing path parameter' }));
      return;
    }
    const safePath = path.normalize(path.join(ROOT_DIR, filePath));
    if (!safePath.startsWith(ROOT_DIR)) {
      res.writeHead(403, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Access denied' }));
      return;
    }
    try {
      if (fs.existsSync(safePath) && fs.statSync(safePath).isFile()) {
        const content = fs.readFileSync(safePath, 'utf8');
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ path: filePath, content }));
      } else {
        res.writeHead(404, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'File not found' }));
      }
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: err.message }));
    }
    return;
  }

  if (pathname === '/api/chat' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const data = JSON.parse(body);
        const userPrompt = data.message || '';
        const currentFile = data.currentFile || '';

        let reply = '';
        const lower = userPrompt.toLowerCase();

        if (lower.includes('python') || lower.includes('01_python_basics') || currentFile.includes('python')) {
          reply = `### 🐍 Python Basics Overview\n\nIn your practice section under \`practice/phase-0-engineering-foundations/01_python_basics.py\`, you have foundation exercises for Python.\n\n**Key Topics:**\n- Data Structures (Lists, Dicts, Sets)\n- Functions & Type Hints\n- File Handling & Error handling\n\nWould you like me to run this script or explain any specific function?`;
        } else if (lower.includes('roadmap') || lower.includes('course') || lower.includes('path')) {
          reply = `### 📍 AI & ML Course Roadmap\n\nYour repository contains structured learning paths:\n1. **Phase 0:** Engineering Foundations (Python, Git, Environment Setup)\n2. **Phase 1:** Math Foundations (Linear Algebra, Calculus, Statistics)\n3. **LLM Fundamentals:** Prompt Engineering, Transformers, Fine-Tuning\n4. **RAG Systems:** Vector DBs, Embeddings, Chunking Strategies\n\nCheck out \`course-path/README.md\` for the full breakdown!`;
        } else if (lower.includes('rag') || lower.includes('vector')) {
          reply = `### 🔍 RAG Systems (Retrieval-Augmented Generation)\n\nRAG architecture enhances LLMs by connecting them to external knowledge sources.\n\n**Core Components:**\n- **Chunking**: Dividing documents into semantic chunks\n- **Embeddings**: Converting text into high-dimensional vectors\n- **Vector Store**: Storing & querying (FAISS, Chroma, Pinecone)\n- **Synthesis**: Passing context + query to LLM`;
        } else {
          reply = `I am analyzing your request regarding **${currentFile ? currentFile : 'the AI/ML Course repository'}**.\n\nHow can I help you explore or write code for this module today?`;
        }

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ reply }));
      } catch (err) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid JSON' }));
      }
    });
    return;
  }

  let reqPath = pathname === '/' ? '/index.html' : pathname;
  let safePath = path.normalize(path.join(ROOT_DIR, reqPath));

  if (!safePath.startsWith(ROOT_DIR)) {
    res.writeHead(403);
    res.end('Forbidden');
    return;
  }

  fs.readFile(safePath, (err, data) => {
    if (err) {
      res.writeHead(404, { 'Content-Type': 'text/html' });
      res.end('<h1>404 Not Found</h1>');
    } else {
      const ext = path.extname(safePath).toLowerCase();
      const contentType = MIME_TYPES[ext] || 'application/octet-stream';
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(data);
    }
  });
});

server.listen(PORT, () => {
  console.log(`🚀 AI Course Dashboard running at http://localhost:${PORT}`);
});
