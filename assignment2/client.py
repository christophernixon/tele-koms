"""Client for communicating with secure social media application server."""
import argparse
import signal
import sys
import json
import threading
import requests

exit_program = False

class client:
    """Client for communicating with secure social media application server."""
    auth_token = ""

    def __init__(self, PORT=5000):
        """Start the client, with an optional argument for setting the port of the server."""
        self.server_port = PORT
        self.local_route = 'http://127.0.0.1:'+ str(self.server_port)
        signal.signal(signal.SIGINT, self.shutdown)
        # Start a thread for user inputs.
        self.user_input_thread = threading.Thread(target=self.serve_user_input)
        self.user_input_thread.start()

    def serve_user_input(self):
        """Handle any user inputs.

        Continuously waits for user inputs. Upon receiving a user input, checks if the input is valid.
        If the input is valid it performs the relevant action, if not it gives an error message.

        ## Parameters:
        None
        ## Returns:
        None
        """
        print("Welcome to a secure social media application.")
        option_string = ("""Please select one of the following options:\n
                            1) Ping server\n
                            2) Send message to server\n
                            3) Get all message sent to server\n
                            4) Login\n
                            5) Register\n
                            6) Exit\n""")
        while True:
            user_input = input(option_string)
            try:
                selected_option = int(user_input)
            except ValueError:
                print("Your selection of {0} was invalid, please enter a digit corresponding to one of the options.".format(user_input))
                continue
            if selected_option == 1:
                self.ping_server()
            elif selected_option == 2:
                self.send_server_message()
            elif selected_option == 3:
                self.get_message_dump()
            elif selected_option == 4:
                self.log_user_in()
            elif selected_option == 5:
                self.register_user()
            elif selected_option == 6:
                self.shutdown(signal.SIGINT,0)
            else:
                print("{0} is not a valid option number.".format(selected_option))
            global exit_program
            if exit_program: 
                break

    def shutdown(self, signum, frame):
        """Handle exiting server. Join all threads."""
        print("Exiting program")
        exit_program = True
        main_thread = threading.currentThread()
        for t in threading.enumerate():
            if t is main_thread:
                print("Attempt to join() {}".format(t.getName()))
                continue
            t.join()
        sys.exit(0)

    def send_server_message(self):
        """Send a message to the server."""
        message_route = self.local_route + '/messages'
        message = input("Please enter the message you'd like to send, followed by enter.")
        dict_data = {'message':message, 'auth_token':self.auth_token}
        raw_response = requests.post(message_route, json=dict_data)
        print(json.dumps(raw_response.text, indent=2))
        print("Message sent.")
    
    def log_user_in(self):
        """Log user into server."""
        login_route = self.local_route + '/login'
        email = input("Please enter the email address you registered with.")
        dict_data = {'email':email}
        raw_response = requests.post(login_route, json=dict_data)
        json_response = raw_response.json()
        # If sucessful login, return.
        if raw_response.status_code == 200:
            print(json_response)
            return
        elif raw_response.status_code == 404:
            print(json_response['message'])

            # give user option of registering
            yes_no = input("Would you like to register as a user? [y/n]")
            while yes_no not in ["y", "n"]:
                yes_no = input("Invalid option. Please type 'y' or 'n':")
            if yes_no == 'n':
                print("Unable to log user in.")
                return
            if yes_no == 'y':
                self.register_user()


    def register_user(self):
        """Register user into server."""
        register_route = self.local_route + '/register'
        email = input("Please enter the email address you would like to register with.")
        username = input("Please enter the username you would like to register with:")
        dict_data = {'email':email, 'username':username}
        raw_response = requests.post(register_route, json=dict_data)
        json_response = raw_response.json()
        if raw_response.status_code == 201:
            print(json_response['message'])
            self.auth_token = json_response['auth_token']
            return
        else:
            print(json_response['message'])



    def get_message_dump(self):
        """Get message dump from server."""
        message_dump_route = self.local_route + '/allmessages'
        raw_response = requests.get(url=message_dump_route, json={'auth_token':self.auth_token})
        print("Message dump:")
        print(json.dumps(raw_response.text, indent=2))

    def ping_server(self):
        """Ping server."""
        ping_route = self.local_route + '/ping'
        raw_response = requests.get(url=ping_route)
        # response = raw_response.json()
        print(json.dumps(raw_response.text, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port_num", type=int, default=5000, help="Port number server is connected to.")
    args = parser.parse_args()
    client(args.port_num)