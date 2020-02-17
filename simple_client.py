# Import socket module 
import socket			 

# Create a socket object 
s = socket.socket()	
print("Socket successfully created")	 

# Define the port on which you want to connect 
port = 5000			

# connect to the server on local computer 
s.connect(('127.0.0.1', port)) 

# receive data from the server 
print("Sending 'hello' message..")
s.sendall(b'hello')
print(s.recv(1024))
# close the connection 
s.close()	 
