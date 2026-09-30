# TouchDesigner LAYERS painting  -  records your painting TOP frame by frame.
# Paste into an Execute DAT named 'layers', turn ON "Frame End".
# Needs the 'gallery' Text DAT (td/station/td_gallery.py) in the same network.
#
#   op('/project1/layers').module.toggle()   # start, or finish if already recording (use this for a MIDI button)
#   op('/project1/layers').module.start()
#   op('/project1/layers').module.finish()   # stop -> shape -> monitor asks for a name -> upload
#   op('/project1/layers').module.cancel()   # stop and throw the take away

import os, json, shutil, time

# ---------------- settings ----------------
GALLERY   = 'gallery'    # Text DAT with td_gallery.py (REPO + upload settings live there)
SRC_TOP   = 'layer_out'  # TOP to record: a Fit TOP (512 on the long side) after your painting
THUMB_TOP = ''           # optional TOP for the thumbnail ('' = use the middle recorded frame)
EVERY     = 1            # save every Nth frame while recording
MAX       = 200          # layers kept in the final painting (phones struggle above ~250 at 512 px)

# how the browser stacks the layers (same options as layers.html)
KEY       = 'luminance'  # luminance: dark pixels become see-through | alpha: use the TOP's alpha | none
BLENDING  = 'additive'   # additive = glowing light | normal = painterly, front layers cover back ones
OPACITY   = 0.08         # per layer; lower it if the stack blows out to white
DEPTH     = 0.6          # thickness of the stack, in painting widths
REVERSE   = False        # True = first frame at the back instead of the front
# ------------------------------------------

EXT = 'png' if KEY == 'alpha' else 'jpg'
_state = {'rec': False, 'n': 0}

def G():
    return op(GALLERY).module

def _tmp():
    return os.path.join(project.folder, '_layers_take')

def toggle():
    finish() if _state['rec'] else start()

def start():
    if _state['rec']:
        return
    shutil.rmtree(_tmp(), ignore_errors=True)
    os.makedirs(_tmp())
    _state.update(rec=True, n=0)
    G().set_status('recording', frames=0)
    print('recording layers…')

def onFrameEnd(frame):
    G().tick()
    if not _state['rec'] or int(absTime.frame) % EVERY:
        return
    op(SRC_TOP).save(os.path.join(_tmp(), 'f_%05d.%s' % (_state['n'], EXT)))
    _state['n'] += 1
    G().status['frames'] = _state['n']

def cancel():
    _state['rec'] = False
    shutil.rmtree(_tmp(), ignore_errors=True)
    G().set_status('idle')
    print('take discarded')

def finish():
    if not _state['rec']:
        return
    _state['rec'] = False
    G().set_status('shaping', frames=_state['n'])
    G().defer(_shape, 3)          # let the monitor show "shaping" before the heavy file work

def _shape():
    g = G()
    frames = sorted(f for f in os.listdir(_tmp()) if f.startswith('f_')) if os.path.isdir(_tmp()) else []
    if len(frames) < 2:
        print('nothing recorded - check SRC_TOP'); g.set_status('idle'); return
    if len(frames) > MAX:                                   # keep MAX evenly spaced frames
        step = (len(frames) - 1) / (MAX - 1)
        frames = [frames[round(i * step)] for i in range(MAX)]

    pid, folder = g.new_painting()
    names = []
    for i, f in enumerate(frames):
        name = 'layer_%04d.%s' % (i, EXT)
        shutil.move(os.path.join(_tmp(), f), os.path.join(folder, name))
        names.append(name)
    shutil.rmtree(_tmp(), ignore_errors=True)

    thumb = op(THUMB_TOP) if THUMB_TOP else None
    if thumb is not None:
        thumb.save(os.path.join(folder, 'thumb.jpg')); thumb_name = 'thumb.jpg'
    else:
        thumb_name = names[len(names) // 2]

    with open(os.path.join(folder, 'manifest.json'), 'w') as fh:
        json.dump({'files': names, 'depth': DEPTH, 'key': KEY, 'blending': BLENDING,
                   'opacity': OPACITY, 'reverse': REVERSE}, fh, indent=2)
    g.add_painting(pid, 'layers', thumb_name)
