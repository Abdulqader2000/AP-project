import vs_utils as vs
import os
import re
from random import choice


def safe_input(prompt:str, possibilities:list):
    while True:
        try:    
            pressed = input(prompt)
        except UnicodeDecodeError:
            continue
        if pressed in possibilities:
            return pressed
        else: 
            print('Invalid!')

def ip_input(prompt:str):
    while True:
        ip = input(prompt).strip()
        if re.fullmatch(r'^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}$', ip):
            return ip
        print('invalid ip address')

def port_input(prompt:str):
    while True:
        port = input(prompt).strip()
        if port.isnumeric():
            return int(port)
        print('port number consist only of numbers!')




def main():
    
    mode = safe_input('choose a video streaming mode:\n(1) Broadcasting mode\n(2) carrier mode\n', ['1', '2'])
    capture_from = 0
    
    if mode == '1':
        files = list(os.scandir('videos'))
        if files:
            on_demand = safe_input('choose (1) live or (2) on-demand: ', ['1', '2'])
        else:
            on_demand = '1'
        
        if on_demand == '2':
            print('choose from the list:')
            for index, file in enumerate(files, start=1):
                print(f'{index}- {file.name}')
                
            file_index = int(safe_input('', list(str(i) for i in range(1, len(files) + 1)))) - 1
            capture_from = files[file_index].path
            
        try:
            broadcaster = vs.Broadcaster(vs.DEFAULT_IP, vs.DEFAULT_PORT, capture_from)
        except OSError:
            print('the server already running')
            exit()

        broadcaster.start()
        print('running...')
        if safe_input('Entern (q) to stop: ', ['q']):
            broadcaster.stop()
            print('closed')


    elif mode == '2':
        while True:
            host = ip_input('Enter server IP address: ')
            port = port_input('Enter server port number: ')
            
            try:
                carrier = vs.Carier(host, port)
            except ConnectionRefusedError:
                if safe_input('Can\'t connect.\n Enter (1) to try again with differnt IP/port numbers (2) to exit: ', ['1', '2']) == '1':
                    continue
                else: 
                    exit()

            start =  carrier.start()
            if start:
                print('the sever is full, you car try connect to one of these clints:')
                for client in start:
                    print(f'- {client["ip"]}/{client["port"]}')
            else:
                break

        # if safe_input('Entern (q) to stop', ['q']):
        #     carrier.stop()
        #     print('closed')
        print('press (q) on window to stop')


if __name__ == '__main__':
    main()