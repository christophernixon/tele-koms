import socket
import sys
from threading import Thread

HOST = ''	# Symbolic name meaning all available interfaces
PORT = 5000	# Arbitrary non-privileged port

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print('Socket created')

try:
	s.bind((HOST, PORT))
except socket.error as msg:
	print('Bind failed. Error Code : {}\nMessage {}'.format(str(msg.errno),str(msg)))
	sys.exit()
	
print('Socket bind complete')

s.listen(10)
print('Socket now listening')

def client_thread(conn):
    #Sending message to connected client
    conn.send(b'Welcome to the server. Type something and hit enter\n')

    #infinite loop so that thread won't end.
    while True:
        data = conn.recv(1024)
        reply = b'OK...' + data
        recieved_string = data.decode('utf-8')
        print("Recieved {} from client".format(recieved_string))
        if not data: 
            break
        conn.sendall(reply)
    conn.close()

# now keep talking with the client
while 1:
    # wait to accept a connection - blocking call
    conn, addr = s.accept()
    print('Connected with ' + addr[0] + ' on port ' + str(addr[1]))
    # start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the function.
    Thread(target=client_thread, args=(conn,)).start()
s.close()

