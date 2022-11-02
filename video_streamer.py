import threading
import json
import vs_utils as vs
import socket

mode = input(
    'choose a video streaming mode:\n(1) Broadcasting mode\n(2) carrier mode\n')

if mode == '1':

    broadcaster = vs.Broadcaster()
    socket = broadcaster.socket

    connection, address = socket.accept()
    status_response = {
        "response": "status",
        "streamingmode": "broadcasting",
        "nclients": 0,
        "handover": "no"
    }
    connection.sendall(json.dumps(status_response).encode())

    streamStart_request = json.loads(connection.recv(1024).decode())
    print(streamStart_request)
    if streamStart_request['request'] == 'streamstarting':
        if 1 < 3:  # TODO
            connection.sendall(json.dumps({"response": "streamstarting"}
                                          ).encode())
        else:
            connection.sendall(json.dumps({"response": "overloaded"}
                                          ).encode())
            exit()

    vs.broadcast(connection)


elif mode == '2':
    host, port = input('enter the server IP/port: ').strip().split('/')

    carier = vs.Carier(host, port)
    socket = carier.socket
    socket.connect((host, int(port)))

    status_response = json.loads(socket.recv(1024).decode())
    socket.sendall(json.dumps({"request": "streamstarting"}).encode())
    data = socket.recv(1024).decode()
    streamstarting_response = json.loads(data)

    vs.cary(socket)
