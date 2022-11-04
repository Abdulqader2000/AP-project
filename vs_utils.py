'''
Utility module that makes project-specific functions/classes/variables easy to access
This is not required.
'''

import sys
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



    # classess...


class Broadcaster:
    def __init__(self, host, port):
        # HOST = '0.0.0.0'
        # PORT = 5002
        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # type: ignore
        self.broadcast_socket.bind((host, port))
        self.broadcast_socket.listen()
        self.connections = []
        self.stopped = False
    

    def broadcasting(self):
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
            
            for connection, _ in self.connections:
                connection.sendall((json.dumps(image_response) + '\n').encode())
                
            time.sleep(.1)
            if self.stopped:
                break
            
        cap.release()
        cv.destroyAllWindows()


    def handle_requests(self, connection_with_address):
        connection = connection_with_address[0]

        status_response = {
            RESPONSE: STATUS,
            STREAMING_MODE: BROADCASTING,
            NUMBER_OF_CLIENTS: len(self.connections),
            HANDOVER: 'no'
        }

        connection.sendall(json.dumps(status_response).encode())

        streamStart_request = json.loads(connection.recv(1024).decode())
        if streamStart_request[REQUEST] == STREAM_START:
            if len(self.connections) < 3:
                connection.sendall(json.dumps({RESPONSE: STREAM_STARTING}
                                            ).encode())
                self.connections.append(connection_with_address)
            else:
                connection.sendall(json.dumps({RESPONSE: OVERLOADED}
                                            ).encode())
                exit()
        
        StreamStop_Requeststop = connection.recv(1024)
        StreamStop_Requeststop = json.loads(StreamStop_Requeststop.decode())

        if StreamStop_Requeststop[REQUEST] == STREAM_STOP:
            connection.sendall((json.dumps({RESPONSE: STREAM_STOPPED})+'\n').encode())
            self.connections.remove(connection_with_address)
            connection.close()
            print('closed')
    
    
    def start(self):
        broacasting_thread = threading.Thread(target=self.broadcasting)
        broacasting_thread.start()
        
        while True:
            connection_with_address = self.broadcast_socket.accept()
            handling_request_thread = threading.Thread(
                target=self.handle_requests, args=(connection_with_address,))
            handling_request_thread.start()



class Carier(Broadcaster):
    def __init__(self, HOST, PORT):
        self.carry_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # type: ignore
        self.carry_socket.connect((HOST, PORT))
        self.carry_thread = threading.Thread(target=self.carry)
        self.accept_connections_thread = threading.Thread(target=self.accept_connections)
        
        super().__init__(*self.carry_socket.getsockname())

    def carry(self):
        while True:
            message = ''
            while not message.endswith('\n'):
                message += self.carry_socket.recv(1024).decode()
                
            
            for connection, _ in self.connections:
                connection.sendall(message.encode())

            try:
                message = json.loads(message.strip())
            except:
                continue
            
            if message[RESPONSE] == STREAM_STOPPED:
                cv.destroyAllWindows()
                self.carry_socket.close()
                exit()
            
            image_str = message[DATA]
            
            frm = str_to_frame(image_str)
            
            try:
                cv.imshow('Frame', frm)
            except:
                pass

            # To quit, press q
            if cv.waitKey(1) == ord('q'):
                pass


    def handle_responses(self):
        status_response = json.loads(self.carry_socket.recv(1024).decode())
        self.carry_socket.sendall(json.dumps({REQUEST: STREAM_START}).encode())
        data = self.carry_socket.recv(1024).decode()
        streamstarting_response = json.loads(data)

        if streamstarting_response[RESPONSE] == OVERLOADED:
            print('server is full, try later')
            exit()
        
        self.carry_thread.start()


    def accept_connections(self):
        while True:
            try:
                connection_with_address = self.broadcast_socket.accept()
            except OSError:
                break
            handling_request_thread = threading.Thread(
                target=self.handle_requests, args=(connection_with_address,))
            handling_request_thread.start()


    def start(self):
        self.handle_responses()
        self.accept_connections_thread.start()


    def stop(self):
        self.broadcast_socket.close()
        self.carry_socket.sendall(json.dumps({REQUEST: STREAM_STOP}).encode())