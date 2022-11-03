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
def broadcast(connection, stop):
    cap = cv.VideoCapture(0)
    if not cap.isOpened():
        print('Cannot open camera')
        exit()

    fourcc = cv.VideoWriter_fourcc(*'XVID')
    out = cv.VideoWriter('output.avi', fourcc, 20.0, (640,  480))

    counter = 0

    try:
        while True:

            # Capture frame-by-frame (image-by-image) from the webcam
            ret, frame = cap.read()

            out.write(frame)
            # if frame is read correctly ret is True
            if not ret:
                print('Can\'t receive frame(stream end?). Exiting ...')
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

            if counter < 600:
                with open('test2.txt', 'a') as f:
                    f.write(image_str)
            counter += 1

            image_response = {RESPONSE: IMAGE, DATA: image_str}
            connection.sendall((json.dumps(image_response) + '\n').encode())
            time.sleep(.1)
            if stop:
                break

    except:
        pass

    out.release()
    cap.release()
    # cv.destroyAllWindows()


def carry(socket, stop):

    counter = 0
    while True:
        image_response = ''
        while not image_response.endswith('\n'):
            image_response += socket.recv(1024).decode()

        image_response = json.loads(image_response.strip())
        image_str = image_response[DATA]

        if counter < 600:
            with open('test1.txt', 'a') as f:
                f.write(image_str)
        else:
            print('done')
        counter += 1

        encoded_base64_image = image_str.encode()
        # Remove the base64 encoding
        decoded_base64_image = base64.b64decode(encoded_base64_image)
        # Decompress the image data
        decompressed_image = gzip.decompress(decoded_base64_image)
        # Convert the raw bytes to make a frame (type is ndarray)
        frm = np.frombuffer(decompressed_image, dtype='uint8')
        # Reshare the ndarray of frame properly e.g. 320 by 240, 3 bytes
        # if len(frm) != 230400:
        # try:
        frm = frm.reshape(RESOLUTION_HEIGHT,
                          RESOLUTION_WIDTH, BYTES_PER_PIXEL)
        # except ValueError:
        #     print('nop')

        cv.imshow('Frame', frm)
        # To quit, press q
        # if stop:
        #     break

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
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((HOST, PORT))
        self.socket.listen()
        self.clients = []


class Carier:
    def __init__(self, HOST, PORT):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((HOST, PORT))
        self.clients = []
