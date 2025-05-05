import tkinter as tki
from tkinter import messagebox as tkm
from tkinter import simpledialog as tks
from PIL import ImageTk, Image
import hashlib

root = tki.Tk()



def quit_func():
    result = tkm.askquestion("eMessage - Alert", "Are You Sure?", icon='warning')
    if result == 'yes':
        print ("Goodbye :(")
        root.destroy()
    else:
        print ("Nice that you've decided to stay :)")


def config_openscreen():

    def login_func():
        print("Trying to login...")
        if password_input.get() == "123":
            tkm.showinfo("-- COMPLETE --", "You Have Now Logged In.", icon="info")
        else:
            tkm.showinfo("-- ERROR --", "Please enter valid infomation!", icon="warning")

    root.geometry("500x500")
    root.title("eMessage - Log In")
    root.iconbitmap('C:\Users\YEHONATAN\Desktop\myWhatsApp\Resources\icon_emsg.ico')
    root.resizable(width=tki.FALSE, height=tki.FALSE)

    menu = tki.Canvas(tki.Frame().grid(row=0, column=0))
    image = Image.open("..\\Resources\\logo.png").resize((462, 245), Image.ANTIALIAS)
    background_image = ImageTk.PhotoImage(image)
    background = tki.Label(menu, image=background_image)
    background.image = background_image
    menu.create_image(15, 0, image=background_image, anchor=tki.NW)
    menu.pack(fill='both', expand=True)

    username_label = tki.Label(menu, text="Username: ", font=("Segoe UI Semibold", 16))
    username_label.place(x=20, y=230)

    username_input = tki.Entry(menu, width=35, font=("Segoe UI Semibold", 12))
    username_input.configure(border=0)
    username_input.focus_set()
    username_input.place(x=140, y=238)
    username = username_input.get()

    password_label = tki.Label(menu, text="Password: ", font=("Segoe UI Semibold", 16))
    password_label.place(x=20, y=300)

    password_input = tki.Entry(menu, width=35, font=("Segoe UI Semibold", 12), show="*")
    password_input.configure(border=0)
    password_input.focus_set()
    password_input.place(x=140, y=308)

    login_button = tki.Button(menu, bg='white', borderwidth=0, text="Login", font=("Segoe UI Semibold", 16),
                              command=login_func)
    login_button.place(x=130, y=360)

    exit_button = tki.Button(menu, bg='white', borderwidth=0, text="Exit", font=("Segoe UI Semibold", 16),
                             command=quit_func)
    exit_button.place(x=300, y=360)


config_openscreen()
root.mainloop()

