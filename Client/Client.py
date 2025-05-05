"""
eMessage - Server.py
Author: Yehonatan
"""
import socket
import threading
import logging
import os
import base64
import tkinter as tki
from tkinter import messagebox as tkm
from tkinter import filedialog as tkf
import io
import glob
import PIL
from PIL import ImageTk, Image
import config
import sys

class VerticalScrolledFrame(tki.Frame):
    """
    From: https://stackoverflow.com/questions/16188420/python-tkinter-scrollbar-for-frame
    """
    def __init__(self, parent, *args, **kw):
        tki.Frame.__init__(self, parent, *args, **kw)

        # create a canvas object and a vertical scrollbar for scrolling it
        vscrollbar = tki.Scrollbar(self, orient=tki.VERTICAL)
        vscrollbar.pack(fill=tki.Y, side=tki.RIGHT, expand=tki.FALSE)

        self.canvas = tki.Canvas(self, bd=0, height=900, highlightthickness=0,
                                yscrollcommand=vscrollbar.set)
        self.canvas.pack(side=tki.LEFT, fill=tki.BOTH, expand=tki.TRUE)
        vscrollbar.config(command=self.canvas.yview)

        # Move mousewheel binding into one function
        def _on_mousewheel(event):
            if sys.platform == 'darwin':
                self.canvas.yview_scroll(-1 * int(event.delta), "units")
            else:
                self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")

        # Bind scrolling only when the mouse is over the canvas
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", _on_mousewheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))
        self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))  # Linux
        self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))   # Linux

        # reset the view
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = tki.Frame(self.canvas)
        interior_id = self.canvas.create_window(0, 0, window=interior, anchor=tki.NW)

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            if size[1] > self.canvas.winfo_height():
                self.canvas.config(scrollregion="0 0 %s %s" % size)
            else:
                self.canvas.config(scrollregion="0 0 %s %s" % (size[0], self.canvas.winfo_height()))
            if interior.winfo_reqwidth() != self.canvas.winfo_width():
                self.canvas.config(width=interior.winfo_reqwidth())

        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != self.canvas.winfo_width():
                self.canvas.itemconfigure(interior_id, width=self.canvas.winfo_width())

        self.canvas.bind('<Configure>', _configure_canvas)

class EMessageClient:
    socket = None
    """
    eMessageServer - This class will connect to eMessage server.
    """

    def __init__(self):
        """
        Constructor - This function will be the constructor of our class.
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect_to_server(self):
        """
        connect - This function will ask to connect to the server
        """
        try:
            self.socket.connect(
                (
                    config.server_address,
                    config.server_port
                )
            )
        except socket.error as e:
            logging.error("Could not connect to server, socket error: {}".format(str(e)))
            raise Exception(str(e))

    def send_message(self, message):
        """
        send_message - Sends message to server
        """
        if isinstance(message, str):
            message = message.encode("utf-8")
        self.socket.send(message)


    def recv(self, size=1024):
        """
        recv - This function will receive messages from the other client or the server
        """
        while True:
            try:
                message = self.socket.recv(size)
                return message
            except socket.error:
                logging.error("The server closed the connection, bye!")
                os._exit(1)

    def close_server_connection(self):
        """
        close - This function will close the connection
        """
        self.socket.close()


class EMessageGUI():
    """
    eMessageGUI - Our Message GUI
    """
    root = None
    content = None
    txt_box = None
    eclient = None

    def __init__(self):
        """
        init - ....
        """
        self.root = tki.Tk()
        self.eclient = EMessageClient()

        # Menu
        self.menubar = tki.Menu(self.root)

        # Menubar configuration
        self.root.config(menu=self.menubar)
        self.menubar.add_command(label="Exit", command=self.quit)        

        #tries to create a connection
        try:
            self.eclient.connect_to_server()
        except Exception as e:
            self.root.withdraw()
            tkm.showerror("eMessage - Error", e)
            os._exit(1)

        self.white_box = None
        self.green_box = None
        self.txt_input = None
        self.authenticated = False
        self.welcome_label = None
        self.password = None
        self.error_label = None
        self.username = None
        self.content_frame = None
        self.attempts = 0
        self.username_input = None
        self.password_input = None
        self.emojies_bar = None
        self.scroller = None
        self.other_username_label = None

    def get_message_once(self):
        try:
            message = b""
            while not message.endswith(b"\n"):
                message += self.eclient.recv(1)
            decoded_msg = message.decode("utf-8").strip()
            if decoded_msg.startswith("USERS::"):
                username_list = decoded_msg.split("::")[1].split(",")
                if len(username_list) <= 1:
                    self.other_username_label["text"] = ""
                    self.other_username_label.pack_forget()
                else:
                    other_user = next((u for u in username_list if u != self.username), None)
                    if other_user:
                        self.other_username_label["text"] = other_user
                        self.other_username_label.pack(side=tki.RIGHT, padx=15, pady=0, fill=tki.Y)
                    else:
                        self.other_username_label["text"] = ""
                        self.other_username_label.pack_forget()

        except Exception as e:
            logging.warning(f"get_message_once failed: {e}")

    def configure_login_window(self):
        """
        configure_login_window - function creates a login window to eMessage
        """
        self.root.geometry("760x900")
        self.root.title("eMessage - Log In")
        try:
            self.root.iconbitmap(os.path.expanduser("~/emessage/Resources/icon_emsg.ico"))
        except tki.TclError:
            pass  # Ignore icon setting if unsupported (Linux/WSL)
        self.root.wm_maxsize(760, 900)
        self.root.wm_minsize(760, 900)
        self.root.protocol('WM_DELETE_WINDOW', self.exit_func)

        #creating canvas and adding the eMessage logo
        container = tki.Frame(self.root)
        container.pack(fill='both', expand=True)
        self.content = tki.Canvas(container)
        image = Image.open("../Resources/logo.png").resize((700, 371), Image.Resampling.LANCZOS)
        background_image = ImageTk.PhotoImage(image)
        background = tki.Label(self.content, image=background_image)
        background.image = background_image
        self.content.create_image(15, 0, image=background_image, anchor=tki.NW)
        self.content.pack(fill='both', expand=True)

        #Username label
        username_label = tki.Label(self.content, text="Username: ", font=("Segoe UI Semibold", 20))
        username_label.place(x=95, y=380)

        #Username entry
        self.username_input = tki.Entry(self.content, width=40, font=("Segoe UI Semibold", 14))
        self.username_input.configure(border=0)
        self.username_input.focus_set()
        self.username_input.place(x=235, y=390)

        #Password label
        password_label = tki.Label(self.content, text="Password: ", font=("Segoe UI Semibold", 20))
        password_label.place(x=95, y=450)

        #Password entry
        self.password_input = tki.Entry(self.content, width=40, font=("Segoe UI Semibold", 14), show="*")
        self.password_input.configure(border=0)
        self.password_input.focus_set()
        self.password_input.place(x=235, y=460)

        #Login button
        login_button = tki.Button(self.content, bg='white', borderwidth=0, text="Login", font=("Segoe UI Semibold", 16),
                                  command=self.login_func)
        login_button.place(x=280, y=550)
        self.root.bind('<Return>', self.login_func)

        #Exit button
        exit_button = tki.Button(self.content, bg='white', borderwidth=0, text="Exit", font=("Segoe UI Semibold", 16),
                                 command=self.exit_func)
        exit_button.place(x=460, y=550)

        #Error label - presented when username is already in use or password is incorrect
        self.error_label = tki.Label(self.content, text="", fg='red', font=("Segoe UI Semibold", 12))
        self.error_label.place(x=160, y=640)

    def login_func(self, event=None):
        """
        login_func - function checks if input username is available and password is correct
        """
        #Get password and username that have been inserted by client
        self.username = self.username_input.get()
        self.password = base64.b64encode(self.password_input.get().encode()).decode()

        # Send password to the server
        self.eclient.send_message(self.username + "::" + self.password)
        server_check = self.eclient.recv().decode("utf-8")

        #authenticates if password is correct or wrong
        if "Wrong" in server_check:
            self.attempts += 1
            self.error_label["text"] = "Username is already taken or incorrect password! (attempt #{})".format(
                self.attempts)
            return
        elif "correct" in server_check:
            self.authenticated = True

            #removes things that have been packed at the login window without closing it
            for element in self.root.winfo_children():
                element.pack_forget()

            #starts chat window
            self.configure_chat_window()
            self.start_emessage()
            return

    def exit_func(self):
        """
        exit_func - function works at login window when "X" or "Exit" is pressed to check if the client
        wants to leave the program. If he does, code will abort, else code will continue
        """
        result = tkm.askquestion("Exit eMessage", "Are you sure that you want to exit?", icon='warning')
        if result == 'yes':
            print ("Goodbye :(")
            self.root.destroy()
        else:
            print ("Nice that you've decided to stay :)")

    def start_emessage(self):
        """
        start_emessage - function starts a thread on get_message(self) function.
        """
        threading.Thread(target=self.get_message, daemon=True).start()

    def quit(self):
        """
        quit - function works at chat window when "X" is pressed to check if the client
        wants to leave the program. If he does, code will abort, else code will continue
        """
        result = tkm.askquestion("Exit eMessage", "Are you sure that you want to quit?", icon='warning')
        if result == 'yes':
            print ("Goodbye :(")
            self.eclient.close_server_connection()
            self.root.destroy()
            os._exit(0)
        else:
            print ("Nice that you've decided to stay :)")

    def configure_chat_window(self):
        """
        configure - function creates a chat window to eMessage
        """
        # Title
        if not self.authenticated:
            return

        # Configuration
        self.root.title("eMessage")
        self.root.geometry('760x900')
        if sys.platform.startswith("win"):
            try:
                self.root.iconbitmap(os.path.abspath("../Resources/icon_emsg.ico"))
            except tki.TclError:
                pass  # Ignore if not found or unsupported
        self.root.protocol('WM_DELETE_WINDOW', self.quit)

        # Background
        self.content_frame = VerticalScrolledFrame(self.root)
        self.welcome_label = tki.Label(self.content_frame.interior, width=760, text="Starting eMessage", font=("Segoe UI Semibold", 14))
        self.welcome_label.pack()

        # Header
        header = tki.Frame(self.root, bg='darkgreen', height=50)
        header.pack_propagate(False)
        header.pack(fill=tki.X, side=tki.TOP)
        self.emojies_bar = tki.Frame(self.root, bg='white', height=90)
        footer = tki.Frame(self.root, bg='white', height=90)

        # Text Input

        self.txt_input = tki.Entry(footer, textvariable=1, width=58, font=("Segoe UI Semibold", 14))
        self.txt_input.configure(border=0)
        self.txt_input.focus_set()
        self.txt_input.pack(padx=5, ipady=8, side=tki.LEFT)

        # Scroller
        self.scroller = tki.Scrollbar(self.content, orient=tki.VERTICAL)
        self.scroller.pack(side=tki.RIGHT, fill=tki.Y)
        self.scroller.config(command=self.content.yview)
        self.content.config(yscrollcommand=self.scroller.set)

        # File menu
        filemenu = tki.Menu(self.menubar, tearoff=0)
        filemenu.add_separator()
        filemenu.add_command(label="Upload photo", command=self.upload_image)
        filemenu.add_separator()

        self.menubar.add_cascade(label="File", menu=filemenu)

        # Image of the send button
        btn_image = Image.open("../Resources/send.png")
        btn_image = ImageTk.PhotoImage(btn_image)

        # Send button
        send_btn = tki.Button(
            footer,
            image=btn_image,
            compound="left",  # image on the left, text on the right (optional)
            bg="#4CAF50",              # nice green
            fg="white",                # white text
            activebackground="#45a049",
            activeforeground="white",
            font=("Segoe UI Semibold", 12),
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.send_message
        )
        send_btn.image = btn_image  # Keep reference to image
        send_btn.pack(side=tki.RIGHT, padx=5, pady=5)


        # Image of the upload button
        upload_btn_image = Image.open("../Resources/upload.png")
        upload_btn_image = ImageTk.PhotoImage(upload_btn_image)

        # Upload button
        upload_send_btn = tki.Button(footer, bg='white', borderwidth=0, command=self.upload_image,
                                     image=upload_btn_image)
        upload_send_btn.image = upload_btn_image
        upload_send_btn.pack(side=tki.RIGHT)

        # White message box
        white_box = Image.open("../Resources/white.png")
        self.white_box = ImageTk.PhotoImage(white_box)

        # Green message box
        green_box = Image.open("../Resources/greenbox.png")
        self.green_box = ImageTk.PhotoImage(green_box)

        # Pack Everything (Header, Body, Footer)
        header.pack(fill=tki.BOTH, side=tki.TOP)

        self_label = tki.Label(header, bg='darkgreen', fg='white',
            text=self.username, font=("Segoe UI Semibold", 18, "bold"),
            pady=10)
        self_label.pack(side=tki.LEFT, padx=15, pady=0, fill=tki.Y)

        self.other_username_label = tki.Label(
            header, bg='darkgreen', fg='lightgrey',
            text="", font=("Segoe UI Semibold", 18),
            anchor='e'
        )
        self.other_username_label.pack(side=tki.RIGHT, padx=15, pady=0, fill=tki.Y)
        
        footer.pack(fill=tki.BOTH, side=tki.BOTTOM)
        self.emojies_bar.pack(fill=tki.BOTH, side=tki.BOTTOM)
        self.fill_emojies()

        self.root.bind('<Return>', self.send_message)

    def fill_emojies(self):
        """
        fill_emojies - function adds buttons of emojies that are uploaded when they're pressed
        """
        #Receives every image in folder that is .png format - in advance all the .pngs are emojies
        emojies = glob.glob("../Resources/emojis/*.png")

        # Opens every emoji
        for emoji in emojies:
            emoji_image = Image.open(emoji)

            # Converts to base64 in order to send it to server
            with open(emoji, "rb") as file_object:
                emoji_image_content = base64.b64encode(file_object.read())

            # Emojis resize when upload
            emoji_image.thumbnail((32, 32), Image.Resampling.LANCZOS)
            emoji_image = ImageTk.PhotoImage(emoji_image)

            # Buttons that each contain an emoji. Buttons numbered by the number of emojies in folder
            emoji_label = tki.Button(self.emojies_bar, image=emoji_image,
                                     borderwidth=1.3, command=lambda x=emoji_image_content: self.send_image(x, 32))
            emoji_label.image = emoji_image
            emoji_label.pack(side=tki.LEFT, fill=tki.Y)

    def upload_image(self):
        """
        upload_image - function uploads an image, converts it to base64 string
        and calls send_image(<image data with base64>)
        """
        photo = tkf.askopenfile("rb")
        if photo is None:
            return
        photo = base64.b64encode(photo.read())
        self.send_image(photo)

    def send_image(self, photo, resize=200):
        """
        send_image - function sends to the server: image base64 data length, client username,
        the wanted size, and the read of the photo itself.
        """
        photo_length = len(photo)
        photo_message = f"Image->length={photo_length}->sender={self.username}->resize={resize}\n"
        self.eclient.send_message(photo_message)
        self.eclient.send_message(photo)

    def send_message(self, event=None):
        """
        send_message - function will send messages to server
        """
        message = self.txt_input.get()
        if (len(message) > 0) and (len(message) < 55) and not message.startswith("Image->"):
            self.eclient.send_message(message + "\n")

    def get_message(self):
        while True:
            message = b""
            while not message.endswith(b"\n"):
                message += self.eclient.recv(1)
            decoded_msg = message.decode("utf-8").strip()
            if not message:
                break

            # Try decoding for text messages
            try:
                decoded_msg = message.decode("utf-8")
            except UnicodeDecodeError:
                decoded_msg = None  # It's probably image data

            # Inside get_message method
            if decoded_msg.startswith("USERS::"):
                username_list = decoded_msg.split("::")[1].split(",")
                if len(username_list) <= 1:
                    self.other_username_label["text"] = ""
                    self.other_username_label.pack_forget()
                else:
                    other_user = next((u for u in username_list if u != self.username), None)
                    if other_user:
                        self.other_username_label["text"] = other_user
                        self.other_username_label.pack(side=tki.RIGHT, padx=15, pady=0, fill=tki.Y)
                    else:
                        self.other_username_label["text"] = ""
                        self.other_username_label.pack_forget()
                continue

            # Handle image
            if decoded_msg and decoded_msg.startswith("Image->"):
                parts = decoded_msg.split("->")
                photo_size = int(parts[1].split("=")[1])
                sender = parts[2].split("=")[1]
                resize = int(parts[3].split("=")[1])
                current_photo_size = 0
                photo_bytes = b""
                while current_photo_size < photo_size:
                    chunk = self.eclient.recv(photo_size - current_photo_size)
                    photo_bytes += chunk
                    current_photo_size += len(chunk)

                try:
                    image_data = base64.b64decode(photo_bytes)
                    image_stream = io.BytesIO(image_data)
                    img = Image.open(image_stream)
                    img.thumbnail((resize, resize), Image.Resampling.LANCZOS)
                    photo_imgtk = ImageTk.PhotoImage(img)

                    # display on right or left
                    label = tki.Label(
                        self.content_frame.interior,
                        image=photo_imgtk
                    )
                    label.image = photo_imgtk
                    anchor = tki.NE if sender != self.username else tki.NW
                    label.pack(anchor=anchor, padx=30, pady=10)
                    self.content_frame.pack()
                    self.content_frame.interior.update_idletasks()
                    self.content_frame.canvas.update_idletasks()
                    self.content_frame.canvas.yview_moveto(1.0)
                    self.txt_input.delete(0, 'end')
                except Exception as e:
                    print(f"Failed to display image: {e}")
                continue

            # Handle regular text messages
            if decoded_msg:
                is_mine = self.my_message(decoded_msg)
                box_img = self.green_box if is_mine else self.white_box
                anchor = tki.NW if is_mine else tki.NE

                label = tki.Label(
                    self.content_frame.interior,
                    image=box_img,
                    text=decoded_msg,
                    font=("Segoe UI Semibold", 12),
                    compound=tki.CENTER,
                    padx=20,
                    pady=10,
                    anchor='center',
                    justify='center',
                    wraplength=350
                )
                label.image = box_img
                label.pack(anchor=anchor, padx=30, pady=5)

                self.content_frame.pack()
                self.content_frame.interior.update_idletasks()
                self.content_frame.canvas.yview_moveto(1.0)
                self.txt_input.delete(0, 'end')

    # checks if the last message that has been sent was sent by me or the other client
    def my_message(self, message):
        try:
            if message.startswith(self.username):
                return True
            return False
        except UnicodeDecodeError:
            if message.decode('utf-8').startswith(self.username):
                return True
            return False            


def main():
    """
    main - This function stores the main settings and calls for other functions in the eMessageClient class
    """
    # Logging
    logging.basicConfig(filename=config.log_file_name, filemode=config.log_file_write_mode, level=logging.DEBUG)

    # GUI
    gui = EMessageGUI()

    gui.configure_login_window()

    # GUI Main Loop
    gui.root.mainloop()


if __name__ == "__main__":
    main()