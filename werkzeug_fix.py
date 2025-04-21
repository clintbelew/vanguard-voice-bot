from urllib.parse import quote as url_quote

# This file creates a compatibility layer for werkzeug 2.2.3
# It provides the url_quote function that was removed in werkzeug 3.0.0
# This allows the application to work with either version of werkzeug

# Usage: Place this file in the same directory as your application
# and import url_quote from this file instead of from werkzeug.urls
