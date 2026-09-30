# TouchDesigner SKIN publisher  -  paste into a Text DAT named 'publish'.
# Works with td_skin_recorder.py (Execute DAT 'execute1') and the 'gallery' Text DAT.
#
#   op('/project1/publish').module.toggle()   # start, or finish if already recording (MIDI button)
#   op('/project1/publish').module.start()
#   op('/project1/publish').module.finish()   # stop -> shape -> monitor asks for a name -> upload
#   op('/project1/publish').module.cancel()

import os

GALLERY   = 'gallery'   # Text DAT with td_gallery.py
RECORDER  = 'execute1'  # Execute DAT running td_skin_recorder.py
REC_CHOP  = 'rec'       # the Constant CHOP with the 'record' channel
THUMB_TOP = 'thumb'     # a TOP to snapshot: e.g. a Fit TOP set to 600x600 after your feedback painting

def G():
    return op(GALLERY).module

def recording():
    return op(REC_CHOP).par.value0.eval() > 0.5

def toggle():
    finish() if recording() else start()

def start():
    op(RECORDER).module.clear()
    op(REC_CHOP).par.value0 = 1
    G().set_status('recording', frames=0)
    print('recording…')

def cancel():
    op(REC_CHOP).par.value0 = 0
    op(RECORDER).module.clear()
    G().set_status('idle')

def finish():
    if not recording():
        return
    op(REC_CHOP).par.value0 = 0
    G().set_status('shaping', frames=len(op(RECORDER).module._frames))
    G().defer(_shape, 3)

def _shape():
    g = G()
    pid, folder = g.new_painting()
    if not op(RECORDER).module.save(os.path.join(folder, 'skin')):
        os.rmdir(folder); g.set_status('idle'); return
    thumb = op(THUMB_TOP)
    if thumb is not None:
        thumb.save(os.path.join(folder, 'thumb.jpg'))
    op(RECORDER).module.clear()
    g.add_painting(pid, 'skin', 'thumb.jpg')
