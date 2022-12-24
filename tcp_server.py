#Server side of chat app
#Author: Devon Hobbs
#21 December 2022

import threading, socket, os

HOST = '[enter host ip here]'
PORT = 10000
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = '!DISCONNECT'

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

clients = []
nicknames = []
chatrooms = []
wifi_ids = {}

# Function will take all the clients in given chat room and
#  send the message to all clients.
def broadcast(chat_name, message):
    indices = find_indices(chatrooms, chat_name)
    for i in indices:
        clients[i].send(message)

# Return all indices which contain a given value in a given list
def find_indices(list_to_search, val_to_find):
    indices = []
    for idx, value in enumerate(list_to_search):
        if value == val_to_find:
            indices.append(idx)
    return indices

def handle(client):
    while True:
        if client in clients:
            index = clients.index(client)
            nickname = nicknames[index]
            chat_name = chatrooms[index]

            message = client.recv(1024).decode(FORMAT)

            if message == DISCONNECT_MESSAGE:
                #print(f'{nickname} has disconnected')
                broadcast(chat_name, f'{nickname} has disconnected'.encode(FORMAT))
                clients.pop(index)
                nicknames.pop(index)
                chatrooms.pop(index)
                client.close()
            else:
                broadcast(chat_name, f'{nickname}: {message}'.encode(FORMAT))
                save_message(message, chat_name, nickname)

def recieve():
    while True:
        client, address = server.accept()
        #print(f'Incoming connection from: {str(address)}')

        client.send("Nick: ".encode(FORMAT))
        nickname = client.recv(1024).decode(FORMAT)
        nicknames.append(nickname)
        clients.append(client)

        wifi_id = client.recv(1024).decode(FORMAT)
        #print(wifi_id)
        if wifi_id not in wifi_ids:
            wifi_ids[wifi_id] = set()

        client.send(f'Existing chats on your wifi are {wifi_ids[wifi_id]}. Enter one of these to connect to an existing room,\
                    or enter a new name for a new room.'.encode(FORMAT))

        client.send("Chat name: ".encode(FORMAT))
        chat_name = client.recv(1024).decode(FORMAT)
        chatrooms.append(chat_name)
        wifi_ids[wifi_id].add(chat_name)

        #print(f'Nickname of the client is: {nickname}')
        #print(f'Chat room of {nickname} is: {chat_name}')

        # Prints last 20 messages if chat room already exists
        if os.path.isfile(chat_name + '.txt'):
            file_name = chat_name + '.txt'
            f = open(file_name, 'r')
            lines = f.readlines()
            for line in lines[-20:]:
                client.send(line.encode(FORMAT))
        else:
            client.send('Creating new chat room'.encode(FORMAT))

        broadcast(chat_name, f'{nickname} has joined the chat.'.encode(FORMAT))
        thread = threading.Thread(target = handle, args = (client,))
        thread.start()

# Saves message to .txt file per chat room
def save_message(message, chat_name, nickname):
    file_name = chat_name + '.txt'
    f = open(file_name, 'a+')
    f.write(nickname + ': ' + message + '\n')
    f.close()



print("Server is listening...")
recieve()