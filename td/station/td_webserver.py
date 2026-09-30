# TouchDesigner WEB SERVER  -  the monitor page talks to TouchDesigner through this.
# 1. Add a Web Server DAT. Port: 9980. Active: On.
# 2. Replace the text of its callbacks DAT (webserver1_callbacks) with this file.
#
#   GET  /api/status   -> what's happening now (recording / shaping / naming / uploading / done)
#   POST /api/name     -> {"name": "..."} names the painting that just finished

import json

GALLERY = 'gallery'   # the Text DAT with td_gallery.py

def _send(response, obj, code=200):
    response['statusCode'] = code
    response['statusReason'] = 'OK' if code == 200 else 'Error'
    response['content-type'] = 'application/json'
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Headers'] = '*'
    response['Cache-Control'] = 'no-store'
    response['data'] = json.dumps(obj)
    return response

def onHTTPRequest(webServerDAT, request, response):
    g = op(GALLERY).module
    uri = str(request.get('uri', '')).split('?')[0].rstrip('/')
    method = str(request.get('method', 'GET')).upper()
    if method == 'OPTIONS':
        return _send(response, {})
    if uri.endswith('/api/status'):
        return _send(response, g.get_status())
    if uri.endswith('/api/name') and method == 'POST':
        body = request.get('data', '')
        if isinstance(body, (bytes, bytearray)):
            body = body.decode('utf-8', 'replace')
        try:
            name = json.loads(body).get('name', '')
        except Exception:
            name = body
        ok = g.set_name(name)
        return _send(response, dict(g.get_status(), ok=ok))
    return _send(response, {'error': 'not found'}, 404)

def onWebSocketOpen(webServerDAT, client, uri):
    return
def onWebSocketClose(webServerDAT, client):
    return
def onWebSocketReceiveText(webServerDAT, client, data):
    return
def onWebSocketReceiveBinary(webServerDAT, client, data):
    return
def onWebSocketReceivePing(webServerDAT, client, data):
    webServerDAT.webSocketSendPong(client, data=data)
    return
def onWebSocketReceivePong(webServerDAT, client, data):
    return
def onServerStart(webServerDAT):
    return
def onServerStop(webServerDAT):
    return
