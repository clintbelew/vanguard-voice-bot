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

# Create blueprint
audio_bp = Blueprint('audio', __name__)

@audio_bp.route('/audio/<filename>')
def serve_audio(filename):
    """Serve cached audio files with CORS headers to allow Twilio access."""
    try:
        # Define cache directory using environment-aware approach
        cache_dir = os.environ.get('AUDIO_CACHE_DIR')
        if not cache_dir:
            # Fallback to a default path if environment variable is not set
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cache_dir = os.path.join(base_dir, 'audio_cache')
            # Ensure directory exists
            os.makedirs(cache_dir, exist_ok=True)
            logger.info(f"Using default audio cache directory: {cache_dir}")
        
        logger.info(f"Serving audio file: {filename} from {cache_dir}")
        
        # Check if file exists before attempting to serve
        file_path = os.path.join(cache_dir, filename)
        if not os.path.exists(file_path):
            logger.error(f"Audio file not found: {file_path}")
            return Response(f"Audio file not found: {filename}", status=404)
            
        # Create response with file
        response = send_from_directory(cache_dir, filename)
        
        # Add CORS headers to allow Twilio to access the audio files
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Content-Type'] = 'audio/mpeg'
        response.headers['Cache-Control'] = 'public, max-age=86400'
        
        logger.info(f"Added CORS headers to response for {filename}")
        return response
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
        # Define cache directory using environment-aware approach
        cache_dir = os.environ.get('AUDIO_CACHE_DIR')
        if not cache_dir:
            # Fallback to a default path if environment variable is not set
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cache_dir = os.path.join(base_dir, 'audio_cache')
        
        for file in Path(cache_dir).glob('*.mp3'):
            file.unlink()
        logger.info("Audio cache cleared")
        return True
    except Exception as e:
        logger.error(f"Error clearing audio cache: {str(e)}")
        return False

def get_cache_stats():
    """Get statistics about the audio cache."""
    try:
        # Define cache directory using environment-aware approach
        cache_dir = os.environ.get('AUDIO_CACHE_DIR')
        if not cache_dir:
            # Fallback to a default path if environment variable is not set
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cache_dir = os.path.join(base_dir, 'audio_cache')
        
        files = list(Path(cache_dir).glob('*.mp3'))
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
        # Define cache directory using environment-aware approach
        cache_dir = os.environ.get('AUDIO_CACHE_DIR')
        if not cache_dir:
            # Fallback to a default path if environment variable is not set
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cache_dir = os.path.join(base_dir, 'audio_cache')
        
        stats = get_cache_stats()
        if stats['total_size_mb'] <= max_size_mb:
            return True
        
        # Get files sorted by modification time (oldest first)
        files = sorted(Path(cache_dir).glob('*.mp3'), key=lambda f: f.stat().st_mtime)
        
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
