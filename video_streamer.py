import threading
import json
import vs_utils as vs
import socket

mode = input(
    'choose a video streaming mode:\n(1) Broadcasting mode\n(2) carrier mode\n')

if mode == '1':

    broadcaster = vs.Broadcaster()
    broadcaster.socket

    while True:
        client = broadcaster.socket.accept()
        thread = threading.Thread(
            target=vs.handle_requests, args=(broadcaster, client))
        thread.start()

elif mode == '2':
    host, port = input('enter the server IP/port: ').strip().split('/')

    # carier = vs.Carier(host, port)
    socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket.connect((host, int(port)))

    vs.handle_responses(socket)
