
#!/usr/bin/python3


import threading
import socket

MAX_MSG_LEN = 1024
MAX_NICKNAME_LEN = 30

class chat_client:
    def __init__(self, socket, address,nickname, recv_callback, disconnect_callback):
        self.socket = socket
        self.address = address
        self.nickname = nickname
        self.accept_thread = None
        self.state = False
        self.recv_callback = recv_callback
        self.disconnect_callback = disconnect_callback


    def send(self, message):
        if self.state == False:
           return

        try:
            #lock
            self.socket.send(message.encode())
            #unlock

        except IOError as e:
            # handling the normal error on nonblocking connections.
            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                print('Reading error: {}'.format(str(e)))
        except:
            print("ERR: client[{self.nickname}]: faile to send")


    def handle_receive(self):
        self.state = True

        print("Start receiving")

        #while self.state:
        while True:
            try:
                print("wait for msg...")
                data = self.socket.recv(MAX_MSG_LEN).decode()
                if not len(data):
                    break

                self.recv_callback(self, data)
            except:
                break

        self.state = False
        print(f"Warning: Client closed connection")
        self.disconnect_callback(self)

    def stop(self):
        self.state = False

    def disconnect(self):
        self.accept_thread.shutdown(socket.SHUT_RDWR)

    def run(self):
        print("client run")
        self.recv_thread = threading.Thread(target=self.handle_receive)
        self.recv_thread.start()


class chat_server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.clients = []

    def accept_connections(self):
        listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen_socket.bind((self.host, self.port))
        listen_socket.listen()

        while True:
            client_socket, client_address = listen_socket.accept()
            #print(f"ChatBox Server {client_socket[0]} {client_socket[1]} {client_address}")
            client_socket.send(b'hello')
            print(f"ChatBox Server Accept connection")
            nickname = client_socket.recv(MAX_NICKNAME_LEN).decode()
            if not len(nickname):
                print(f"Warning: Client closed connection {client_address}")
                continue

            client = chat_client(client_socket, client_address, nickname, self.broadcast, self.disconnect)
            self.add_client(client)
            client.run()
            client.send("Welcome to the server")
            self.broadcast(client,"just joined the chat")

    def add_client(self, client):
        self.clients.append(client)

    def rm_client(self, client):
        self.clients.remove(client)


    def broadcast(self, sender_client, message):
        print("broadcast: {} : {}".format(sender_client.nickname,message))
        msg = "{} : {}".format(sender_client.nickname,message)
        for client in self.clients:
            if client != sender_client:
                client.send(msg)

    def disconnect(self, client):
        print("Server : client disconnect")
        self.rm_client(client)

    def run(self):
        self.accept_thread = threading.Thread(target=self.accept_connections)
        #self.accept_thread.setDaemon(True)
        self.accept_thread.start()

    def stop(self):
        for client in self.clients:
                client.stop()
        for client in self.clients:
                client.disconnect()
        self.accept_thread.shutdown(socket.SHUT_RDWR)

    def join(self):
        try:
            self.accept_thread.join()
        except:
            print("Exit")

if __name__ == '__main__':
    server = chat_server("localhost", 5555)
    print(f"ChatBox Server {server.host} {server.port}")
    server.run()
    server.join()
