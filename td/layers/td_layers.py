# TouchDesigner LAYERS painting  -  one file does everything.
# Paste into an Execute DAT named 'layers', turn ON "Frame End".
#
# Records your painting TOP frame by frame, keeps ~80 evenly spaced frames,
# saves them into paintings/<date_time>/ in the website repo with a thumbnail,
# adds the painting to the gallery list and pushes to GitHub.
# In the browser the frames are stacked front to back, so the painting has depth.
#
#   op('layers').module.start()                 # begin recording
#   op('layers').module.finish()                # stop, save, upload
#   op('layers').module.finish('Night one')     # ...with a title
#   op('layers').module.cancel()                # stop and throw the take away
#   op('layers').module.push()                  # retry an upload (e.g. wifi was down)
#
# Tip: drive start/finish from a Keyboard In CHOP or a Button COMP with a CHOP Execute DAT.

import os, json, shutil, datetime, threading, subprocess

# ---------------- settings ----------------
REPO      = 'C:/Users/YOU/Documents/GitHub/makers-marks'   # local clone of the site repo
SRC_TOP   = 'layer_out'  # TOP to record. Best: a Fit TOP (1024 on the long side) after your painting.
THUMB_TOP = ''           # optional TOP for the thumbnail ('' = use the middle recorded frame)
EVERY     = 2            # save every Nth frame while recording (higher = lighter on the frame rate)
MAX       = 80           # layers kept in the final painting (phones struggle above ~100)
PUSH      = True         # False = save locally only (the monitor still updates)

# how the browser stacks the layers (same options as layers.html)
KEY       = 'luminance'  # luminance: dark pixels become see-through | alpha: use the TOP's alpha | none
BLENDING  = 'additive'   # additive = glowing light | normal = painterly, front layers cover back ones
OPACITY   = 0.35         # per layer; lower it if the stack blows out to white
DEPTH     = 1.2          # thickness of the stack, in painting widths
REVERSE   = False        # True = first frame at the back instead of the front
# ------------------------------------------

EXT = 'png' if KEY == 'alpha' else 'jpg'
_state = {'rec': False, 'n': 0}

def _tmp():
    return os.path.join(project.folder, '_layers_take')

def start():
    shutil.rmtree(_tmp(), ignore_errors=True)
    os.makedirs(_tmp())
    _state.update(rec=True, n=0)
    print('recording layers…')

def onFrameEnd(frame):
    if not _state['rec'] or int(absTime.frame) % EVERY:
        return
    op(SRC_TOP).save(os.path.join(_tmp(), 'f_%05d.%s' % (_state['n'], EXT)))
    _state['n'] += 1

def cancel():
    _state['rec'] = False
    shutil.rmtree(_tmp(), ignore_errors=True)
    print('take discarded')

def finish(title=''):
    _state['rec'] = False
    frames = sorted(f for f in os.listdir(_tmp()) if f.startswith('f_')) if os.path.isdir(_tmp()) else []
    if len(frames) < 2:
        print('nothing recorded - check SRC_TOP'); return
    if len(frames) > MAX:                                   # keep MAX evenly spaced frames
        step = (len(frames) - 1) / (MAX - 1)
        frames = [frames[round(i * step)] for i in range(MAX)]

    now = datetime.datetime.now()
    pid = now.strftime('%Y-%m-%d_%H%M%S')
    folder = os.path.join(REPO, 'paintings', pid)
    os.makedirs(folder, exist_ok=True)
    names = []
    for i, f in enumerate(frames):
        name = 'layer_%04d.%s' % (i, EXT)
        shutil.move(os.path.join(_tmp(), f), os.path.join(folder, name))
        names.append(name)
    shutil.rmtree(_tmp(), ignore_errors=True)

    thumb = op(THUMB_TOP) if THUMB_TOP else None
    if thumb is not None:
        thumb.save(os.path.join(folder, 'thumb.jpg'))
        thumb_name = 'thumb.jpg'
    else:
        thumb_name = names[len(names) // 2]

    with open(os.path.join(folder, 'manifest.json'), 'w') as fh:
        json.dump({'files': names, 'depth': DEPTH, 'key': KEY, 'blending': BLENDING,
                   'opacity': OPACITY, 'reverse': REVERSE}, fh, indent=2)

    idx_path = os.path.join(REPO, 'paintings', 'index.json')
    try:
        with open(idx_path) as fh: idx = json.load(fh)
    except Exception:
        idx = []
    idx.append({'id': pid, 'kind': 'layers', 'date': now.isoformat(timespec='seconds'),
                'title': title, 'thumb': thumb_name})
    with open(idx_path, 'w') as fh:
        json.dump(idx, fh, indent=1)
    print('saved painting', pid, '-', len(names), 'layers')
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
