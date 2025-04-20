"""
Audio Manager Module for Voice Bot

This module handles serving audio files and managing the audio cache directory.
It provides routes for accessing cached audio files and utilities for audio management.
"""

import os
import logging
from pathlib import Path
from flask import Blueprint, send_from_directory, abort, current_app, request, Response
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants with absolute paths - define at module level
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(BASE_DIR, 'audio_cache')

# Create audio cache directory immediately
try:
    os.makedirs(CACHE_DIR, exist_ok=True)
    logger.info(f"Audio cache directory created at: {CACHE_DIR}")
except Exception as e:
    logger.error(f"Error creating audio cache directory: {str(e)}")

# Create logs directory with absolute path
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
try:
    os.makedirs(LOGS_DIR, exist_ok=True)
    logger.info(f"Logs directory created at: {LOGS_DIR}")
except Exception as e:
    logger.error(f"Error creating logs directory: {str(e)}")

# Create blueprint
audio_bp = Blueprint('audio', __name__)

@audio_bp.route('/audio/<filename>')
def serve_audio(filename):
    """Serve cached audio files with CORS headers to allow Twilio access."""
    try:
        # Use the global CACHE_DIR directly - no local variable needed
        logger.info(f"Serving audio file: {filename} from {CACHE_DIR}")
        
        # Check if file exists before attempting to serve
        file_path = os.path.join(CACHE_DIR, filename)
        if not os.path.exists(file_path):
            logger.error(f"Audio file not found: {file_path}")
            return Response(f"Audio file not found: {filename}", status=404)
            
        # Create response with file
        response = send_from_directory(CACHE_DIR, filename)
        
        # Add CORS headers to allow Twilio to access the audio files
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Content-Type'] = 'audio/mpeg'
        response.headers['Cache-Control'] = 'public, max-age=86400'
        
        logger.info(f"Added CORS headers to response for {filename}")
        return response
    except NameError as e:
        logger.error(f"NameError serving audio file {filename}: {str(e)}")
        # Return a more specific error for debugging
        return Response(f"NameError: {str(e)}", status=500)
    except Exception as e:
        logger.error(f"Error serving audio file {filename}: {str(e)}")
        # Return a more specific error for debugging
        return Response(f"Error: {str(e)}", status=500)

@audio_bp.route('/audio/<filename>', methods=['OPTIONS'])
def options_audio(filename):
    """Handle OPTIONS requests for CORS preflight."""
    response = current_app.make_default_options_response()
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Content-Type'] = 'audio/mpeg'
    return response

def clear_cache():
    """Clear the audio cache directory."""
    try:
        # Use the global CACHE_DIR directly - no local variable needed
        for file in Path(CACHE_DIR).glob('*.mp3'):
            file.unlink()
        logger.info("Audio cache cleared")
        return True
    except Exception as e:
        logger.error(f"Error clearing audio cache: {str(e)}")
        return False

def get_cache_stats():
    """Get statistics about the audio cache."""
    try:
        # Use the global CACHE_DIR directly - no local variable needed
        files = list(Path(CACHE_DIR).glob('*.mp3'))
        total_size = sum(f.stat().st_size for f in files)
        stats = {
            'file_count': len(files),
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024)
        }
        logger.info(f"Cache stats: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        return {
            'file_count': 0,
            'total_size_bytes': 0,
            'total_size_mb': 0
        }

def prune_cache(max_size_mb=100):
    """
    Prune the cache to keep it under the specified size limit.
    Removes oldest files first based on modification time.
    """
    try:
        # Use the global CACHE_DIR directly - no local variable needed
        stats = get_cache_stats()
        if stats['total_size_mb'] <= max_size_mb:
            return True
        
        # Get files sorted by modification time (oldest first)
        files = sorted(Path(CACHE_DIR).glob('*.mp3'), key=lambda f: f.stat().st_mtime)
        
        # Remove files until we're under the limit
        while stats['total_size_mb'] > max_size_mb and files:
            file_to_remove = files.pop(0)
            file_size = file_to_remove.stat().st_size / (1024 * 1024)
            file_to_remove.unlink()
            stats['total_size_mb'] -= file_size
            logger.info(f"Pruned cache file: {file_to_remove.name}")
        
        return True
    except Exception as e:
        logger.error(f"Error pruning cache: {str(e)}")
        return False
