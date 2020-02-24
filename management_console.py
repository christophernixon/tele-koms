"""A management console for monitoring and controlling a proxy server."""
import argparse
import json
import signal
import socket
import logging
import sys
import threading

from proxy_server import proxy_server


class management_console:
    """A console for starting and managing a proxy server."""

    def __init__(self, PORT, MAX_CONNECTIONS):
        """Inialize a management console.
        
        Starts a management console on the given port or as close as possible
        and starts a proxy server on a nearby port.
        """
        self.PORT = PORT
        self.MAX_CONNECTIONS = MAX_CONNECTIONS
        self.HOST = ''
        self.MAX_REQ_LEN = 4096
        self.CONNECTION_TIMEOUT = 10
        self.logger = setup_logging()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.logger.info('Socket created')
        signal.signal(signal.SIGINT, self.shutdown)
        self.bind_to_port()
        self.PROXY_PORT = self.PORT + 1
        self.socket.listen(MAX_CONNECTIONS)
        self.logger.info('Management console now listening for maximum {0} connections on port {1}'.format(MAX_CONNECTIONS,self.PORT))
        # Start a thread for proxy server.
        self.PROXY_SERVER_THREAD = threading.Thread(target=proxy_server, args=(self.PROXY_PORT, self.MAX_CONNECTIONS, self.PORT,))
        self.PROXY_SERVER_THREAD.start()
        # self.PROXY_SERVER = proxy_server(self.PROXY_PORT, self.MAX_CONNECTIONS, self.PORT)
        self.serve()
    
    def bind_to_port(self):
        """Bind server to port.

        This will attempt to bind the server to the given port. If this port is already
        in use, the server will try up to the next ten ports to find one not in use, if
        one is found it will be bound to, if not the server will abort starting.
        ## Parameters:
        None
        ## Returns:
        None
        """
        try:
            self.socket.bind((self.HOST, self.PORT))
        except socket.error as err:
            self.logger.error('Bind failed. Error Code : {}\nMessage {}'.format(str(err.errno),str(err)))
            if err.errno == 48:
                self.logger.info("Attempting to find address not already in use.")
                attempted_address = self.PORT
                address_found = False
                while self.PORT < attempted_address+10:
                    self.PORT += 1
                    try:
                        self.socket.bind((self.HOST, self.PORT))
                        address_found = True
                        self.logger.info('Found available address at port {}'.format(self.PORT))
                        break
                    except socket.error as err:
                        self.logger.info('Port {} already in use'.format(self.PORT))
                        pass
                if not address_found:
                    self.logger.error("Tried up to port {} but unable to find free port, aborting server start.".format(self.PORT))
                    sys.exit()
            else:
                sys.exit()
        self.logger.info('Socket bind complete')
    
    def serve(self):
        """Serve any messages that the proxy server sends to the port the server is listening on.

        ## Parameters:
        None
        ## Returns:
        None
        """
        # Start a thread for listening to user inputs.
        d_thread = threading.Thread(target=self.serve_user_input)
        d_thread.setDaemon(True)
        d_thread.start()

        while True:
            conn, addr = self.socket.accept()
            self.logger.info('Connected with proxy server on port ' + str(addr[1]))
            d_thread = threading.Thread(target=self.proxy_message, args=(conn,))
            d_thread.setDaemon(True)
            d_thread.start()
    
    def proxy_message(self, conn):
        """Recieve a message from the proxy server.

        ## Parameters:
        conn - A socket object with a connection to the proxy server
        ## Returns:
        None
        """
        try:
            raw_request = conn.recv(self.MAX_REQ_LEN)
            if raw_request != b'':
                request = json.loads(raw_request)
                print(request)
        except ConnectionError as conError:
            self.logger.error('Connection failed. Error Code : {}\nMessage {}'.format(str(conError.errno),str(conError)))
        

    def serve_user_input(self):
        """Handle any user inputs.

        Continuously waits for user inputs. Upon receiving a user input, checks if the input is valid.
        If the input is valid it performs the relevant action, if not it gives an error message.

        ## Parameters:
        None
        ## Returns:
        None
        """
        while True:
            print("Waiting for input")
            user_input = input("Management console live.\n")
            print("User inputted: {}".format(user_input))
    
    def shutdown(self, signum, frame):
        """Handle exiting server. Join all threads."""
        self.logger.warning("Ctrl+C inputted so shutting down server")
        main_thread = threading.currentThread()
        for t in threading.enumerate():
            if t is main_thread:
                self.logger.error("Attempt to join() {}".format(t.getName()))
                continue
            t.join()
            self.socket.close()
        sys.exit(0)
    

def setup_logging():
    """Initialize logging to file and console."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    project_loc = "/Users/chrisnixon/yr3/semes2/telecoms/tele-koms/"
    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(project_loc + "logs/{}.log".format(__name__), mode='w')
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
    parser.add_argument("-c","--max_cons", type=int, default=10, help="Maximum number of connections to hold before dropping one")
    args = parser.parse_args()
    management_console(args.port_num, args.max_cons)
