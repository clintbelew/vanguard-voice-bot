import werkzeug.urls

# Patch werkzeug.urls.url_quote function to handle unicode properly
original_url_quote = werkzeug.urls.url_quote

def patched_url_quote(string, charset='utf-8', errors='strict', safe='/:', unsafe=''):
    if isinstance(string, str):
        string = string.encode(charset, errors)
    return original_url_quote(string, charset, errors, safe, unsafe)

werkzeug.urls.url_quote = patched_url_quote
