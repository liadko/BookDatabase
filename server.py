__author__ = 'Liad Koren'

import sqlite3
import socket
import sys
import threading



def recv_from_client(client):
    #receive first byte, also check if he left
    try:
        msg_length = int.from_bytes(client.recv(1), 'little') # convert first received byte to int
    except Exception as e:
        return None
    
    msg = client.recv(msg_length).decode() # get message from one client
    
    print(f"Client Has Sent The Message: \'{msg}\'")

    return msg

def send(client, msg, log=False):
    
    if(log):
        print(f"Server Sending The Message: \'{msg}\'\n")
    
    message_bytes = msg.encode() # string to bytes
    msg_length = len(message_bytes) # get length int
    msg_length_bytes = msg_length.to_bytes(1, byteorder='little') # int to byte
    client.send(msg_length_bytes + message_bytes)

# returns True on success, False on fail, and None on Disconnect
def try_sign_in(client):
    
    signin_reguest = recv_from_client(client) 
    
    if(not signin_reguest):
        return None # client disconnected
    
    request_parts = signin_reguest.split("~")
    
    if(len(request_parts) != 3):
        print("Client Has Sent Invalid Signin Request")
        send(client, "INCORRECT", 1)
        return False
    
    (request, username, password)  = request_parts
    
    if(request == "REGISTER"):
        if(db_user_exists(username)):
            send(client, "USEREXISTS", 1)
            return False
        
        # success!
        db_add_user(username, password)
        return True
        
    if(request == "LOGIN"):
        if(not db_user_password_combo_exists(username, password)):
            send(client, "INCORRECT", 1)
            return False
        
        # success!
        return True
    
    
    print("Unrecognised Registeration/login message")
    send(client, "INCORRECT", 1)
    return False        


def booklist_string():
    books = db_fetch_book_list()
    if(len(books) == 0):
        return "Library Is Empty."
    
    s = "   " + "Title".ljust(25, ' ') + " Author\n"
    for i, book in enumerate(books):
        (_, title, author) = book
        s += f"{i+1}. {str(title).ljust(25, ' ')} {str(author)}\n"
    
    return s


def try_add_book(request_parts):
    if(len(request_parts) != 3):
        return "Invalid Add request."
        
    if(db_book_exists(request_parts[1])):
        return f"Book Titled {request_parts[1]} already exists."
    
    db_add_book(request_parts[1], request_parts[2])
    return f"Successfuly Added Book Titled {request_parts[1]} To Library."

def try_remove_book(request_parts):
    if(len(request_parts) != 2):
        return "Invalid Remove request."
        
    if(not db_book_exists(request_parts[1])):
        return f"Book Titled {request_parts[1]} does not exist."
    
    db_remove_book(request_parts[1])
    return f"Successfuly Removed Book Titled {request_parts[1]} From Library."

def get_response(client_msg):
    
    if(not client_msg):
        return None
    
    request_parts = client_msg.split("~")
    
    request = request_parts[0]
    
    if(request == "GETBOOKS"):
        return booklist_string()
    
    if(request == "ADD"):
        return try_add_book(request_parts)
    
    if(request == "REMOVE"):
        return try_remove_book(request_parts)
    
    
    return "Server Does Not Understand Request: {}".format(client_msg)

# Function to handle client requests
def handle_client(client:socket):
    
    # SIGN IN PROCESS
    success = False
    while success == False:
        success = try_sign_in(client)
        
        if(success == None):
            print("Client Left While Signing In")
            client.close()
            return
        
    send(client, "SUCCESS", 1)
    
    # SERVER CLIENT CORRESPONDENCE
    while True:
        client_msg = recv_from_client(client)

        response = get_response(client_msg)
        
        if(response == None):
            print("Client Disconnected.")
            client.close()
            return
        
        send(client, response, 1)
        


def db_user_exists(username):
    connection = sqlite3.connect('books.db')
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM Users WHERE Username LIKE '{username}'")
    users_with_name = cursor.fetchall()
    connection.commit()
    connection.close()
    return len(users_with_name) > 0

def db_user_password_combo_exists(username, password):
    connection = sqlite3.connect('books.db')
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM Users WHERE Username = '{username}' AND Password = '{password}';")
    users = cursor.fetchall()
    connection.commit()
    connection.close()
    return len(users) > 0

def db_book_exists(title):
    connection = sqlite3.connect('books.db')
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM Books WHERE Title LIKE '{title}'")
    books_with_title = cursor.fetchall()
    connection.commit()
    connection.close()
    return len(books_with_title) > 0

# Function to fetch books from the SQLite database
def db_fetch_book_list():
    connection = sqlite3.connect('books.db')
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Books ORDER BY Title")
    books = cursor.fetchall()
    connection.close()
    return books

# Function to add a book to the database
def db_add_book(title, author):
    connection = sqlite3.connect('books.db')
    cursor = connection.cursor()
    cursor.execute(f"INSERT INTO Books (Title, Author) VALUES ('{title}', '{author}')")
    connection.commit()
    connection.close()

# Function to add a book to the database
def db_add_user(name, password):
    connection = sqlite3.connect('books.db')
    cursor = connection.cursor()
    cursor.execute(f"INSERT INTO Users (Username, Password) VALUES ('{name}', '{password}')")
    connection.commit()
    connection.close()


# Function to remove a book from the database
def db_remove_book(book_title):
    connection = sqlite3.connect('books.db')
    cursor = connection.cursor()
    cursor.execute(f"DELETE FROM Books WHERE Title = ?", (book_title,))
    connection.commit()
    connection.close()




# Main server function
def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 9999))
    server.listen(5)

    print("[*] Listening on 0.0.0.0:9999")

    while True:
        client_socket, addr = server.accept()
        print(f"[*] Accepted connection from: {addr[0]}:{addr[1]}")
        thread = threading.Thread(target=handle_client, args=(client_socket,))
        thread.start()

if __name__ == '__main__':
    main()
