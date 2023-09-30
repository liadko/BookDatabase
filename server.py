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

def send(client, msg):
    message = msg.encode() # string to bytes
    msg_length = len(message) # get length int
    msg_length = msg_length.to_bytes(1, byteorder='little') # int to byte
    full_message = msg_length + message # append msg length to msg 
    client.send(full_message)

# Function to handle client requests
def handle_client(client):
    
    while(True):
        msg:str = recv_from_client(client)
        incoming_msg = msg.split("~")
        
        if(len(incoming_msg) != 3):
            print("Client Has Sent Invalid")
            send(client, "INCORRECT signin message")
        
        elif(incoming_msg[0] == "REGISTER"):
            if(user_exists(incoming_msg[1])):
                send(client, "USEREXISTS")
                continue
            add_user(incoming_msg[1], incoming_msg[2])
            send(client, "SUCCESS")
            break
            
        elif(incoming_msg[0] == "LOGIN"):
            if(user_password_combo_exists(incoming_msg[1], incoming_msg[2])):
                send(client, "SUCCESS")
                break
            else:
                send(client, "INCORRECT")
        else:
            print("Unrecognised Registeration/login message")
    
    
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
