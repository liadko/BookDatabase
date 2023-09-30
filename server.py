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
        print(f"Server Sending The Message: \'{msg}\'")
    
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
    
    request  = request_parts[0]
    username = request_parts[1]
    password = request_parts[2] 
    
    if(request == "REGISTER"):
        if(user_exists(username)):
            send(client, "USEREXISTS", 1)
            return False
        
        # success!
        add_user(username, password)
        return True
        
    if(request == "LOGIN"):
        if(not user_password_combo_exists(username, password)):
            send(client, "INCORRECT", 1)
            return False
        
        # success!
        return True
    
    
    print("Unrecognised Registeration/login message")
    return False        
            

# Function to handle client requests
def handle_client(client:socket):
    
    success = False
    while(success == False):
        success = try_sign_in(client)
        
        if(success == None):
            print("Client Left While Signing In")
            client.close()
            return
        
    send(client, "SUCCESS", 1)
    
    while True:
        
        msg = recv_from_client(client)

        
        if(not msg):
            break
        
        incoming_msg = msg.split("~")
        
        if (incoming_msg[0] == 'GETBOOKS'):
            books = fetch_books()
            if(len(books) == 0):
                send(client, "Library Is Empty.")
            else:
                s = "\n   " + "Title".ljust(25, ' ') + " Author\n"
                for i, book in enumerate(books):
                    s += f"{i+1}. {str(book[1]).ljust(25, ' ')} {str(book[2])}\n"
                send(client, s)
            continue
        elif(incoming_msg[0] == 'ADD'):
            if(len(incoming_msg) != 3):
                send(client, "Invalid Add request.")
            elif(book_exists(incoming_msg[1])):
                send(client, f"Book Titled {incoming_msg[1]} already exists.")
            else:
                add_book(incoming_msg[1], incoming_msg[2])
                send(client, f"Successfuly Added Book Titled {incoming_msg[1]} To Library.")
            continue
        elif(incoming_msg[0] == 'REMOVE'):
            if(len(incoming_msg) != 2):
                send(client, "Invalid Remove request.")
            elif(not book_exists(incoming_msg[1])):
                send(client, f"Book Titled {incoming_msg[1]} does not exist.")
            else:
                remove_book(incoming_msg[1])
                send(client, f"Successfuly Removed Book Titled {incoming_msg[1]} From Library.")
            continue
        elif(incoming_msg[0] == 'UPDATE'):
            pass  
            continue
        
        
        elif(msg == 'LEAVING'):
            pass
        
        else:
            print(f"UNHANDLED MSG FROM CLIENT: {msg}")
        


    client.close()


def user_exists(username):
    connection = sqlite3.connect('books.db')
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM Users WHERE Username LIKE '{username}'")
    users_with_name = cursor.fetchall()
    connection.commit()
    connection.close()
    return len(users_with_name) > 0

def user_password_combo_exists(username, password):
    connection = sqlite3.connect('books.db')
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM Users WHERE Username = '{username}' AND Password = '{password}';")
    users = cursor.fetchall()
    connection.commit()
    connection.close()
    return len(users) > 0

def book_exists(title):
    connection = sqlite3.connect('books.db')
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM Books WHERE Title LIKE '{title}'")
    books_with_title = cursor.fetchall()
    connection.commit()
    connection.close()
    return len(books_with_title) > 0

# Function to fetch books from the SQLite database
def fetch_books():
    connection = sqlite3.connect('books.db')
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Books ORDER BY Title")
    books = cursor.fetchall()
    connection.close()
    return books

# Function to add a book to the database
def add_book(title, author):
    connection = sqlite3.connect('books.db')
    cursor = connection.cursor()
    cursor.execute(f"INSERT INTO Books (Title, Author) VALUES ('{title}', '{author}')")
    connection.commit()
    connection.close()

# Function to add a book to the database
def add_user(name, password):
    connection = sqlite3.connect('books.db')
    cursor = connection.cursor()
    cursor.execute(f"INSERT INTO Users (Username, Password) VALUES ('{name}', '{password}')")
    connection.commit()
    connection.close()


# Function to remove a book from the database
def remove_book(book_title):
    connection = sqlite3.connect('books.db')
    cursor = connection.cursor()
    cursor.execute(f"DELETE FROM Books WHERE Title = ?", (book_title,))
    connection.commit()
    connection.close()

# Function to update reading progress in the database
def update_reading(book_details):
    connection = sqlite3.connect('books.db')
    cursor = connection.cursor()
    cursor.execute("UPDATE Books SET CurrentPage=?, TotalPages=? WHERE Title=?", book_details.split(','))
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
