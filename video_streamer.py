import threading
import json
import vs_utils as vs
import socket

mode = input(
    'choose a video streaming mode:\n(1) Broadcasting mode\n(2) carrier mode\n')

if mode == '1':

    broadcaster = vs.Broadcaster('127.0.0.1', 5000)
    broadcaster.start()


elif mode == '2':
    host, port = input('enter the server IP/port: ').strip().split('/')

    
    carrier = vs.Carier(host, int(port))
    print(carrier.carry_socket.getsockname())
    carrier.start()
    input('Enter anything to stop: ')
    carrier.stop()