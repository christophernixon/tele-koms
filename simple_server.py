import socket
import sys
import argparse
import logging
from threading import Thread

def setup_logging():
    """Setup logging to file and console."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler("logs/{}.log".format(__name__), mode='w')
    c_handler.setLevel(logging.WARNING)
    # Create formatters and add it to handlers
    c_format = logging.Formatter('%(name)s - %(levelname)s - %(lineno)d - %(message)s')
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s')
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)
    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    return logger

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("port_num", type=int, help="Port number for the server to listen on.")
    parser.add_argument("-c","--max_cons", type=int, help="Maximum number of connections to hold before dropping one")
    args = parser.parse_args()
    if args.max_cons:
        MAX_CONNECTIONS = args.max_cons
    else:
        MAX_CONNECTIONS = 10
    PORT = args.port_num
    logger = setup_logging()

HOST = ''	# Symbolic name meaning all available interfaces

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
logger.info('Socket created')

try:
	s.bind((HOST, PORT))
except socket.error as msg:
	logger.error('Bind failed. Error Code : {}\nMessage {}'.format(str(msg.errno),str(msg)))
	sys.exit()
	
logger.info('Socket bind complete')

s.listen(MAX_CONNECTIONS)
logger.info('Socket now listening for maximum {1} connections on port {0}'.format(PORT, MAX_CONNECTIONS))

def client_thread(conn):
    #Sending message to connected client
    conn.send(b'Welcome to the server. Type something and hit enter\n')

    #infinite loop so that thread won't end.
    while True:
        try:
            data = conn.recv(1024)
            reply = b'OK...' + data
            recieved_string = data.decode('utf-8')
            logger.info("Recieved {} from client".format(recieved_string))
            if not data: 
                break
            conn.sendall(reply)
        except ConnectionError as conError:
            logger.error('Connection failed. Error Code : {}\nMessage {}'.format(str(conError.errno),str(conError)))
    conn.close()

# now keep talking with the client
while 1:
    # wait to accept a connection - blocking call
    conn, addr = s.accept()
    logger.info('Connected with ' + addr[0] + ' on port ' + str(addr[1]))
    # start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the function.
    Thread(target=client_thread, args=(conn,)).start()
s.close()
