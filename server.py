#
# Серверное приложение для соединений
#

import asyncio

# Server - client connection
from asyncio import transports
from random import choice
from typing import Optional


class ServerProtocol(asyncio.Protocol):
    # get - decode - read - code - send
    login: str = None
    server: 'Server'  # solved that server is not declared
    transport: transports.BaseTransport
    __no_color = "\033[0m"

    def __init__(self, server: 'Server'):
        self.server = server

    user_color: str

    @staticmethod
    def choose_color():
        for_colors = list(range(30, 37)) + list(range(90, 97))
        color = choice(for_colors)
        return f"\033[{color}m"

    def data_received(self, data: bytes) -> None:
        decoded = data.decode()
        print(decoded)
        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                login = decoded.replace("login:", "").replace("\r\n", "")
                if login in [user.login for user in self.server.clients]:
                    self.transport.write(f"User {login} is already exist, try another user name\n".encode())
                    self.transport.close()
                else:
                    self.login = login
                    self.send_history(self)
                    self.user_color = self.choose_color()
                    self.transport.write(f"{self.user_color}Hello {self.login}\n{self.__no_color}".encode())
            else:
                self.transport.write("Wrong login\n".encode())

    def send_message(self, content):
        text = f"{self.user_color}{self.login}{self.__no_color}: {content}"
        self.server.history.append(text.encode())

        if content == "logout:\r\n":
            self.transport.close()

        # Delete oldest message if size of history is greater then 10
        if len(self.server.history) > 10:
            self.server.history.pop(0)

        for user in self.server.clients:
            user.transport.write(text.encode())

    def connection_made(self, transport: transports.BaseTransport) -> None:
        self.server.clients.append(self)
        self.transport = transport
        print("New client is come\n")

    def connection_lost(self, exc: Optional[Exception]) -> None:
        self.server.clients.remove(self)
        if self.login is None:
            print(f"Client with already existed login is blocked\n")
        else:
            print(f"Client {self.user_color}{self.login}{self.__no_color} is out\n")

    def send_history(self, user):
        self.transport.write("\nHistory of the chat:\n".encode())

        if len(self.server.history) == 0:
            user.transport.write("No history\n\n".encode())
        else:
            for massage in self.server.history:
                user.transport.write(massage)


class Server:
    clients: list
    history: list

    def __init__(self):
        self.clients = []
        self.history = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(self.build_protocol, "127.0.0.1", 8888)

        print("Server started")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Server is closed manually")
