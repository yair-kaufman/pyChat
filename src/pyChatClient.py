#!/usr/bin/python3

import customtkinter as ctk
import threading
import socket

MAX_BUFF = 1024

class chatbox_client(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry('500x500')
        self.title('Chat-Box Client')
        self.login_frame = login_frame(self, self.login_callback)
        self.login_frame.show()
        self.chat_frame = chat_frame(self, self.send_message_callback)
        self.client = client(self.receive_message_callback, self.disconnect_callback)
        self.protocol("WM_DELETE_WINDOW", self.close)

    def login_callback(self):
        connection_info = self.login_frame.info()
        print(connection_info)
        self.client.set(connection_info[0], connection_info[1], connection_info[2])
        self.client.connect()
        self.login_frame.hide()
        self.chat_frame.show()

    def send_message_callback(self):
        message = self.chat_frame.get_message()
        self.client.send_message(message)
        self.chat_frame.write_my_message(message)

    def receive_message_callback(self, message):
        self.chat_frame.write_other_message(message)

    def disconnect_callback(self):
        print("disconnect_callback")
        self.chat_frame.hide()
        self.login_frame.show()

    def close(self):
        self.client.disconnect()
        #self.chat_frame.hide()
        #self.login_frame.show()
        self.quit()


class chat_frame(ctk.CTkFrame):
    def __init__(self, app, command):
        super().__init__(app)
        self.message_entry = ctk.CTkEntry(master=self)
        self.scrollable_frame = messages_frame(self)
        self.send = ctk.CTkButton(master=self, text="send", command=self.handle_button)
        self.command = command
        self.message_entry.bind('<Return>', self.handle_newline)

    def get_message(self):
        return self.message_entry.get()

    def show(self):
        self.message_entry.grid(row=1, column=1, padx=20, pady=20, sticky='ws')
        self.scrollable_frame.grid(row=0, column=1, columnspan=2, padx=20, pady=20, sticky='wse')
        self.pack(fill="none", expand=True)
        self.send.grid(row=1, column=2, padx=20, pady=20, sticky='es')

    def handle_button(self):
        self.command()
        # clear input message
        self.message_entry.delete(0, 'end')

    def handle_newline(self, event):
        self.handle_button()

    def hide(self):
        self.pack_forget()

    def write_other_message(self, message):
        self.scrollable_frame.other_messages(message)

    def write_my_message(self, message):
        self.scrollable_frame.my_message(message)


class messages_frame(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.counter = 0

    def my_message(self, text):
        message = ctk.CTkLabel(master=self, text=text, fg_color='green', corner_radius=10)
        message.grid(row=self.counter, column=0, padx=20, pady=5, sticky="w")
        self.counter = self.counter + 1

    def other_messages(self, text):
        message = ctk.CTkLabel(master=self, text=text, fg_color='gray', corner_radius=10)
        message.grid(row=self.counter, column=0, padx=20, pady=5, sticky='e')
        self.counter = self.counter + 1


class client:

    def __init__(self, recv_callback, disconnect_callback,
                 host="localhost", port=5555, nickname="chatbot"):

        self.set(host, port, nickname)
        self.socket = socket.socket()
        self.recv_callback = recv_callback
        self.disconnect_callback = disconnect_callback
        self.handle_thread = None
        self.event = threading.Event()


    def set(self, host, port, nickname):
        self.host = host
        self.port = port
        self.nickname = nickname


    def connect(self):
        #      self.status = True
        self.handle_thread = threading.Thread(target=self.handle_connection)
        self.handle_thread.start()

    def handle_connection(self):
        self.settimeout(5)
        try:
            self.socket.connect(self.host, self.port)
            recv = self.socket.recv(MAX_BUFF).decode()
            print(recv)
            if not recv == 'hello':
                self.socket.close()
                self.disconnect_callback()
                print('connect: handshake failed')
                return

            self.socket.send(self.nickname.encode())
        except:
            self.disconnect_callback()
            return

        while self.event.is_set():
            try:
                message = self.socket.recv(MAX_BUFF).decode()
                print(message)
                self.recv_callback(message)
            except:
                self.socket.close()
                print('close socket')
                self.disconnect_callback()
                break

    def send_message(self, message):
        self.socket.send(f'{message}'.encode())
        print(message)

    def disconnect(self):
        self.client.event.set()


class login_frame(ctk.CTkFrame):

    def __init__(self, app, command):
        super().__init__(app)
        self.client = client
        self.host_label = ctk.CTkLabel(master=self, text="host: ")
        self.host_label.grid(row=0, column=0, padx=20, pady=20)

        default_address = ctk.StringVar(value="127.0.0.1")
        self.host_entry = ctk.CTkEntry(master=self, textvariable=default_address,
                                       placeholder_text="127.0.0.1")
        self.host_entry.grid(row=0, column=1, padx=20, pady=20)

        self.port_label = ctk.CTkLabel(master=self, text="port: ")
        self.port_label.grid(row=1, column=0, padx=20, pady=20)
        default_port = ctk.StringVar(value="5555")
        self.port_entry = ctk.CTkEntry(master=self, textvariable=default_port,
                                       placeholder_text="5555")
        self.port_entry.grid(row=1, column=1, padx=20, pady=20)

        default_nickname = ctk.StringVar(value="nickname")
        self.nickname_label = ctk.CTkLabel(master=self, text="nickname: ")
        self.nickname_label.grid(row=2, column=0, padx=20, pady=20)
        self.nickname_entry = ctk.CTkEntry(master=self,  textvariable=default_nickname,
                                           placeholder_text="nickname")
        self.nickname_entry.grid(row=2, column=1, padx=20, pady=20)

        self.connect_button = ctk.CTkButton(master=self, text="connect", command=command)
        self.connect_button.grid(row=3, column=1, padx=20, pady=20)

    def info(self):
        host = self.host_entry.get()
        port = int(self.port_entry.get())
        nickname = self.nickname_entry.get()
        return [host, port, nickname]

    def show(self):
        self.pack(fill="none", expand=True)

    def hide(self):
        self.pack_forget()


client = chatbox_client()
client.mainloop()
