'''
Utility module that makes project-specific functions/classes/variables easy to access
This is not required.
'''

import cv2 as cv
import numpy as np
import gzip
import base64
import socket
import json
import time
import threading


# Resolution: 320x240
RESOLUTION_WIDTH = 320
RESOLUTION_HEIGHT = 240
BYTES_PER_PIXEL = 3

# Messages
RESPONSE = 'response'
REQUEST = 'request'
DATA = 'data'
STREAMING_MODE = 'streamingmode'
BROADCASTING = 'broadcasting'
CARRIER = 'carrier'
STREAM_STOP = 'streamstop'
STREAM_STOPPED = '"streamstopped'
STATUS = 'status'
NUMBER_OF_CLIENTS = 'nclients'
HANDOVER = 'handover'
STREAM_START = 'streamstart'
STREAM_STARTING = 'streamstarting'
OVERLOADED = 'overloaded'
IMAGE = 'image'

# continoue the list ...


# functions ...

def frame_to_str(frame):
    resized_frame = cv.resize(
        frame, (320, 240))
    # Get the raw bytes of the frame
    raw_image_bytes = resized_frame.tobytes()
    # Compress the frame(image) using GZIP algorithm
    compressed_image = gzip.compress(raw_image_bytes)
    # Encode to Base64
    encoded_base64_image = base64.b64encode(compressed_image)
    # Note: You may need to convert bytes to str and use the image data in JSON format, use the following line:
    image_str = encoded_base64_image.decode()
    
    return image_str

def str_to_frame(image_str):
    encoded_base64_image = image_str.encode()
    # Remove the base64 encoding
    decoded_base64_image = base64.b64decode(encoded_base64_image)
    # Decompress the image data
    decompressed_image = gzip.decompress(decoded_base64_image)
    # Convert the raw bytes to make a frame (type is ndarray)
    frm = np.frombuffer(decompressed_image, dtype='uint8')
    # Reshare the ndarray of frame properly e.g. 320 by 240, 3 bytes
    frm = frm.reshape(240,
                      320, 3)
    
    return frm


def broadcast(connection, stop):
    cap = cv.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        exit()
        
    while True:
        # Capture frame-by-frame (image-by-image) from the webcam
        ret, frame = cap.read()
        # if frame is read correctly ret is True
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break
        
        image_str = frame_to_str(frame)
        
        image_response = {RESPONSE: IMAGE, DATA: image_str}
        connection.sendall((json.dumps(image_response) + '\n').encode())
        time.sleep(.1)
        if stop:
            break
        
    cap.release()
    cv.destroyAllWindows()


def carry(socket, stop):

    while True:
        image_response = ''
        while not image_response.endswith('\n'):
            image_response += socket.recv(1024).decode()

        image_response = json.loads(image_response.strip())
        image_str = image_response[DATA]

        frm = str_to_frame(image_str)

        cv.imshow('Frame', frm)
        # To quit, press q
        if cv.waitKey(1) == ord('q'):
            break

    cv.destroyAllWindows()


def handle_requests(broadcaster, client):
    connection = client[0]

    status_response = {
        RESPONSE: STATUS,
        STREAMING_MODE: BROADCASTING,
        NUMBER_OF_CLIENTS: len(broadcaster.clients),
        HANDOVER: 'no'
    }
    connection.sendall(json.dumps(status_response).encode())

    streamStart_request = json.loads(connection.recv(1024).decode())
    if streamStart_request[REQUEST] == STREAM_START:
        if len(broadcaster.clients) < 3:  # TODO
            connection.sendall(json.dumps({RESPONSE: STREAM_STARTING}
                                          ).encode())
            broadcaster.clients.append(client[1])
        else:
            connection.sendall(json.dumps({RESPONSE: OVERLOADED}
                                          ).encode())
            exit()

    stop = False
    thread = threading.Thread(target=broadcast, args=(connection, stop))

    thread.start()

    StreamStop_Requeststop = connection.recv(1024)
    StreamStop_Requeststop = json.loads(StreamStop_Requeststop.decode())

    if StreamStop_Requeststop[REQUEST] == STREAM_STOP:
        stop = True
        thread.join()
        connection.sendall(json.dumps({RESPONSE: STREAM_STOPPED}).encode())
        connection.close()


def handle_responses(socket):
    status_response = json.loads(socket.recv(1024).decode())
    socket.sendall(json.dumps({REQUEST: STREAM_START}).encode())
    data = socket.recv(1024).decode()
    streamstarting_response = json.loads(data)

    stop = False
    thread = threading.Thread(target=carry, args=(socket, stop))

    thread.start()

    input('Enter anything to stop streaming: ')

    socket.sendall(json.dumps({REQUEST: STREAM_STOP}).encode())

    stop = True
    thread.join()
    socket.recv(1024)

    socket.close()

    # classess...


class Broadcaster:
    def __init__(self):
        HOST = '0.0.0.0'
        PORT = 5002
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # type: ignore
        self.socket.bind((HOST, PORT))
        self.socket.listen()
        self.clients = []


class Carier:
    def __init__(self, HOST, PORT):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # type: ignore
        self.socket.connect((HOST, PORT))
        self.clients = []



mode = input(
    'choose a video streaming mode:\n(1) Broadcasting mode\n(2) carrier mode\n')

if mode == '1':

    broadcaster = Broadcaster()
    conn, _ = broadcaster.socket.accept()
    broadcast(conn, False)



elif mode == '2':
    host, port = input('enter the server IP/port: ').strip().split('/')

    # carier = vs.Carier(host, port)
    socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket.connect((host, int(port)))

    carry(socket, False)
