# Proxy Server with Management Console
I decided to write my proxy server in python. There are two main python files, one which contains the Management Console and the other which contains the proxy server. 
### Proxy server
This module contains a proxy server class, and a method for setting up logging. I will discuss the logging details later on. 

The proxy server is initialised with a port that it will listen on, and a maximum number of connections at any one time. There were some issues while debugging the application of the given port being already taken, due to a lot of starting and stopping of the application. Some logic for searching for an available port was implememnted because of these issues.

Once a suitable port has been found, the server will continuously listen on this port, every time it gets a connection it starts a thread and passes the connection onto this thread. This multi-threading allows it to be highly available.

Upon recieving a connection, the request passed to the proxy server is passed to the management console, to pass the message and determine whether the request refers to a blacklisted site. If the site is not blacklisted, it is determined by parsing the request whether it is a http or https request. These two cases are handled seperately, in the case of https a sucessfull connection response is sent to the web browser, then the browser and web server are allowed to perform their TLS handshake without interference. 

### Management console
The management console is initialised as a server on a port, and the same port-selection logic is implemented. It is started from the command line, and an argument parsing library `argparse` is used to provide helpful messages for what command line arguments are required. 

Once the management console is bound to a port it starts a proxy server on a nearby port. Having these as essentially two servers means communications between them are very straightforward. 

The management console is multi-threaded, with a dedicated thread for listening to and responding to user input. This thread listens for user input and takes appropriate actions based on the input, for example blacklisting a website. Blacklisting is implemented, and sites can be removed from the blacklist by 'whitelisting' them.

Upon recieving a message from the proxy server, the management console checks whether the sent request is in the blacklist, in which case it communicates this to the proxy server.

For both the management console and the proxy server there is a function set up to be executed upon recieving a Ctrl-c input which will properly close down all the threads. 

### Logging
Logging is set up for both the management console and the proxy server. There are multiple levels of logging, such as `info`, `debug` or `error`. Everything that is logged is written to log files contained within a `/log` folder. Anything of a logging level of error is printed to console as well, for added visibility. The log files are also named after the module from which they came. 