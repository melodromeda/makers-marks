# TouchDesigner GALLERY  -  shared by both script sets.
# Paste into a Text DAT named 'gallery' in the same network as your other DATs.
#
# Keeps the station status (recording, shaping, naming, uploading, done),
# adds new paintings to paintings/index.json, waits for a name from the monitor,
# then uploads to GitHub in the background.
#
#   op('gallery').module.push()        # retry an upload (e.g. wifi was down)
#   op('gallery').module.rename('2026-09-26_003954', 'New name')   # fix a name later
#   op('gallery').module.hide('2026-09-26_003954')                 # take a painting off the site

import os, json, time, datetime, threading, subprocess, unicodedata

# ---------------- settings ----------------
REPO         = r'C:/Users/YOU/Documents/GitHub/makers-marks'   # keep the r in front!
PUSH         = True     # False = save locally only (the monitor still updates)
NAME_TIMEOUT = 60       # seconds to wait for a name before publishing as untitled
NAME_MAX     = 40       # longest allowed name
DONE_HOLD    = 12       # seconds the "in the gallery" message stays up
# ------------------------------------------

status = {'state': 'idle', 'frames': 0, 'id': '', 'kind': '', 'title': '', 'message': '',
          'since': time.time(), 'deadline': 0, 'timeout': NAME_TIMEOUT}
_later = []   # [frames_left, function]  (see defer)

def set_status(state, **kw):
    status.update(state=state, since=time.time(), message='', **kw)

def get_status():
    s = dict(status)
    s['elapsed'] = time.time() - s['since']
    if s['state'] == 'naming':
        s['remaining'] = max(0.0, s['deadline'] - time.time())
    return s

def defer(fn, frames=3):
    """run fn a few frames later, so the monitor gets to show the current status first"""
    _later.append([frames, fn])

def tick():
    """call every frame (both recorders do this from onFrameEnd)"""
    for item in list(_later):
        item[0] -= 1
        if item[0] <= 0:
            _later.remove(item)
            item[1]()
    s = status['state']
    if s == 'naming' and time.time() > status['deadline']:
        set_name('')                                   # nobody typed: publish untitled
    elif s in ('done', 'failed') and time.time() - status['since'] > DONE_HOLD:
        set_status('idle')

# ---------------- paintings ----------------
def new_painting():
    """returns (id, folder) for a new painting"""
    if status['state'] == 'naming':                    # someone started a new take before naming the last one
        set_name('')
    pid = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
    folder = os.path.join(REPO, 'paintings', pid)
    os.makedirs(folder, exist_ok=True)
    return pid, folder

def _index_path():
    return os.path.join(REPO, 'paintings', 'index.json')

def _load():
    try:
        with open(_index_path(), encoding='utf-8') as fh:
            return json.load(fh)
    except Exception:
        return []

def _save(idx):
    with open(_index_path(), 'w', encoding='utf-8') as fh:
        json.dump(idx, fh, indent=1, ensure_ascii=False)

def add_painting(pid, kind, thumb):
    """painting files are saved: list it (untitled for now) and ask the monitor for a name"""
    idx = _load()
    idx.append({'id': pid, 'kind': kind, 'date': datetime.datetime.now().isoformat(timespec='seconds'),
                'title': '', 'thumb': thumb})
    _save(idx)
    set_status('naming', id=pid, kind=kind, title='', deadline=time.time() + NAME_TIMEOUT, timeout=NAME_TIMEOUT)
    print('saved painting', pid, '- waiting for a name')

def clean(name):
    name = ''.join(ch for ch in str(name) if unicodedata.category(ch)[0] != 'C')
    return ' '.join(name.split())[:NAME_MAX]

def set_name(name):
    """called by the Web Server DAT when someone names the painting (or on timeout)"""
    if status['state'] != 'naming':
        return False
    pid, title = status['id'], clean(name)
    idx = _load()
    for p in idx:
        if p['id'] == pid:
            p['title'] = title
    _save(idx)
    print('named', pid, '->', title or '(untitled)')
    _publish(pid, title)
    return True

def rename(pid, name):
    idx = _load()
    for p in idx:
        if p['id'] == pid:
            p['title'] = clean(name)
    _save(idx); push('rename ' + pid)

def hide(pid):
    _save([p for p in _load() if p['id'] != pid]); push('hide ' + pid)

# ---------------- upload ----------------
def _publish(pid, title):
    if not PUSH:
        set_status('done', id=pid, title=title, kind=status['kind']); return
    set_status('uploading', id=pid, title=title, kind=status['kind'])
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
        _result(False, 'commit failed: ' + out); return
    run('pull', '--rebase', '--autostash')
    code, out = run('push')
    _result(code == 0, out)

def _result(ok, out):
    print('uploaded to GitHub' if ok else 'upload failed (saved locally, run push() later): ' + out)
    if status['state'] == 'uploading':
        status.update(state='done' if ok else 'failed', since=time.time(), message='' if ok else out[-200:])
