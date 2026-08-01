import sys

content = open('frontend/js/api_config.js', 'r', encoding='utf-8').read()

to_replace = """    const url = endpoint.startsWith("http")
        ? endpoint
        : `${window.API_BASE_URL}${endpoint}`;"""

replacement = """    let normalized = endpoint;
    if (normalized.startsWith("./")) {
        normalized = normalized.slice(1);
    }
    if (!normalized.startsWith("/")) {
        normalized = "/" + normalized;
    }
    const url = endpoint.startsWith("http")
        ? endpoint
        : `${window.API_BASE_URL}${normalized}`;"""

if to_replace in content:
    content = content.replace(to_replace, replacement)
    with open('frontend/js/api_config.js', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed api_config.js.")
else:
    print("Could not find the block in api_config.js")
