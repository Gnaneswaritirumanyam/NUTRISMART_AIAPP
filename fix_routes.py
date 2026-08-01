import sys
import os

content = open('backend/main.py', 'r', encoding='utf-8').read()

route = '''
@app.get("/{page}.html", response_class=HTMLResponse)
async def serve_html_pages(page: str):
    import os
    path = os.path.join(STATIC_DIR, f"{page}.html")
    if not os.path.exists(path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Page not found")
    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())
'''

if '@app.get("/{page}.html"' not in content:
    with open('backend/main.py', 'a', encoding='utf-8') as f:
        f.write('\n' + route + '\n')
    print('Added catch-all route.')
else:
    print('Route already exists.')
