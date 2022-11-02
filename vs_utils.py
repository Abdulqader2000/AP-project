"""
Utility module that makes project-specific functions/classes/variables easy to access
This is not required.
"""

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
RESPONSE = "response"
REQUEST = "request"
DATA = "data"
STREAMING_MODE = "streamingmode"
BROADCASTING = "broadcasting"
CARRIER = "carrier"

# continoue the list ...


# functions ...
def broadcast(connection):
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
        # Make a resolution of 320 by 240 pixels. 3 bytes per pixel
        resized_frame = cv.resize(
            frame, (RESOLUTION_WIDTH, RESOLUTION_HEIGHT))
        # Get the raw bytes of the frame
        raw_image_bytes = resized_frame.tobytes()
        # Compress the frame(image) using GZIP algorithm
        compressed_image = gzip.compress(raw_image_bytes)
        # Encode to Base64
        encoded_base64_image = base64.b64encode(compressed_image)
        # Note: You may need to convert bytes to str and use the image data in JSON format, use the following line:
        image_str = encoded_base64_image.decode()
        connection.sendall((json.dumps(image_str) + '\n').encode())
        time.sleep(.1)

    cap.release()
    cv.destroyAllWindows()


def cary(socket):
    while True:
        image_str = ''
        while not image_str.endswith('\n'):
            image_str += socket.recv(1024).decode()

        encoded_base64_image = image_str.strip().encode()
        # Remove the base64 encoding
        decoded_base64_image = base64.b64decode(encoded_base64_image)
        # Decompress the image data
        decompressed_image = gzip.decompress(decoded_base64_image)
        # Convert the raw bytes to make a frame (type is ndarray)
        frm = np.frombuffer(decompressed_image, dtype='uint8')
        # Reshare the ndarray of frame properly e.g. 320 by 240, 3 bytes
        # if len(frm) != 230400:
        try:
            frm = frm.reshape(RESOLUTION_HEIGHT,
                              RESOLUTION_WIDTH, BYTES_PER_PIXEL)
        except ValueError:
            pass

        cv.imshow('Frame', frm)
        # To quit, press q
        if cv.waitKey(1) == ord('q'):
            break

    cv.destroyAllWindows()


def handle_client(broadcaster, client):
    connection, address = broadcaster.socket.accept()
    status_response = {
        RESPONSE: "status",
        STREAMING_MODE: BROADCASTING,
        "nclients": len(broadcaster.clients),
        "handover": "no"
    }
    connection.sendall(json.dumps(status_response).encode())

    streamStart_request = json.loads(connection.recv(1024).decode())
    if streamStart_request[REQUEST] == 'streamstarting':
        if len(broadcaster.clients) < 3:  # TODO
            connection.sendall(json.dumps({RESPONSE: BROADCASTING}
                                          ).encode())
            broadcaster.clients.append(client)
        else:
            connection.sendall(json.dumps({RESPONSE: "overloaded"}
                                          ).encode())
            exit()

    thread = threading.Thread(target=broadcast, args=(connection,))

    thread.start()

    StreamStop_Requeststop = json.loads(connection.recv(1024).decode())

    if StreamStop_Requeststop[REQUEST] == 'streamstop':
        pass

    # classess...


class Broadcaster:
    def __init__(self):
        HOST = "0.0.0.0"
        PORT = 5002
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((HOST, PORT))
        self.socket.listen()
        self.clients = []


class Carier:
    def __init__(self, HOST, PORT):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((HOST, PORT))
        self.clients = []
