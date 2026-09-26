# Sound Paintings website

- index.html    gallery, where the QR code leads (phones)
- view.html     3D viewer for skin paintings    (view.html?p=<id>)
- layers.html   3D viewer for image-stack paintings (layers.html?p=<id>)
- display.html  full-screen page for the gallery monitor: newest painting + QR code, switches by itself
- config.json   title, subtitle, and the gallery web address the QR points to
- paintings/    one folder per painting + index.json (the list)
- td/layers/    TouchDesigner: record a TOP as stacked layers
- td/skin/      TouchDesigner: record deformed circle geometry as a skin
- tools/        image-stack publisher from exported files + printable QR

## One-time setup
1. github.com -> New repository -> name it makers-marks (Public).
2. Install GitHub Desktop, sign in, "Add existing repository" (or clone the new one) and copy
   everything from this zip into it. Commit + Push.
   GitHub Desktop also sets up git + your login so TouchDesigner can push.
3. On github.com: repo -> Settings -> Pages -> Source: Deploy from a branch -> main, / (root) -> Save.
   Your address: https://YOUR-NAME.github.io/makers-marks/
4. Put that address in config.json ("galleryUrl"), commit + push.

## In TouchDesigner (two script sets: use whichever patch is live)
Both need REPO set to your local repo folder, e.g. 'C:/Users/you/Documents/GitHub/makers-marks'.

### A. Layers: records your painting TOP  (td/layers/td_layers.py)
1. Execute DAT named 'layers', paste td_layers.py, turn on Frame End.
2. SRC_TOP = the TOP to record. Put a Fit TOP (1024 on the long side) after your painting so saving stays fast.
3. op('layers').module.start()   ...perform...   op('layers').module.finish('optional title')
   It keeps ~80 evenly spaced frames, saves them + a thumbnail into paintings/, updates the list and pushes.
   cancel() throws a take away, push() retries an upload.

### B. Sound Skin: records the audio-deformed circle geometry  (td/skin/)
1. Execute DAT named 'execute1' with td_skin_recorder.py (Frame End on). Set SOP, INSTANCE, and COLOR (a CHOP with r g b, or everything is white).
2. Constant CHOP named 'rec', channel 'record'.
3. Text DAT named 'publish' with td_publish.py. Set THUMB_TOP to a Fit TOP (600x600) after your feedback painting.
4. op('publish').module.start()   ...perform...   op('publish').module.finish('optional title')

Either way the site updates about a minute later. If the wifi is down, the painting is still saved
locally; run push() later to upload it. Both kinds show up in the same gallery.

## The monitor
In a terminal in the repo folder:  python -m http.server 8000
Open http://localhost:8000/display.html in Chrome and press F for full screen
(or start Chrome with --kiosk http://localhost:8000/display.html).
It reads the paintings on this computer, so it updates instantly and works offline.

## Image-stack paintings (optional)
python tools/prepare_layers.py path/to/frames --title "..." --push      (pip install pillow)
Printable QR:  python tools/prepare_layers.py --qr https://YOUR-NAME.github.io/makers-marks/
