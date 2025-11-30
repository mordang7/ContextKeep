#!/usr/bin/env python3
"""
ContextKeep V1.0 - WebUI Server
Provides a modern web interface for memory management
"""

from flask import Flask, render_template, jsonify, request
from datetime import datetime
from pathlib import Path
import sys
import os

# Add parent directory to path to import memory_manager
sys.path.insert(0, str(Path(__file__).parent))
from core.memory_manager import memory_manager

app = Flask(__name__)

@app.route('/')
def index():
    """Serve the main WebUI page"""
    return render_template('index.html')

@app.route('/api/memories', methods=['GET'])
def list_memories():
    """Get all memories"""
    try:
        memories = memory_manager.list_memories()
        return jsonify({'success': True, 'memories': memories})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/memories/<key>', methods=['GET'])
def get_memory(key):
    """Get a specific memory by key"""
    try:
        memory = memory_manager.retrieve_memory(key)
        if memory:
            return jsonify({'success': True, 'memory': memory})
        return jsonify({'success': False, 'error': 'Memory not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/memories', methods=['POST'])
def create_memory():
    """Create a new memory"""
    try:
        data = request.json
        key = data.get('key', '')
        title = data.get('title', '')
        content = data.get('content', '')
        tags = data.get('tags', [])
        
        if not key:
            return jsonify({'success': False, 'error': 'Key is required'}), 400
        
        # Add creation timestamp
        timestamp = datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')
        content_with_log = f"{content}\n\n---\n**Created:** {timestamp}"
        
        result = memory_manager.store_memory(key, content_with_log, tags, title)
        return jsonify({'success': True, 'memory': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/memories/<key>', methods=['PUT'])
def update_memory(key):
    """Update a memory (including title)"""
    try:
        data = request.json
        content = data.get('content', '')
        title = data.get('title', '')
        tags = data.get('tags', [])
        action = data.get('action', 'Manual Edit')  # Track what kind of edit
        
        # Get existing memory to check for changes
        existing = memory_manager.retrieve_memory(key)
        
        # Create detailed edit log
        timestamp = datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')
        
        # Determine what changed
        changes = []
        if existing:
            if existing.get('title') != title:
                changes.append(f"Title changed from '{existing.get('title')}' to '{title}'")
            if existing.get('content') != content:
                changes.append("Content modified")
        
        # Build log entry
        if changes:
            change_description = " | ".join(changes)
            log_entry = f"\n\n---\n**{timestamp} | {action}**\n{change_description}"
        else:
            log_entry = f"\n\n---\n**{timestamp} | {action}**"
        
        content_with_log = f"{content}{log_entry}"
        
        result = memory_manager.store_memory(key, content_with_log, tags, title)
        return jsonify({'success': True, 'memory': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/memories/<key>', methods=['DELETE'])
def delete_memory(key):
    """Delete a memory"""
    try:
        success = memory_manager.delete_memory(key)
        if success:
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Memory not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/search', methods=['GET'])
def search_memories():
    """Search memories"""
    try:
        query = request.args.get('q', '')
        results = memory_manager.search_memories(query)
        return jsonify({'success': True, 'memories': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("🌐 Starting ContextKeep V1.0 WebUI...")
    print("📍 Access at: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
