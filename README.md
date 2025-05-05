# eMessage Chat Application

A real-time Python chat app with GUI, emoji support, and image sharing. Built with sockets and Tkinter.

---

## 🗂 Project Structure

```
eMessageProject/
├── Client/
│   ├── __init__.py
│   ├── Client.py
│   ├── config.py
│   └── Resources/
│       ├── emojis/
│       ├── logo.png
│       ├── send.png
│       └── upload.png
├── Server/
│   ├── __init__.py
│   ├── Server.py
│   └── config.py
├── test.py
├── setup.sh
└── README.md
```

---

## ⚙️ Setup Instructions

After cloning the project, just run:

```bash
chmod +x setup.sh
./setup.sh
```

This installs everything you need – no manual steps, no package guesswork.

---

## ▶️ Running the App

1. Open one terminal and run the **server**:
```bash
cd Server
```

```bash
python3 Server.py
```

2. For each user, open a **new terminal** and run the **client**:
```bash
cd Client
```

```bash
python3 Client.py
```

You can open multiple client windows to simulate multiple users chatting with each other.

---

## 🧪 Running Tests

To run automated tests:
```bash
python3 test.py
```

---

## 📌 Features

- Secure login (with password verification)
- Styled GUI with chat bubbles
- Emoji bar
- Image upload & sharing

---

***Further updates and patches are coming soon!***
***Stay tuned 😎*** 

**Author:** Yehonatan  
**Enjoy chatting 🟢**
