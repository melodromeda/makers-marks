# Makers Marks website

- index.html    the gallery. On phones: pages of live 3D previews. On the installation monitor it also shows
                the QR code and the status / "Name your painting!" block (it talks to TouchDesigner).
- view.html     full viewer for skin paintings    (view.html?p=<id>)
- layers.html   full viewer for layer paintings   (layers.html?p=<id>)
- config.json   title, subtitle, galleryUrl (where the QR points), stationUrl (TouchDesigner web server)
- paintings/    one folder per painting + index.json (the list)
- td/station/   TouchDesigner: gallery status + naming + upload, and the web server for the monitor
- td/layers/    TouchDesigner: record a TOP as stacked layers
- td/skin/      TouchDesigner: record deformed circle geometry as a skin
- tools/        publish already-exported frames + printable QR

## One-time GitHub setup
1. Repo makers-marks (Public), cloned with GitHub Desktop, these files copied in, Commit + Push.
2. Settings -> Pages -> Deploy from a branch -> main, / (root).
3. config.json: "galleryUrl": "https://YOUR-NAME.github.io/makers-marks/"
4. Command-line git must be installed and signed in (Git for Windows, then one `git push` in a terminal).

## TouchDesigner (put every DAT in the same network, e.g. /project1)
Always:
1. Text DAT named 'gallery'  <- td/station/td_gallery.py. Set REPO (keep the r in front of the quote).
2. Web Server DAT, Port 9980, Active on. Paste td/station/td_webserver.py into its callbacks DAT.

Then whichever patch is live:
- Layers: Execute DAT named 'layers' <- td/layers/td_layers.py, Frame End on. SRC_TOP = a Fit TOP (512) after your painting.
  Button: op('/project1/layers').module.toggle()
- Skin: Execute DAT 'execute1' <- td/skin/td_skin_recorder.py (Frame End on), Constant CHOP 'rec' (channel 'record'),
  Text DAT 'publish' <- td/skin/td_publish.py.
  Button: op('/project1/publish').module.toggle()

MIDI button (CHOP Execute DAT on your Select CHOP, Off to On only):
    import time
    _last = [0.0]
    def onOffToOn(channel, sampleIndex, val, prev):
        if time.time() - _last[0] < 0.5: return
        _last[0] = time.time()
        op('/project1/layers').module.toggle()      # or /project1/publish for the skin set

What happens: press -> recording -> press -> shaping -> the monitor asks "Name your painting!" ->
name + Enter (or 60 s passes and it goes up untitled) -> uploading -> in the gallery.
Fix a name later:        op('/project1/gallery').module.rename('<painting id>', 'New name')
Take one off the site:   op('/project1/gallery').module.hide('<painting id>')
Retry a failed upload:   op('/project1/gallery').module.push()

## The monitor
In a terminal in the repo folder:  python -m http.server 8000
Open http://localhost:8000/ in Chrome, full screen (F11) or: chrome --kiosk http://localhost:8000/
Needs a keyboard for naming. Arrow keys / buttons flip pages; it flips on its own when nobody's using it.
Clicking a painting opens it; the monitor comes back to the gallery after 90 s, or as soon as a new recording starts.
