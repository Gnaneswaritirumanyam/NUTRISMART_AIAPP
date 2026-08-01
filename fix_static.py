import sys
import os

content = open('backend/main.py', 'r', encoding='utf-8').read()
mount_str = 'app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="root_static")'

if mount_str not in content:
    with open('backend/main.py', 'a', encoding='utf-8') as f:
        f.write(f'\n{mount_str}\n')
    print('Mounted root static files.')
else:
    print('Already mounted.')
