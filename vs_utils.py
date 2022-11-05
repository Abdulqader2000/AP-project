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
from threading import Thread
from datetime import datetime
import time


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
CLIENTS = 'clients'
SERVER = 'sever'

# addresses 
DEFAULT_IP = '0.0.0.0'
DEFAULT_PORT = 9191


# functions ...

def frame_to_str(frame):
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
    frm = frm.reshape(RESOLUTION_HEIGHT,
                      RESOLUTION_WIDTH, BYTES_PER_PIXEL)
    
    return frm

def send_with_newline(sender:socket.socket, message:dict):
    sender.sendall((json.dumps(message)+'\n').encode())
    
def receive_with_newline(receiver:socket.socket):
    str_message = ''
    while not str_message.endswith('\n'):
        str_message += receiver.recv(1024).decode()
    return json.loads(str_message[:-1])




    # classess...

class Broadcaster:
    def __init__(self, host, port, capture_from, mode=BROADCASTING):
        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.broadcast_socket.bind((host, port))
        self.broadcast_socket.listen()
        self.connections = []
        self.broacasting_thread = Thread(target=self.broadcasting)
        self.accept_connections_thread = Thread(target=self.accept_connections)
        self.capture_from = capture_from
        self.mode = mode
        self.stopped = False 


    def broadcasting(self):
        cap = cv.VideoCapture(self.capture_from)
        fourcc = cv.VideoWriter_fourcc(*'XVID')
        record = cv.VideoWriter(f'videos/{datetime.now().strftime(r"%m-%d-%Y_%H&%M")}.avi', fourcc, 20.0, (640,  480))

        if not cap.isOpened():
            Thread(target=self.stop).start()
            exit()
            
        while True:
            ret, frame = cap.read()
            if not ret:
                cap = cv.VideoCapture(self.capture_from)
                continue
            
            if self.capture_from:
                resized_frame = cv.resize(
        frame, (RESOLUTION_WIDTH, RESOLUTION_HEIGHT))
                cv.imshow('Frame', resized_frame)
                if cv.waitKey(1) == ord('q'):
                    Thread(target=self.stop).start()
            else:
                record.write(frame)
            
            image_str = frame_to_str(frame)
            
            image_response = {RESPONSE: IMAGE, DATA: image_str}
            
            for connection, _ in self.connections:
                try:
                    send_with_newline(connection, image_response)
                except ConnectionResetError:
                    continue
                
            time.sleep(.1)
            
            if self.stopped:
                break
            
        cap.release()
        record.release()
    
        cv.destroyAllWindows()


    def handle_requests(self, connection_with_address):
        connection = connection_with_address[0]

        status_response = {
            RESPONSE: STATUS,
            STREAMING_MODE: self.mode,
            NUMBER_OF_CLIENTS: len(self.connections),
            HANDOVER: 'yes'
        }

        send_with_newline(connection, status_response)
        
        streamstart_request = receive_with_newline(connection)
        
        if len(self.connections) < 3:
            streamstarting_response = {RESPONSE: STREAM_STARTING}
            send_with_newline(connection, streamstarting_response)
            self.connections.append(connection_with_address)
        else:
            overloaded_response = {RESPONSE: OVERLOADED, CLIENTS: [{'ip': client[1][0], 'port': client[1][1]} for client in self.connections]}
            if self.mode == CARRIER:
                address = self.broadcast_socket.getsockname()
                overloaded_response |= {'server': {'ip': address[0], 'port': address[1]}}
            send_with_newline(connection, overloaded_response)
            exit()
        

        try:
            streamstop_requeststop = receive_with_newline(connection)
        except ConnectionResetError:
            self.connections.remove(connection_with_address)
            exit()
        except (ConnectionAbortedError, OSError):
            exit()

        
        streamstopped_response = {RESPONSE: STREAM_STOPPED}
        send_with_newline(connection, streamstopped_response)
        self.connections.remove(connection_with_address)
        connection.close()
    
    def accept_connections(self):
        while True:
            try:
                connection_with_address = self.broadcast_socket.accept()
            except OSError:
                break
            handling_request_thread = Thread(
                target=self.handle_requests, args=(connection_with_address,))
            handling_request_thread.start()
    
    
    def start(self):
        self.broacasting_thread.start()
        self.accept_connections_thread.start()
    
    def stop(self):
        self.stopped = True
        self.broacasting_thread.join()
        streamstopped_response = {RESPONSE: STREAM_STOPPED}
        for connection, _ in self.connections:
            send_with_newline(connection, streamstopped_response)
            connection.close()
        self.broadcast_socket.close()



class Carier(Broadcaster):
    def __init__(self, HOST, PORT):
        self.carry_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # type: ignore
        self.carry_socket.connect((HOST, PORT))
        self.carry_thread = Thread(target=self.carry)
        
        super().__init__(*self.carry_socket.getsockname(), mode=CARRIER, capture_from=None)


    def carry(self):
        while True:
            
            try:
                message = receive_with_newline(self.carry_socket)
            except ConnectionResetError:
                message = {RESPONSE: STREAM_STOPPED}
            except json.decoder.JSONDecodeError:
                continue

            
            for connection, _ in self.connections:
                send_with_newline(connection, message)

            
            if message[RESPONSE] == STREAM_STOPPED:
                break
            
            image_str = message[DATA]
            
            frm = str_to_frame(image_str)
            
            try:
                cv.imshow('Frame', frm)
            except:
                pass

            if cv.waitKey(1) == ord('q'):
                self.stopped = True
                streamstop_request = {REQUEST: STREAM_STOP}
                send_with_newline(self.carry_socket, streamstop_request)
            
        cv.destroyAllWindows()
        for connection, _ in self.connections:
            connection.close()
        self.carry_socket.close()
        self.broadcast_socket.close()
        if not self.stopped:
            print('the server stopped')



    def handle_responses(self):
        status_response = receive_with_newline(self.carry_socket)
        streamstart_request = {REQUEST: STREAM_START}
        send_with_newline(self.carry_socket, streamstart_request)
        
        streamstarting_response = receive_with_newline(self.carry_socket)
        return streamstarting_response


    def start(self):
        streamstarting_response = self.handle_responses()
        if streamstarting_response[RESPONSE] == OVERLOADED:
            return streamstarting_response[CLIENTS]

        self.carry_thread.start()
        self.accept_connections_thread.start()
