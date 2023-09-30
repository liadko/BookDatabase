__author__ = 'Liad Koren'

import socket
import sys

server = None

def recv_from_server():
    global server
    
    try:
        msg_length = int.from_bytes(server.recv(1), "little")  # single msg length byte
        msg = server.recv(msg_length).decode()
    except Exception as e:
        return 'LEAVE' # if server malfunctions, we pretend it told us to leave
    
    return msg

def send(msg):
    global server
    message = msg.encode()
    msg_length = len(message)  # should be less than 256 if got up to here, fits in a single byte
    msg_length = msg_length.to_bytes(1, byteorder="little")  # convert to byte
    full_message = msg_length + message
    server.send(full_message)


def main():
    global server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect(('127.0.0.1', 9999))

    # Log In Or Register
    while True:
        print("\n1. Register")
        print("2. Login")
        method = input("Choose Sign In Method: ")
        if(method != "1" and method != "2"):
            print(f"Option '{method}' doesn't exist")
            continue
        
        while True:
            username = input("Username: ")
            if(len(username) > 4):
                break
            print("Username must be longer than 4 characters")
        
        while True:
            password = input("Password: ")
            if(len(password) > 5):
                break
            print("Password must be longer than 5 characters")
        
        if(method == "1"):
            send(f"REGISTER~{username}~{password}")
            response = recv_from_server()
            if(response == "USEREXISTS"):
                print("User Already Exists")
                continue
            elif(response == "SUCCESS"):
                print(f"Successfuly logged in as {username}")
                break
            else:
                print("Error When Registering")
                
        elif(method == "2"):
            send(f"LOGIN~{username}~{password}")
            response = recv_from_server()
            if(response == "INCORRECT"):
                print("Username Or Password is incorrect")
                continue
            elif(response == "SUCCESS"):
                print(f"Successfuly logged in as {username}")
                break
            else:
                print("Error When logging in")
        
    
    # Server-Client Conversation 
    while True:
        print("\nMenu:")
        print("1. Display books")
        print("2. Add a book")
        print("3. Remove a book")
        print("4. Display username")
        print("5. Log out")
        print("6. Quit\n")

        choice = input("Enter your choice: ")
        
        print()
        
        if choice == "1":
            send("GETBOOKS")
            books = recv_from_server()
            print(books)
        elif choice == "2":
            title = input("Enter book title: ")
            author = input("Enter author: ")
            send(f"ADD~{title}~{author}")
            response = recv_from_server()
            print(response)
        elif choice == "3":
            title = input("Enter book title to remove: ")
            send(f"REMOVE~{title}")
            response = recv_from_server()
            print(response)
        elif choice == "4":
            print(f"Currently Logged In As {username}")
        elif choice == "5":
            main()
        elif choice == "6":
            server.close()
            sys.exit()
        else:
            print("Invalid choice. Please try again.")
        
        

if __name__ == '__main__':
    main()
