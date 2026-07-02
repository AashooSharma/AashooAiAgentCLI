"""
Lightweight Web Editor Server for Aashoo AI Agent CLI.
Zero extra dependencies (uses built-in http.server).
Runs on Windows, Linux, and Termux.
"""

import os
import urllib.parse
import json
import threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer

# Project directory to be edited
_project_dir = "."
_server_instance = None
_server_thread = None

# Custom HTML template for Monaco Web Editor
EDITOR_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aashoo Web Editor</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0f111a;
            --bg-secondary: #1a1c29;
            --border-color: #2e3047;
            --text-primary: #f8f8f2;
            --text-secondary: #9092b0;
            --accent-color: #00e6ff;
            --accent-hover: #00b3cc;
            --success-color: #50fa7b;
            --error-color: #ff5555;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Outfit', sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            height: 100vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }

        /* Top Header */
        header {
            height: 55px;
            background-color: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 20px;
            z-index: 10;
        }

        .logo-container {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .logo-icon {
            font-size: 24px;
            animation: pulse 2s infinite;
        }

        .logo-title {
            font-size: 18px;
            font-weight: 600;
            background: linear-gradient(45deg, #00e6ff, #bd93f9);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        /* Layout Main */
        .main-container {
            flex: 1;
            display: flex;
            height: calc(100vh - 55px - 30px);
        }

        /* Left Sidebar - File Explorer */
        .sidebar {
            width: 280px;
            background-color: var(--bg-secondary);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            overflow-y: auto;
        }

        .sidebar-header {
            padding: 15px;
            border-bottom: 1px solid var(--border-color);
            font-size: 14px;
            font-weight: 600;
            color: var(--text-secondary);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .refresh-btn {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            font-size: 16px;
        }
        
        .refresh-btn:hover {
            color: var(--accent-color);
        }

        .file-list {
            list-style: none;
            padding: 10px;
        }

        .file-item {
            padding: 8px 10px;
            border-radius: 6px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
            transition: all 0.2s ease;
            margin-bottom: 3px;
        }

        .file-item:hover {
            background-color: rgba(255, 255, 255, 0.05);
            color: var(--accent-color);
        }

        .file-item.active {
            background-color: rgba(0, 230, 255, 0.1);
            color: var(--accent-color);
            border-left: 3px solid var(--accent-color);
        }

        /* Right Editor Pane */
        .editor-pane {
            flex: 1;
            display: flex;
            flex-direction: column;
            position: relative;
        }

        #editor-container {
            flex: 1;
            width: 100%;
            height: 100%;
        }

        /* Bottom Status Bar */
        .status-bar {
            height: 30px;
            background-color: var(--bg-secondary);
            border-top: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 15px;
            font-size: 12px;
            color: var(--text-secondary);
        }

        .status-file {
            font-weight: 600;
        }

        .status-message {
            transition: color 0.3s;
        }

        .status-message.success {
            color: var(--success-color);
        }

        .status-message.unsaved {
            color: var(--error-color);
            font-weight: bold;
        }

        .save-btn {
            background-color: var(--accent-color);
            color: #000;
            border: none;
            padding: 5px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: background-color 0.2s;
        }

        .save-btn:hover {
            background-color: var(--accent-hover);
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }

        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: var(--bg-primary);
        }
        ::-webkit-scrollbar-thumb {
            background: var(--border-color);
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: var(--text-secondary);
        }
    </style>
</head>
<body>

    <header>
        <div class="logo-container">
            <span class="logo-icon">🚀</span>
            <span class="logo-title">Aashoo Web Editor</span>
        </div>
        <div class="header-actions">
            <button class="save-btn" onclick="saveCurrentFile()">Save (Ctrl+S)</button>
        </div>
    </header>

    <div class="main-container">
        <div class="sidebar">
            <div class="sidebar-header">
                <span>PROJECT FILES</span>
                <button class="refresh-btn" onclick="loadFiles()">🔄</button>
            </div>
            <ul class="file-list" id="files-root">
                <li style="padding: 15px; color: var(--text-secondary);">Loading...</li>
            </ul>
        </div>
        
        <div class="editor-pane">
            <div id="editor-container"></div>
        </div>
    </div>

    <div class="status-bar">
        <div id="status-file-info">No file open</div>
        <div id="status-msg" class="status-message">Ready</div>
        <div>Monaco Editor | Cross-platform</div>
    </div>

    <!-- RequireJS & Monaco CDN Loader -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/require.js/2.3.6/require.min.js"></script>
    <script>
        let editor = null;
        let currentFilePath = null;
        let isUnsaved = false;

        // Configure Monaco Editor path
        require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.39.0/min/vs' }});

        require(['vs/editor/editor.main'], function() {
            editor = monaco.editor.create(document.getElementById('editor-container'), {
                value: '// Select a file from the explorer to open it here.',
                language: 'javascript',
                theme: 'vs-dark',
                fontSize: 14,
                automaticLayout: true,
                minimap: { enabled: true }
            });

            // Listen for changes to mark unsaved status
            editor.onDidChangeModelContent(() => {
                if (currentFilePath && !isUnsaved) {
                    isUnsaved = true;
                    const statusMsg = document.getElementById('status-msg');
                    statusMsg.innerText = 'Unsaved changes';
                    statusMsg.className = 'status-message unsaved';
                }
            });

            // Add Ctrl+S save handler
            editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, function() {
                saveCurrentFile();
            });

            // Load file explorer
            loadFiles();
        });

        // Get file type/language from extension
        function getLanguage(fileName) {
            const ext = fileName.split('.').pop().toLowerCase();
            const map = {
                'py': 'python',
                'js': 'javascript',
                'ts': 'typescript',
                'html': 'html',
                'css': 'css',
                'json': 'json',
                'md': 'markdown',
                'sh': 'shell',
                'txt': 'plaintext',
                'ini': 'ini',
                'yaml': 'yaml',
                'yml': 'yaml'
            };
            return map[ext] || 'plaintext';
        }

        // Load files list
        function loadFiles() {
            fetch('/api/files')
                .then(res => res.json())
                .then(data => {
                    const filesRoot = document.getElementById('files-root');
                    filesRoot.innerHTML = '';
                    if (data.length === 0) {
                        filesRoot.innerHTML = '<li style="padding:15px;color:var(--text-secondary);">No files found.</li>';
                        return;
                    }
                    data.forEach(item => {
                        const li = document.createElement('li');
                        li.className = 'file-item';
                        if (currentFilePath === item.path) {
                            li.classList.add('active');
                        }
                        li.innerHTML = `📄 ${item.name}`;
                        li.onclick = () => openFile(item.path);
                        filesRoot.appendChild(li);
                    });
                })
                .catch(err => {
                    document.getElementById('files-root').innerHTML = '<li style="padding:15px;color:var(--error-color);">Error loading files.</li>';
                });
        }

        // Open a file
        function openFile(path) {
            if (isUnsaved) {
                if (!confirm('You have unsaved changes. Do you want to leave without saving?')) {
                    return;
                }
            }

            fetch(`/api/read?path=${encodeURIComponent(path)}`)
                .then(res => {
                    if (!res.ok) throw new Error('Could not read file');
                    return res.text();
                })
                .then(content => {
                    currentFilePath = path;
                    isUnsaved = false;
                    
                    // Set language & value
                    const model = monaco.editor.createModel(content, getLanguage(path));
                    editor.setModel(model);
                    
                    // Highlight active file
                    document.querySelectorAll('.file-item').forEach(el => {
                        el.classList.remove('active');
                    });
                    loadFiles();

                    // Update UI status
                    document.getElementById('status-file-info').innerText = path;
                    const statusMsg = document.getElementById('status-msg');
                    statusMsg.innerText = 'File loaded';
                    statusMsg.className = 'status-message success';
                })
                .catch(err => {
                    alert('Error: ' + err.message);
                });
        }

        // Save current file
        function saveCurrentFile() {
            if (!currentFilePath) {
                alert('No file open to save!');
                return;
            }

            const content = editor.getValue();
            const statusMsg = document.getElementById('status-msg');
            statusMsg.innerText = 'Saving...';
            statusMsg.className = 'status-message';

            fetch(`/api/save?path=${encodeURIComponent(currentFilePath)}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: content })
            })
            .then(res => {
                if (!res.ok) throw new Error('Save failed');
                return res.json();
            })
            .then(data => {
                isUnsaved = false;
                statusMsg.innerText = 'Saved successfully';
                statusMsg.className = 'status-message success';
            })
            .catch(err => {
                statusMsg.innerText = 'Save error';
                statusMsg.className = 'status-message unsaved';
                alert('Save failed: ' + err.message);
            });
        }
    </script>
</body>
</html>
"""

class EditorHTTPRequestHandler(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        # Mute logging to stdout to keep CLI interface clean
        pass

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        if path == "/":
            # Serve the Web Editor page
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(EDITOR_HTML.encode("utf-8"))
            
        elif path == "/api/files":
            # List files from project directory recursively
            files = []
            ignore_folders = {".git", "venv", ".venv", "node_modules", "__pycache__", ".aashoo"}
            try:
                base_path = Path(_project_dir)
                for root, dirs, filenames in os.walk(_project_dir):
                    # In-place modification to skip ignored dirs
                    dirs[:] = [d for d in dirs if d not in ignore_folders]
                    for fname in filenames:
                        # Skip temporary pyc, logs, and sensitive envs
                        if fname.endswith((".pyc", ".log")) or fname == ".env":
                            continue
                        f_abs = Path(root) / fname
                        f_rel = f_abs.relative_to(base_path)
                        files.append({
                            "name": str(f_rel).replace("\\", "/"),
                            "path": str(f_rel).replace("\\", "/")
                        })
                # Sort alphabetically
                files.sort(key=lambda x: x["name"].lower())
            except Exception as e:
                pass
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(files).encode("utf-8"))

        elif path == "/api/read":
            file_param = query.get("path", [""])[0]
            resolved = Path(_project_dir) / file_param
            
            # Security check: resolve to prevent directory traversal
            try:
                if not resolved.resolve().is_relative_to(Path(_project_dir).resolve()):
                    self.send_error(403, "Access Denied")
                    return
            except Exception:
                self.send_error(400, "Invalid File Path")
                return

            if resolved.exists() and resolved.is_file():
                try:
                    content = resolved.read_text(encoding="utf-8", errors="replace")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(content.encode("utf-8"))
                except Exception as e:
                    self.send_error(500, f"Error: {e}")
            else:
                self.send_error(404, "File not found")

        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        if path == "/api/save":
            file_param = query.get("path", [""])[0]
            resolved = Path(_project_dir) / file_param
            
            # Security check
            try:
                if not resolved.resolve().is_relative_to(Path(_project_dir).resolve()):
                    self.send_error(403, "Access Denied")
                    return
            except Exception:
                self.send_error(400, "Invalid File Path")
                return

            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode("utf-8"))
                
                # Write to file
                resolved.write_text(data["content"], encoding="utf-8")
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
            except Exception as e:
                self.send_error(500, f"Error saving file: {e}")
        else:
            self.send_error(404, "Not Found")


def start_editor_server(project_path: str, port: int = 8080) -> str:
    """Editor Web server ko start karta hai background thread mein."""
    global _project_dir, _server_instance, _server_thread
    
    if _server_instance is not None:
        return f"http://localhost:{port}"

    _project_dir = project_path
    
    def run_server():
        global _server_instance
        try:
            _server_instance = HTTPServer(("localhost", port), EditorHTTPRequestHandler)
            _server_instance.serve_forever()
        except Exception:
            pass

    _server_thread = threading.Thread(target=run_server, daemon=True)
    _server_thread.start()
    return f"http://localhost:{port}"


def stop_editor_server():
    """Web Server ko stop karta hai."""
    global _server_instance, _server_thread
    if _server_instance is not None:
        try:
            _server_instance.shutdown()
            _server_instance.server_close()
        except Exception:
            pass
        _server_instance = None
        _server_thread = None
