"""
eMessage - Server.py
Author: Yehonatan
"""
import socket
import logging
import config
import _thread
import hashlib
import base64


class EMessageServer:
    """
    EMessageServer - This class will accept connect and listen.
    """
    # list of connected users
    username_list = []

    def __init__(self):
        """
        Constructor - This function will be the constructor of our class.
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients_list = []

    def bind(self):
        """
        bind - This function allows clients to connect to the following server info
        """
        self.socket.bind(
            (
                config.server_address,
                config.server_port
            )
        )
    def broadcast_users(self):
        """
        שולחת לכל המשתמשים את רשימת השמות המלאה בפורמט USERS::
        """
        user_list_message = f"USERS::{','.join(self.username_list)}\n"
        self.sendall(user_list_message)
        
    def listen(self):
        """
        listen - This function will listen
        """
        logging.info("Starting to listen - max connections: {}".format(config.server_max_connections))
        self.socket.listen(config.server_max_connections)

    def accept(self):
        """
        accept - Accepts new client connections, handles login/authentication,
        and starts a new thread for each authenticated client.
        """
        while True:
            try:
                client_connection, client_address = self.socket.accept()
                logging.info(f"Incoming connection from {client_address}")

                # Receive login data
                raw_data = client_connection.recv(config.server_receive_size).decode()
                client_username, client_password = raw_data.split("::")
                client_password = base64.b64decode(client_password.encode())

                # Authentication loop
                while not self.verify(client_username, client_password):
                    client_connection.send("Username is already taken or Wrong Password!".encode())
                    raw_data = client_connection.recv(config.server_receive_size).decode()

                    # Handle unexpected disconnect
                    if not raw_data:
                        client_connection.close()
                        logging.warning("Client disconnected before successful login")
                        break

                    try:
                        client_username, client_password = raw_data.split("::")
                        client_password = base64.b64decode(client_password.encode())
                    except Exception as ex:
                        logging.warning(f"Malformed login retry: {ex}")
                        client_connection.close()
                        break
                else:
                    # בתוך else של ההתחברות המוצלחת:
                    client_connection.send("Password is correct, welcome!".encode())

                    # מוסיפים קודם
                    self.username_list.append(client_username)
                    self.clients_list.append(client_connection)

                    # שולחים רשימת משתמשים לכולם, כולל ללקוח החדש
                    self.broadcast_users()

                    # פתיחת thread
                    _thread.start_new_thread(self.client_handler, (client_connection, client_username))

            except (ValueError, socket.error) as e:
                logging.warning(f"Login error: {e}")
                try:
                    client_connection.close()
                except:
                    pass
                continue

    def client_handler(self, client_connection, client_username):
        """
        client-handler - This function will receive messages from client and handle them.
        """
        logging.info(f"New connection from: {client_username}")

        while True:
            try:
                # First, read the message header (ends with \n)
                header = b""
                while not header.endswith(b"\n"):
                    chunk = client_connection.recv(1)
                    if not chunk:
                        raise socket.error("Client disconnected")
                    header += chunk

                decoded_header = header.decode("utf-8").strip()

                # Re-send updated users list on every message
                # self.sendall(f"USERS::{','.join(self.username_list)}\n")

                # Handle image messages
                if decoded_header.startswith("Image->"):
                    parts = decoded_header.split("->")
                    photo_size = int(parts[1].split("=")[1])
                    sender = parts[2].split("=")[1]
                    resize = parts[3].split("=")[1]

                    # Receive image data
                    photo = b""
                    while len(photo) < photo_size:
                        chunk = client_connection.recv(photo_size - len(photo))
                        if not chunk:
                            raise socket.error("Client disconnected during image transfer")
                        photo += chunk

                    # Send metadata and image
                    self.sendall((decoded_header + "\n").encode("utf-8"))
                    self.sendall(photo)
                    continue

                # Regular text message
                message = f"{client_username} - {decoded_header}"
                self.sendall(message + "\n")

            except socket.error:
                logging.info(f"Client {client_username} has disconnected.")
                self.clients_list.remove(client_connection)
                self.username_list.remove(client_username)
                self.broadcast_users()

                # Send updated user list
                self.sendall(f"USERS::{','.join(self.username_list)}\n")

                self.sendall(f"{client_username} has disconnected.\n", without=client_connection)
                _thread.exit_thread()

    def verify(self, username, password):
        """
        verify- This function checks if the password that has been inserted is correct and returns True/False
        """
        # Compare md5 of the input with our secret hashed password
        special_char_list = ["@", "!", "#", "$", "%", "^", "&", "(", ")", "-", "+", ";"]
        if hashlib.md5(password).hexdigest().upper() == config.server_hashed_password.upper() \
                and (username not in self.username_list) and (len(username) > 0) and (len(username) < 35):
            for i in range(0, len(username)):
                for j in range(0, len(special_char_list)):
                    if username[i] == special_char_list[j]:
                        return False
            return True

        return False

    def sendall(self, message, without=None):
        """
        sendall - sends message to all the clients except the 'without' client
        """
        if isinstance(message, str):
            message = message.encode("utf-8")

        for client in self.clients_list:
            if client is not without:
                try:
                    client.send(message)
                except socket.error as e:
                    logging.warning(f"Failed to send to a client: {e}")

def main():
    """
    main - this is the main function which will start the server and define the logging
    """
    # Logging
    logging.basicConfig(
        filename=config.log_file_name,
        filemode='w',
        level=logging.DEBUG
    )

    # Server
    server = EMessageServer()

    # Bind address to port
    server.bind()

    # Listen
    server.listen()

    try:
        # Accept connections
        server.accept()
    except KeyboardInterrupt:
        print("\nServer is closed.")
        logging.info("Server manually stopped with Ctrl+C")
        try:
            server.socket.close()
        except:
            pass
        exit(0)

if __name__ == "__main__":
    main()