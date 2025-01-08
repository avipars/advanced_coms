import base64
import socket
import time

import SMTP_protocol

# email configurations

# Add the minimum required fields to the email (i added more stuff for fun
# and to check the email split)
INNER_MSG = (
    "Hello darkness my old friend, we come together once again " * 10
)  # repeat this x times
EMAIL_TEXT = (
    f"From: {SMTP_protocol.USER}@{SMTP_protocol.DOMAIN}\r\n"
    f"To: {SMTP_protocol.RCPT}@{SMTP_protocol.DOMAIN}\r\n"
    "Subject: Test Email\r\n"
    "\r\n" + INNER_MSG  # the actual stuff we care for
)


# helper functions to avoid repetition
def decode_b64(message):
    return (
        base64.b64decode(message).decode()
        if isinstance(message, str)
        else base64.b64decode(message.decode())
    )  # avoid python issue of decoding a string (as we cannot), but we can decode a byte array


def encode_b64(message):
    return (
        base64.b64encode(message.encode())
        if isinstance(message, str)
        else base64.b64encode(message).encode()
    )


def quit(my_socket: socket, msg, with_error=True):
    """Nice way to quit and print some message while doing so"""
    print(
        f"\nError - Client closing socket:  {msg}") if with_error else print(msg)
    my_socket.close()
    return  # exit


def create_EHLO():
    return "{} {}\r\n".format(
        SMTP_protocol.EHLO,
        SMTP_protocol.CLIENT_NAME).encode()


# More functions must follow, in the form of create_EHLO, for every client
# message
def create_AUTH_LOGIN():
    return SMTP_protocol.AUTH_LOGIN.encode()


def create_AUTH_VAL(msg):  # encode message to base64 (username, password)
    return encode_b64(msg) + b"\r\n"  # convert ending to bytes


def create_MAIL_FROM(sender=SMTP_protocol.USER):
    return (
        f"{SMTP_protocol.MAIL_FROM} <{sender}>\r\n".encode()
    )  # given email address already


def create_RCPT_TO(recipient):
    return (
        f"{SMTP_protocol.RCPT} <{recipient}>\r\n".encode()
    )  # given email address already


def create_DATA():
    return SMTP_protocol.DATA.encode()


def create_CONTENT(msg):
    return (
        f"{msg}{SMTP_protocol.EMAIL_END}".encode()
    )  # append end of email here, ... user can't forget


def create_QUIT():
    return SMTP_protocol.CLIENT_QUIT.encode()


def req_comp(response):
    return response.startswith(SMTP_protocol.REQUESTED_ACTION_COMPLETED)


def too_long(response):
    return response.startswith(SMTP_protocol.MSG_TOO_LONG)


def auth_input(response):
    return response.startswith(SMTP_protocol.AUTH_INPUT)


def init_session():
    """Connect to server - Session Initiation"""
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # ip and tcp
    try:
        my_socket.connect(
            (SMTP_protocol.SERVER_ADDRESS, SMTP_protocol.PORT)
        )  # send tuple to connect to  (server port)
        print(f"Client connected to server successfully")
        return my_socket
    except socket.error as er:  # captures errors on initial connect
        quit(my_socket, f"{er} from client to server ", False)
        return None  # nada, we are done


def get_from_serv(my_socket):
    msg = my_socket.recv(SMTP_protocol.MSG_SIZE).decode()
    print(msg)  # helper function to save on lines of code
    return msg


def send_RCPT_TO(
        my_socket,
        recipient=SMTP_protocol.RCPT,
        domain=SMTP_protocol.DOMAIN):
    """Send SMTP_protocol.RCPT TO message to server"""
    my_socket.send(create_RCPT_TO(f"{recipient}@{domain}"))  # full email
    response = get_from_serv(my_socket)
    return req_comp(response)


def send_MAIL_FROM(
        my_socket,
        sender=SMTP_protocol.USER,
        domain=SMTP_protocol.DOMAIN):
    """Send MAIL FROM message to server"""
    my_socket.send(create_MAIL_FROM(f"{sender}@{domain}"))  # adds full address
    response = get_from_serv(my_socket)
    return req_comp(response)


def main():
    # try to initiate connection with server, if worked then skip the
    # following and go to TRY
    my_socket = init_session()
    # retry failed connection - works great if you started client first or
    # have >1 client trying to connect
    i = 1  # number of tries so far
    while (
        my_socket is None and i <= SMTP_protocol.FAILED_ATTEMPTS
    ):  # loop over till get successful connection or exceed the failed bounds
        # each time let's give it exponentially longer to wait
        time.sleep(i**2)
        print(
            f"No connection to {SMTP_protocol.SERVER_ADDRESS}:{SMTP_protocol.PORT}, retry #{i}, sleeping {i**2} seconds"
        )
        my_socket = init_session()  # re-try connection
        i += 1  # increment

    if (
        i > SMTP_protocol.FAILED_ATTEMPTS and my_socket is None
    ):  # if exceeded max attempts and still didn't succeed
        print(
            f"Exiting after {i-1} unsuccessful attempts"
        )  # we are done (including the 1st try before loop)
        return

    try:
        # 1 server welcome message
        # Check that the welcome message is according to the protocol
        if get_from_serv(my_socket).startswith(
                SMTP_protocol.SMTP_SERVICE_READY):
            print("Welcome message is valid")
        else:
            quit(my_socket, f"SMTP SERVICE READY command failed")
            return

        # 2 EHLO message
        my_socket.send(create_EHLO())
        if req_comp(get_from_serv(my_socket)):
            print("EHLO Succeeded")
        else:
            quit(my_socket, f"EHLO command failed")
            return

        # 3 AUTH LOGIN
        my_socket.send(create_AUTH_LOGIN())
        if auth_input(get_from_serv(my_socket)):
            print("AUTH LOGIN succeeded")
        else:
            quit(my_socket, f"AUTH LOGIN failed")
            return

        # 4 Username
        my_socket.send(create_AUTH_VAL(SMTP_protocol.USER))
        if auth_input(get_from_serv(my_socket)):  # get username response
            print("User auth succeeded")
        else:
            quit(my_socket, "User authentication failed")
            return

        # 5 password
        my_socket.send(create_AUTH_VAL(SMTP_protocol.PASSWORD))
        if get_from_serv(my_socket).startswith(
            SMTP_protocol.AUTH_SUCCESS
        ):  # get password response
            print("Password auth succeeded")
        else:
            quit(my_socket, "Password authentication failed")
            return

        # 6 mail from
        if send_MAIL_FROM(
            my_socket, SMTP_protocol.USER, SMTP_protocol.DOMAIN
        ):  # adds full address
            print("MAIL FROM command succeeded")
        else:
            quit(my_socket, "Error: MAIL FROM failed")
            return

        # 7 rcpt to
        if send_RCPT_TO(my_socket, SMTP_protocol.RCPT, SMTP_protocol.DOMAIN):
            print("RCT TO command succeeded")
        else:
            quit(my_socket, "Error: SMTP_protocol.RCPT TO command failed")
            return

        # 8 data
        my_socket.send(create_DATA())
        if get_from_serv(my_socket).startswith(
            SMTP_protocol.ENTER_MESSAGE
        ):  # worked! now send content
            print("DATA command succeeded")
        else:
            quit(my_socket, "Error: DATA command failed")
            return

        # 9 email content
        l = len(EMAIL_TEXT)
        n = SMTP_protocol.MSG_SIZE
        if l <= n:  # can send it all in 1 packet
            print("Email content fits in one message! Sending it to server")
            my_socket.send(create_CONTENT(EMAIL_TEXT))  # 1 message, send it
        else:  # if exceeds max size, split it into chunks of 1024 bytes
            print(
                f"Email content length: {l} exceeds one message, splitting it"
            )  # (or number set in config file MSG_SIZE)
            j = 1  # counter for message number
            for i in range(
                    0, l, n):  # go through email, in steps of n bytes (1024)
                print(
                    f"Sending message {j} with bytes [{i} to {n+i}) to server"
                )  # document how far through
                j += 1  # increment
                my_socket.send(
                    create_CONTENT(EMAIL_TEXT[i: n + i])
                )  # splice array to get next parts

        response = get_from_serv(my_socket)  # done with email
        if req_comp(response):  # now to next stage - succeeded
            print(f"Client finished sending email contents: {response}")
        elif too_long(response):  # too many fragmented messages
            quit(my_socket, f"Error: {response}")
            return
        else:  # failed - didn't get confirmation from server
            quit(my_socket, f"Error: EMAIL CONTENT command failed {response}")
            return

        # 10 quit - done connection - make sure to close properly
        my_socket.send(create_QUIT())
        response = get_from_serv(my_socket)
        if response.startswith(SMTP_protocol.GOODBYE):
            print("Success: Server said goodbye to client - finished session")
        else:
            print("Error: Server didn't say goodbye to client - not ended correctly")
    except ConnectionResetError as cre:
        print(f"Connection forcibly closed on client {cre}")
    except ConnectionRefusedError as cref:
        print(f"Server actively refused client connection {cref}")
    except ConnectionAbortedError as cae:
        print(f"Connection aborted on client {cae}")
    except ConnectionError as ce:
        print(f"Generic connection error on client {ce}")
    except socket.timeout as st:
        print(f"C Error: Socket timed out before end {st}")
    except socket.error as se:
        print(f"C Socket error {se}")
    finally:
        # either way, we are done
        quit(my_socket, "Client closing socket", False)
        return


if __name__ == "__main__":
    main()
