#Client side chat app
#Author: Brodie McCuen
#21 December 2022

import socket
import datetime
import threading
import subprocess


# Create a TCP/IP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

HEADER_LENGTH = 64
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = '!DISCONNECT'
SERVER_PORT = 10000
# SERVER_IP changed 
SERVER_IP = '[insert server ip here]'


def get_wifi():
    wifi = subprocess.check_output(['netsh', 'WLAN', 'show', 'interfaces'])
    data = wifi.decode('utf-8')
    data = data.split('\n')

    # parses through the lines and finds SSID to get the ssid
    for line in data:
        new_line = line.strip()
        if new_line.startswith("SSID"):
            index = new_line.rfind(' ') + 1
            ssid = new_line[index:]

            return ssid

    return 'No Wifi Found'

# only prints the date if 5 minutes apart
def date_logic(previous_date, date):
    if previous_date != '':
        # converst date and previous date to datetime format
        new_date = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        previous_date = datetime.datetime.strptime(previous_date, '%Y-%m-%d %H:%M:%S')
        elapsed = new_date - previous_date
        duration_in_s = elapsed.total_seconds()
        minutes = divmod(duration_in_s, 60)[0]

        if minutes > 5:
            print(date)

    if date != '':
        previous_date = date

# extra function 
def find_match(expected_messages, message):
    for key in expected_messages:
        if message.find(key) != -1:
            return True
    return False

def parse_message(message):
    '''
    Only recieves message in the format \'name: date!body\'
    '''
    message = message.strip()
    # the indeces of the parts of the message
    date_index = message.find(' ')
    message_index = message.find('!', date_index) + 1

    name = message[0:date_index]
    date = message[date_index+1: message_index-1] # the 1's are here to remove white space and exclaimation mark
    body = message[message_index:]

    return name, date, body

# adds the date and time to the message
# doesn't send messages that aren't zero
def send_message(msg, client_socket):
    
    dt = datetime.datetime.now()
    current_time = dt.strftime("%Y-%m-%d %H:%M:%S") # removes milliseconds
    # '!' here to easily find the start of the message in the string
    message = str(current_time) + '!' + msg
    message = message.encode(FORMAT)

    # don't send messages that are empty
    if len(message) > 0:
        client_socket.send(message)

# handle different messages depending on their type
def receive(client_socket, nickname):
    previous_date = ''
    # certain messages are sent by the server than dont need to be parsed
    # extra server messages need to be added to expected_messages
    expected_messages = ['Connected to the server', 
                         'has joined the chat', 
                         'has left the chat',
                         'Creating new chat room',
                         'has disconnected',
                         'No existing chats on your wifi',
                         'Existing chats on your wifi are ']

    while True:
        try:
            # message will only be in the type of a string
            message = client_socket.recv(1024).decode(FORMAT)
            if len(message) > 0:
                # print("MESSAGE: ", message)
                
                if message == 'Nick: ':
                    client_socket.send(nickname.encode(FORMAT))
                    wifi_name = get_wifi()
                    client_socket.send(wifi_name.encode(FORMAT))
                    
                elif message == 'Chat name: ':
                    chat_room = input("What is the chatroom?: ")
                    client_socket.send(chat_room.encode(FORMAT))
                    # thread starts here as I only write once I enter a chat room
                    write_thread = threading.Thread(target=write, args=(client_socket,))
                    write_thread.start()
                
                # all of the other messages 
                else:
                    # some messages are sent more than one at a time, so they are split
                    message_lines = message.split('\n')
                    # strip whitespace
                    while '' in message_lines:
                        message_lines.remove('')

                    for msg in message_lines:
                        # message is expected
                        if find_match(expected_messages, msg):
                            print(msg)
                        # message is a broadcast message
                        else:
                            name, date, body = parse_message(msg)

                            date_logic(previous_date, date)
                        
                            print(f"{name} {body}")

                
                    # messages from a text file will be sent in a block sperated by '\n'

        except:
            print("An error occurred")
            client_socket.close()
            break


# main loop to write messages for server
def write(client_socket):
    # msg = input("Enter your message (Type 'quit' to exit)\n")

    msg = input("Enter your message or type 'quit' to exit: \n")
    while msg != 'quit':
        send_message(msg, client_socket)
        msg = input("\n")
        
    client_socket.send(DISCONNECT_MESSAGE.encode(FORMAT))
    client_socket.close()
    print("[EXIT] Sending disconnect request to server")


def start_client():
    
    nickname = input("Put in a nickname: ")
    
    # spaces mess with the message parsing protocol
    while nickname.find(' ') != -1:
        nickname = input("Invalid nickname, try again: ")

    server_address = (SERVER_IP, SERVER_PORT)
    print ('connecting to %s port %s' % server_address)
    client_socket.connect(server_address)
    
    cond = threading.Condition()
    # Two Threads: one to deal with inputs and one to deal with server messages
    receive_thread = threading.Thread(target=receive, args=(client_socket, nickname))
    receive_thread.start()


start_client()