"""
rebuild_index.py - rebuilds paintings/index.json from the painting folders.
Use it if the gallery list got emptied or out of sync:   python tools/rebuild_index.py
Keeps any titles that are still in the current index.json.
"""
import json, os, datetime

repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pdir = os.path.join(repo, 'paintings')
idx_path = os.path.join(pdir, 'index.json')
try:
    old = {p['id']: p for p in json.load(open(idx_path, encoding='utf-8'))}
except Exception:
    old = {}

out = []
for pid in sorted(os.listdir(pdir)):
    folder = os.path.join(pdir, pid)
    if not os.path.isdir(folder):
        continue
    files = os.listdir(folder)
    if 'manifest.json' in files:
        kind = 'layers'
        layers = json.load(open(os.path.join(folder, 'manifest.json'))).get('files', [])
        thumb = 'thumb.jpg' if 'thumb.jpg' in files else (layers[len(layers) // 2] if layers else '')
    elif 'skin.json' in files:
        kind, thumb = 'skin', 'thumb.jpg'
    else:
        print('skipping', pid, '(no manifest.json or skin.json)'); continue
    try:
        date = datetime.datetime.strptime(pid, '%Y-%m-%d_%H%M%S').isoformat()
    except ValueError:
        date = datetime.datetime.fromtimestamp(os.path.getmtime(folder)).isoformat(timespec='seconds')
    prev = old.get(pid, {})
    out.append({'id': pid, 'kind': kind, 'date': prev.get('date', date), 'title': prev.get('title', ''), 'thumb': prev.get('thumb', thumb)})

json.dump(out, open(idx_path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(f'index.json now lists {len(out)} paintings')
