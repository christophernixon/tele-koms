"""A proxy server and logging functions."""
import argparse
import logging
import re
import signal
import socket
import json
import urllib
import sys
import time
import threading


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

class proxy_server:
    """A proxy server for http/https connections."""

    def __init__(self, PORT, MAX_CONNECTIONS, MAN_CONSOLE_PORT):
        """Inialize a proxy server."""
        self.PORT = PORT
        self.MAX_CONNECTIONS = MAX_CONNECTIONS
        # The port the Management Console is listening on is required for passing messages
        self.MAN_CONSOLE_PORT = MAN_CONSOLE_PORT
        self.HOST = ''
        self.MAX_REQ_LEN = 4096
        self.CONNECTION_TIMEOUT = 10
        self.CACHE = {}
        self.USE_CACHE = False # A flag for whether or not to use the cache
        # Logging
        self.logger = setup_logging()
        # Setting up the socket for the server to listen on
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.logger.info('Socket created')
        self.bind_to_port()
        self.socket.listen(MAX_CONNECTIONS)
        self.logger.info('Proxy server now listening for maximum {0} connections on port {1}'.format(MAX_CONNECTIONS,self.PORT))
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
        """Serve any connections that attempt to connect to the port the server is listening on.

        ## Parameters:
        None
        ## Returns:
        None
        """
        while True:
            conn, addr = self.socket.accept()
            self.logger.info('Connected with ' + addr[0] + ' on port ' + str(addr[1]))
            d_thread = threading.Thread(target=self.client_thread, args=(conn,))
            d_thread.setDaemon(True)
            d_thread.start()
    
    def client_thread(self, conn):
        """Receive request from client, and relay request to relevant server, send any response back to client.

        ## Parameters:
        conn - A socket object with a connection to the client
        ## Returns:
        None
        """
        try:
            raw_request = conn.recv(self.MAX_REQ_LEN)
            if raw_request != b'':  
                is_not_blocked = True
                request = self.parse_request(raw_request)
                if not request: 
                    self.logger.error("No data found for request")

                # Send request to management console
                tmp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                tmp_socket.connect(('127.0.0.1', self.MAN_CONSOLE_PORT))
                message = json.dumps(request)
                tmp_socket.sendall(message.encode('latin-1'))
                while True:
                    data = tmp_socket.recv(self.MAX_REQ_LEN)
                    if (len(data) > 0):
                        if data.decode('latin-1') == 'HTTP/1.0 400 Site blacklisted\r\n':
                            is_not_blocked = False
                            conn.sendall(b'')
                            conn.close()
                    else:
                        break

                if is_not_blocked and self.is_https_request(request['request']):
                    self.logger.info("https request: {}".format(request['request']))
                    tmp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
                    tmp_socket.connect((request['url'], request['port']))
                    reply = "HTTP/1.0 200 Connection established\r\n"
                    reply += "Proxy-agent: Pyx\r\n"
                    reply += "\r\n"
                    conn.sendall(reply.encode())
                    conn.setblocking(0)
                    tmp_socket.setblocking(0)
                    while True:
                        try:
                            request = conn.recv(self.MAX_REQ_LEN)
                            tmp_socket.sendall(request)
                        except socket.error as err:
                            pass
                        except BlockingIOError as err:
                            time.sleep(0.1)
                        try:
                            reply = tmp_socket.recv(self.MAX_REQ_LEN)
                            conn.sendall(reply)
                        except socket.error as err:
                            pass
                        except BlockingIOError as err:
                            time.sleep(0.1)

                elif is_not_blocked: # It is a http request
                    # Check cache
                    if self.USE_CACHE and request['request'][0:255] in self.CACHE:
                        self.logger.info("Cache hit for: '{}...'".format(request['request'][0:20]))
                        conn.sendall(self.CACHE[request['request'][0:255]].encode('latin-1'))

                    else:
                        tmp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
                        tmp_socket.settimeout(self.CONNECTION_TIMEOUT)
                        tmp_socket.connect((request['url'], request['port']))

                        self.logger.info("Cache miss for: '{}...'".format(request['request'][0:20]))
                        tmp_socket.sendall(request['request'].encode('latin-1'))
                        while True:
                            data = tmp_socket.recv(self.MAX_REQ_LEN)
                            if (len(data) > 0):
                                conn.send(data)
                                cache_result = data.decode('latin-1')
                                 # Update cache
                                if self.USE_CACHE:
                                    self.logger.info("Updated cache for: '{}...'".format(request['request'][0:20]))
                                    cache_request = urllib.Request('http://'+request['url'])
                                    cache_response = urllib.Request.urlopen(cache_request)
                                    self.CACHE[request['request'][0:255]] = cache_response
                            else:
                                break
                        tmp_socket.close()
        except ConnectionError as conError:
            self.logger.error('Connection failed. Error Code : {}\nMessage {}'.format(str(conError.errno),str(conError)))
        except socket.timeout:
            self.logger.error("Socket timed out.")
            tmp_socket.close()
        except UnicodeDecodeError as err:
            self.logger.error('Unicode error. Message {}'.format(str(err)))
        finally:
            conn.close()
    
    def is_https_request(self, request):
        """Check whether request is https (True) or http (False).

        CHecks first line of request for 'CONNECT' keyword.
        ## Parameters:
        raw_request - The bytes of a request as returned from a socket.
        ##  Returns:
        is_http - Boolean
        """
        lines = request.split('\n')
        https_pos = lines[0].find("CONNECT")
        if https_pos == -1:
            return False
        else:
            return True
    
    def parse_request(self, raw_request):
        """Parse the webserver url and port(if available) out of a raw request.

        ## Parameters:
        raw_request - The bytes of a request as returned from a socket.
        ##  Returns:
        return_request - A dict containing keys url,port and request
        or 
        An empty dict.
        """
        # Make sure data is decoded from bytes to a string
        try:
            request = raw_request.decode('latin-1')
        except UnicodeDecodeError as err:
            raise err
        # Split request into lines
        lines = request.split('\n')
        pattern = re.compile("[^: ]*[:][0-9]+")
        # Search first line for url and port number
        match = re.search(pattern, lines[0])
        if match:
            url_port = match.group()
            port_pos = url_port.find(":") # find the port pos (if any)
            port = int(url_port[port_pos+1:])
        else:
            url_port = lines[0].split(' ')[1]
            port_pos = -1
            # Use default port
            port = 80
        http_pos = url_port.find("://")
        if (http_pos==-1):
            temp_url = url_port
        else:
            temp_url = url_port[(http_pos+3):]
        webserver_pos = temp_url.find("/")
        if webserver_pos == -1:
            webserver_pos = len(temp_url)
        url = ""
        if (port_pos == -1 or webserver_pos < port_pos): 
            url = temp_url[:webserver_pos] 
        else:
            url = temp_url[:port_pos] 
        self.logger.info("Parsed url as '{0}' and port as '{1}'.".format(url, port))
        return_request = {'port': port, 'url': url, 'request':request}
        return return_request
