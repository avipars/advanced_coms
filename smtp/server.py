import base64
import re
import socket
import time

import SMTP_protocol

user_names = {"shooki": "abcd1234", "barbie": "helloken"}


# helper functions to avoid repetition
def decode_b64(message):
    return (
        base64.b64decode(message).decode()
        if isinstance(message, str)
        else base64.b64decode(message.decode())
    )  # avoid python issue of decoding a string (as we cannot), but we can decode a byte array


def encode_b64(message):  # ternary operators in python to check if string or byte array
    return (
        base64.b64encode(message.encode())
        if isinstance(message, str)
        else base64.b64encode(message).encode()
    )


def b64_setup(message):  # for sending b64 to client (auth)
    return encode_b64(message).decode()


def create_initial_response():
    curr_date = str(
        time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime())
    )  # timestamp
    # 220 SMTP_protocol.SERVER_NAME SMTP service ready
    return f"{SMTP_protocol.SMTP_SERVICE_READY}-{SMTP_protocol.SERVER_NAME} {curr_date}\r\n SMTP service ready for mail".encode()


# Example of how a server function should look like
def create_EHLO_response(client_message):
    """Check if client message is legal EHLO message
    If yes - returns proper Hello response
    Else - returns proper protocol error code"""
    if not client_message.startswith(SMTP_protocol.EHLO):
        return ("{}".format(SMTP_protocol.COMMAND_SYNTAX_ERROR)).encode(), False
    client_name = client_message.split()[1]
    return (
        "{}-{} Hello {}\r\n".format(
            SMTP_protocol.REQUESTED_ACTION_COMPLETED,
            SMTP_protocol.SERVER_NAME,
            client_name,
        ).encode(),
        True,
    )


# return two vals, first is what to send to client... 2nd is false if there is an error or true otherwise this way it makes checking in the main part of the code easier
# stage 3 - auth login
def create_AUTH_response(client_message):
    if client_message.startswith(
            SMTP_protocol.AUTH_LOGIN):  # valid client message
        return (
            "{}-{}\r\n".format(
                SMTP_protocol.AUTH_INPUT, b64_setup("Username")
            ).encode(),
            True,
        )  # encode this in b64 and send
    else:
        return (
            "{} AUTH LOGIN command not received\r\n".format(
                SMTP_protocol.COMMAND_SYNTAX_ERROR
            ).encode(),
            False,
        )


# message will be username
def create_USER_response(client_message):
    if client_message in user_names.keys():  # go through dictionary
        return (
            "{}-{}\r\n".format(
                SMTP_protocol.AUTH_INPUT, b64_setup("Password")
            ).encode(),
            True,
        )  # encode this in b64 and send to ask user to enter password
    else:
        return (
            "{} Authentication credentials invalid\r\n".format(
                SMTP_protocol.INCORRECT_AUTH
            ).encode(),
            False,
        )  # dont be verbose with error as easier to bruteforce


# ensure user&password combo exists
def create_PASSWORD_response(user: str, passw: str):
    if (
        user in user_names.keys() and user_names[user] == passw
    ):  # verify key exists and password matches key
        return (
            "{} Authentication succeeded\r\n".format(
                SMTP_protocol.AUTH_SUCCESS
            ).encode(),
            True,
        )
    else:
        return (
            "{} Authentication credentials invalid\r\n".format(
                SMTP_protocol.INCORRECT_AUTH
            ).encode(),
            False,
        )  # user password mismatch


def create_MAIL_FROM_response(client_message):
    if client_message.startswith(SMTP_protocol.MAIL_FROM):  # valid command
        return (
            "{} OK\r\n".format(
                SMTP_protocol.REQUESTED_ACTION_COMPLETED).encode(),
            True,
        )  # 250 ok per wireshark
    else:
        return (
            "{} No sender found\r\n".format(
                SMTP_protocol.COMMAND_SYNTAX_ERROR
            ).encode(),
            False,
        )


def create_RCPT_TO_response(client_message):
    if client_message.startswith(SMTP_protocol.RCPT):
        return (
            "{} Accepted\r\n".format(
                SMTP_protocol.REQUESTED_ACTION_COMPLETED).encode(),
            True,
        )  # 250 accepted as per wireshark
    else:
        return (
            "{} No recipient set\r\n".format(
                SMTP_protocol.COMMAND_SYNTAX_ERROR
            ).encode(),
            False,
        )


def create_DATA_response(client_message):
    if client_message.startswith(
        SMTP_protocol.DATA
    ):  # getting ready to receive email bodies
        return (
            '{} Enter message, ending with "." on a line by itself\r\n'.format(
                SMTP_protocol.ENTER_MESSAGE
            ).encode(),
            True,
        )  # had to escape the period in python
    else:
        return (
            "{} No data found\r\n".format(
                SMTP_protocol.COMMAND_SYNTAX_ERROR).encode(),
            False,
        )


def create_ERROR_RESPONSE():
    """Error message for too many messages sent by client"""
    return "{} Message is too long\r\n".format(
        SMTP_protocol.MSG_TOO_LONG).encode()


def create_CONTENT_RESPONSE(client_message):
    """
    gets email and checks if ends with SMTP_protocol.EMAIL_END
    """
    if client_message.endswith(
            SMTP_protocol.EMAIL_END):  # done sending content
        return (
            "{} OK\r\n".format(
                SMTP_protocol.REQUESTED_ACTION_COMPLETED).encode(),
            True,
        )  # 250 ok per wireshark
    else:
        return (
            "{} No end email deliminator found\r\n".format(
                SMTP_protocol.COMMAND_SYNTAX_ERROR
            ).encode(),
            False,
        )


def create_QUIT_response(client_message):
    print(client_message)
    if client_message.startswith(SMTP_protocol.CLIENT_QUIT):
        return (
            "{} {} closing connection\r\n".format(
                SMTP_protocol.GOODBYE, SMTP_protocol.SERVER_NAME
            ).encode(),
            True,
        )  # per wireshark
    else:
        return (
            "{} No quit message from client\r\n".format(
                SMTP_protocol.COMMAND_SYNTAX_ERROR
            ).encode(),
            False,
        )


def get_from_client(
    client_socket, to_print=True
):  # get message from client, avoid duplicate code
    msg = client_socket.recv(SMTP_protocol.MSG_SIZE).decode()
    if to_print:
        print(msg)
    return msg


def handle_SMTP_client(client_socket):
    try:
        # 1 send initial message
        message = create_initial_response()
        client_socket.send(message)
        print(message.decode())

        # 2 receive and send EHLO
        response, res = create_EHLO_response(get_from_client(client_socket))
        client_socket.send(response)
        if res:
            print("EHLO worked")
        else:
            print("Error client EHLO")
            return

        # 3 receive and send AUTH Login
        response, res = create_AUTH_response(get_from_client(client_socket))
        client_socket.send(response)
        if res:
            print("AUTH LOGIN worked")
        else:
            print(
                f"Auth login error {response.decode()}"
            )  # issue with the auth response function
            return

        # 4 receive and send USER message
        decoded_user = decode_b64(get_from_client(client_socket)).split()[
            0
        ]  # decode user (in 1st arg)
        response, res = create_USER_response(
            decoded_user)  # check if user is valid
        client_socket.send(response)
        if res:
            print(f"User entered: {decoded_user}")
        else:
            print(
                f"Error with user: {response.decode()}"
            )  # print error message with details for admin to see
            return

        # 5 password
        decoded_pass = decode_b64(get_from_client(client_socket)).split()[
            0
        ]  # decode password (1st arg)
        response, res = create_PASSWORD_response(decoded_user, decoded_pass)
        client_socket.send(response)
        if res:
            print(f"User {decoded_user} logged in successfully")
        else:
            print(
                f"Error: Password login for {decoded_user} credentials wrong"
            )  # print error message
            return

        # 6 mail from
        response, res = create_MAIL_FROM_response(
            get_from_client(client_socket))
        client_socket.send(response)
        if res:
            print("MAIL FROM worked")
        else:
            print("Error: MAIL FROM failed")
            return

        # 7 rcpt to
        response, res = create_RCPT_TO_response(
            get_from_client(client_socket)
        )  # (simple case of only 1 recipient)
        client_socket.send(response)
        if res:
            print("RCPT TO worked")
        else:
            print("Error: RCPT TO failed")
            return

        # 8 DATA - preamble to content
        response, res = create_DATA_response(get_from_client(client_socket))
        client_socket.send(response)
        if res:
            print("DATA command worked")
        else:
            print("Error: DATA command failed")
            return

        # 9 email content
        # The server should keep receiving data, until the sign of end email is
        # received
        proceed = True  # control flag
        i = 0  # how long to go for
        # store contents, can come in several fragments/packets if message is
        # big
        email_content = []
        while (
            proceed and i < SMTP_protocol.MAX_MESSAGES
        ):  # limit max amount to avoid being overloaded
            message = get_from_client(client_socket, False)  #
            if not message:  # runt packet
                print("Error: Empty packet from client, connection might be closed")
                proceed = False

            email_content.append(message)  # add to array
            i += 1  # i++
            if message.endswith(
                SMTP_protocol.EMAIL_END
            ):  # check that last email has the end mark
                proceed = False  # exit

        # after loop
        if (
            i >= SMTP_protocol.MAX_MESSAGES
        ):  # we want to avoid being overloaded - or sent too many messages,
            # break away, send error message and close connection
            print(
                "Error: exceeded the maximum number of fragmented messages allowed by server"
            )
            response = create_ERROR_RESPONSE()
            client_socket.send(response)
            return

        print("Email content received:")
        print("\n".join(email_content))  # combine all to print nicely
        response, res = create_CONTENT_RESPONSE(
            email_content[-1]
        )  # check last message for end mark
        client_socket.send(response)  # send confirmation
        if res:
            print("Client finished email content stage successfully")
        else:
            print("Error: Email content failed")
            return

        # 10 quit
        message = get_from_client(client_socket)
        response, res = create_QUIT_response(message)
        client_socket.send(response)
        if res:
            print("Client quit successfully")
        else:
            print("Error: client QUIT command failed")
            return

    except Exception as e:
        print(f"Generic server error: {e}")


def init_server():
    # Open a socket
    server_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM)  # ipv4 via tcp
    server_socket.bind(
        (SMTP_protocol.SERVER_ADDRESS, SMTP_protocol.PORT)
    )  # hog the port
    server_socket.listen()  # start listening
    print(
        "Listening for connections on ip {}:{}".format(
            SMTP_protocol.SERVER_ADDRESS, SMTP_protocol.PORT
        )
    )
    return server_socket  # pass socket back


def main():
    try:
        server_socket = init_server()  # call init function
        while (
            True
        ):  # keep on accepting new users (and loop forever while waiting for clients)
            client_socket, client_address = server_socket.accept()
            print(f"New connection received: {client_address}")
            client_socket.settimeout(
                SMTP_protocol.SOCKET_TIMEOUT)  # wait for seconds
            handle_SMTP_client(client_socket)
            print(f"Client Connection closed: {client_address}")
    # handle error cases & fail gracefully below
    except ConnectionResetError as cre:
        print(f"Connection forcibly closed on server {cre}")
    except ConnectionRefusedError as cree:
        print(f"S Connection refused {cree}")
    except ConnectionAbortedError as cae:
        print(f"Connection aborted on server {cae}")
    except ConnectionError as ce:
        print(f"Generic connection error on server {ce}")
    except ValueError as ve:  # shouldn't happen unless they dont send bytes/strings
        print(f"Client is doing bad stuff with values {ve}")
    except socket.timeout as st:
        print(f"S Error: Socket timed out before end {st}")
    except socket.error as se:
        print(f"S Socket error {se}")


if __name__ == "__main__":
    # Call the main handler function
    main()
