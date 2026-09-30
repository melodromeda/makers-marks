# TouchDesigner "skin" recorder  -  paste into an Execute DAT, turn ON "Frame End".
#
# Every frame it grabs the audio-deformed outline of each circle (in world space),
# and when you save it writes two files for skin.html:
#     skin.json  (small header)     skin.bin  (all the points, float32)
#
# ---------------- setup ----------------
# SOP      : the SOP with your deformed circles, AFTER the audio deformation.
#            Each circle should be its own primitive (Circle SOP -> Noise/Point SOP ... is fine,
#            several circles merged/copied into one SOP is also fine).
# INSTANCE : leave '' if the SOP already has the circles where they are in space.
#            If the circles are placed by Geometry COMP instancing, put the instance CHOP here
#            (one sample per circle, channels tx ty tz / rx ry rz / sx sy sz or scale, optional r g b).
#            The one deformed SOP is then copied to every instance position.
# COLOR    : optional CHOP with channels r g b (one sample per circle, or one sample for all).
# REC      : Constant CHOP with a channel 'record'. Set to 1 to record, 0 to stop.
#
# When finished, in the Textport:
#     op('execute1').module.save()      # writes skin.json + skin.bin next to your .toe
#   (normally td_publish.py does record -> save -> name -> upload for you)
#     op('execute1').module.clear()     # start over
# ----------------------------------------

import json, math, array

SOP      = 'deformed_circles'
INSTANCE = ''
COLOR    = ''
REC      = 'rec'
POINTS   = 96     # every outline is resampled to this many points (keeps the skin clean)
EVERY    = 1      # record every Nth frame

_frames = []      # list of frames; each frame = list of circles; each circle = flat [x,y,z,...]
_colors = []      # per frame, per circle [r,g,b]

def _resample(pts, n):
    """evenly resample a closed loop of (x,y,z) to n points"""
    if len(pts) < 2:
        return (pts * n)[:n]
    loop = pts + [pts[0]]
    seg = [math.dist(loop[i], loop[i + 1]) for i in range(len(pts))]
    total = sum(seg) or 1.0
    out, i, acc = [], 0, 0.0
    for k in range(n):
        target = total * k / n
        while i < len(seg) - 1 and acc + seg[i] < target:
            acc += seg[i]; i += 1
        t = (target - acc) / seg[i] if seg[i] else 0
        a, b = loop[i], loop[i + 1]
        out.append(tuple(a[j] + (b[j] - a[j]) * t for j in range(3)))
    return out

def _xform(p, inst, i):
    """apply TouchDesigner-style instance transform (scale, rotate XYZ in degrees, translate)"""
    def c(name, d=0.0):
        ch = inst.chan(name)
        return ch[i] if ch is not None else d
    s = c('scale', 1.0)
    sx, sy, sz = c('sx', s), c('sy', s), c('sz', s)
    x, y, z = p[0] * sx, p[1] * sy, p[2] * sz
    for axis in ('rx', 'ry', 'rz'):
        a = math.radians(c(axis))
        ca, sa = math.cos(a), math.sin(a)
        if axis == 'rx': y, z = y * ca - z * sa, y * sa + z * ca
        if axis == 'ry': x, z = x * ca + z * sa, -x * sa + z * ca
        if axis == 'rz': x, y = x * ca - y * sa, x * sa + y * ca
    return (x + c('tx'), y + c('ty'), z + c('tz'))

def _color(chop, i):
    if chop is None:
        return [1.0, 1.0, 1.0]
    j = min(i, chop.numSamples - 1)
    return [chop[c][j] if chop.chan(c) is not None else 1.0 for c in ('r', 'g', 'b')]

GALLERY  = 'gallery'   # Text DAT with td_gallery.py (status + naming)

def onFrameEnd(frame):
    g = op(GALLERY)
    if g is not None:
        g.module.tick()
        if g.module.status['state'] == 'recording':
            g.module.status['frames'] = len(_frames)
    rec = op(REC)
    if rec is None or rec['record'] is None or rec['record'].eval() < 0.5:
        return
    if int(absTime.frame) % EVERY:
        return
    sop = op(SOP)
    loops = []
    for prim in sop.prims:
        pts = [(v.point.P[0], v.point.P[1], v.point.P[2]) for v in prim]
        if len(pts) >= 3:
            loops.append(_resample(pts, POINTS))
    inst = op(INSTANCE) if INSTANCE else None
    col = op(COLOR) if COLOR else inst
    circles, colors = [], []
    if inst is not None:
        base = loops[0] if loops else []
        for i in range(inst.numSamples):
            circles.append([v for p in base for v in _xform(p, inst, i)])
            colors.append(_color(col, i))
    else:
        for i, loop in enumerate(loops):
            circles.append([v for p in loop for v in p])
            colors.append(_color(col, i))
    _frames.append(circles)
    _colors.append(colors)

def save(base=None):
    """write <base>.json + <base>.bin  (base defaults to <project folder>/skin). Returns True on success."""
    if not _frames:
        print('nothing recorded'); return False
    nc = min(len(f) for f in _frames)            # circles present in every frame
    if nc == 0:
        print('recorded frames had no circles - check SOP name'); return False
    data, cols = array.array('f'), array.array('f')
    for f, c in zip(_frames, _colors):
        for i in range(nc):
            data.extend(f[i]); cols.extend(c[i])
    base = base or (project.folder + '/skin')
    with open(base + '.bin', 'wb') as fh:
        data.tofile(fh); cols.tofile(fh)
    with open(base + '.json', 'w') as fh:
        json.dump({'frames': len(_frames), 'circles': nc, 'points': POINTS, 'fps': project.cookRate / EVERY}, fh)
    print('wrote', base + '.json/.bin :', len(_frames), 'frames,', nc, 'circles')
    return True

def clear():
    _frames.clear(); _colors.clear()
