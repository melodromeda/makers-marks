# TouchDesigner publisher  -  paste into a Text DAT named 'publish'.
#
# Record a painting, save it into your local copy of the website repo,
# snapshot a thumbnail, add it to the gallery list and push to GitHub.
# The site updates about a minute later; the monitor (display.html) switches instantly.
#
#   op('publish').module.start()                 # begin recording
#   op('publish').module.finish()                # stop, save, upload
#   op('publish').module.finish('Night one')     # ...with a title
#   op('publish').module.push()                  # retry an upload (e.g. wifi was down)
#
# Tip: drive start/finish from a Keyboard In CHOP or a Button COMP with a CHOP Execute DAT.

import os, json, datetime, threading, subprocess

REPO      = 'C:/Users/YOU/Documents/GitHub/makers-marks'   # local clone of the site repo
RECORDER  = 'execute1'  # Execute DAT running td_skin_recorder.py
REC_CHOP  = 'rec'       # the Constant CHOP with the 'record' channel
THUMB_TOP = 'thumb'     # a TOP to snapshot: e.g. a Fit TOP set to 600x600 after your feedback painting
PUSH      = True        # False = save locally only (monitor still updates)

def start():
    op(RECORDER).module.clear()
    op(REC_CHOP).par.value0 = 1
    print('recording…')

def finish(title=''):
    op(REC_CHOP).par.value0 = 0
    now = datetime.datetime.now()
    pid = now.strftime('%Y-%m-%d_%H%M%S')
    folder = os.path.join(REPO, 'paintings', pid)
    os.makedirs(folder, exist_ok=True)

    if not op(RECORDER).module.save(os.path.join(folder, 'skin')):
        os.rmdir(folder); return
    thumb = op(THUMB_TOP)
    if thumb is not None:
        thumb.save(os.path.join(folder, 'thumb.jpg'))

    idx_path = os.path.join(REPO, 'paintings', 'index.json')
    try:
        with open(idx_path) as fh: idx = json.load(fh)
    except Exception:
        idx = []
    idx.append({'id': pid, 'kind': 'skin', 'date': now.isoformat(timespec='seconds'),
                'title': title, 'thumb': 'thumb.jpg'})
    with open(idx_path, 'w') as fh:
        json.dump(idx, fh, indent=1)
    print('saved painting', pid)
    op(RECORDER).module.clear()
    if PUSH:
        push('add painting ' + pid)

def push(msg='update paintings'):
    # runs in the background so TouchDesigner never freezes while uploading
    threading.Thread(target=_git, args=(msg,), daemon=True).start()

def _git(msg):
    flags = 0x08000000 if os.name == 'nt' else 0          # no console window flash on Windows
    def run(*args):
        r = subprocess.run(['git', '-C', REPO] + list(args), capture_output=True, text=True, creationflags=flags)
        return r.returncode, (r.stdout + r.stderr).strip()
    run('add', 'paintings')
    code, out = run('commit', '-m', msg)
    if code and 'nothing to commit' not in out:
        print('git commit failed:', out); return
    run('pull', '--rebase', '--autostash')
    code, out = run('push')
    print('uploaded to GitHub' if code == 0 else 'upload failed (saved locally, run push() later): ' + out)
