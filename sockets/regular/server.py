import select
import socket

from protocols import *

SERVER_FIXED = "0.0.0.0"  # listen on all interfaces
# allow spaces in messages - if disabled, only sends the 1 word (and cuts
# off rest)
ALLOW_SPACES_MSG = True
DEBUG = False


def main():
    # initialize startup process
    print("Setting up server...")
    s_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM)  # server socket
    try:
        s_socket.bind((SERVER_FIXED, SERVER_PORT))
        s_socket.listen()
        s_socket.setblocking(0)  # set to non-blocking
        if DEBUG:
            print(
                "Listening for clients on {}:{}".format(
                    SERVER_FIXED, SERVER_PORT))
        else:
            print("Listening for clients...")
        # commence startup process

        # client-server comms via sockets
        client_sockets = []  # list of client sockets
        message_queue = []  # list of messages to send
        client_names = {}  # dict of client names and their sockets

        while True:  # always listening (like the NSA)
            # list of interesting sockets
            read_list = client_sockets + [s_socket]
            to_ready, to_write, in_error = select.select(
                read_list, client_sockets, []
            )  # what to chose

            # read from 1st param, 2nd param is what to send , 3rd is errors
            # (empty for now), 4th is timeout (none for now)
            for curr_sock in to_ready:  # for each socket in the list with a message
                if curr_sock.fileno() == -1:  # if CLIENT is down
                    print("Client went down, closing connection")
                    remove_client(client_sockets, client_names, curr_sock)
                    continue

                if curr_sock == s_socket:  # someone wants to connect
                    c_socket, c_address = s_socket.accept()  # handshake approved
                    print(f"New client connected from: {c_address}")
                    client_sockets.append(c_socket)  # add client to list
                    print_client_sockets(client_sockets)
                else:  # client has a message
                    # get message from client
                    data, res = get_message(curr_sock)
                    if DEBUG:
                        print(f"Data: {data} Result: {res}")
                    else:
                        print(f"Info received from client")

                    if res and data != "":  # got tuple true
                        reply, dest_socket = handle_client_request(
                            curr_sock, client_names, data
                        )  # GET COMMAND HERE AND DECIDE
                        print(f"Message from client: {data}")
                        message_queue.append((dest_socket, reply))
                    elif res and data == "":  # empty message - exit worked
                        print(f"Connection closed by client")
                        remove_client(client_sockets, client_names, curr_sock)
                    else:  # error , issue with message itself, socket, or length field
                        print(f"Client encountered an error with {data}")
                        remove_client(client_sockets, client_names, curr_sock)

            # forward messages
            for message in message_queue:
                c_socket, data = message  # unpack tuple
                if c_socket in to_write:  # if the client is ready to receive
                    data, res = send_message(c_socket, data)
                    if res:  # send worked
                        # remove message from queue
                        message_queue.remove(message)
                    else:
                        # print error, remove msg, remove client from dict
                        print(f"Error sending: {data} to {c_socket}")
                        # remove message from queue
                        message_queue.remove(message)
                        remove_client(client_sockets, client_names, c_socket)
    except Exception as e:
        print(f"Server Error: {e}")
    finally:
        print(f"Closing server...")
        s_socket.close()


def remove_client(client_sockets, client_names, c_socket: socket):
    """
    Remove client from the server
    """
    for item in list(
        client_names.keys()
    ):  # iterate over copy of keys - to avoid bug of dictionary size
        if client_names[item] == c_socket:  # if client socket is found
            name = item  # get name
            client_names.pop(name)  # remove client name from listA

    client_sockets.remove(c_socket)  # remove client socket from listB
    c_socket.close()  # close client connection


def print_client_sockets(client_sockets):
    """
    print out client ip and port numbers = socket
    """
    for c in client_sockets:
        # use function that exists in socket class
        print("\t", c.getpeername())


def handle_client_request(current_socket, client_names, data):
    """find and return right response to right client"""
    # default to current socket (if no destination specified)
    dest_socket = current_socket
    info = data.split()  # any whitespace separated

    if len(info) <= 0:  # if empty message
        return error_msg(err="Empty message", num=EMPTY_MESSAGE), dest_socket

    # pull out command to compare and deal with properly
    cmd = info[0]  # command is first word (by protocol)
    cmd = cmd.strip()  # remove whitespace

    reply = error_msg(
        err=f"Invalid Command: {cmd}", num=INVALID_COMMAND
    )  # default reply

    commands = ("NAME", "GET_NAMES", "MSG", "EXIT")
    if cmd.startswith(ERROR):  # if error message
        return error_msg(err="Error message sent",
                         num=UNKNOWN_MESSAGE), dest_socket
    elif not cmd.startswith(commands):  # no match found
        return reply, dest_socket
    elif not cmd.startswith(
        ("NAME", "MSG")
    ):  # meaning EXIT, GET_NAMES - commands without any arguments
        if len(info) > 1:  # allow whitespace but not anything else besides cmd
            return (
                error_msg(
                    err=f"Command {cmd} does not take any arguments (cannot have text appended to it)",
                    num=APPEND_ERROR,
                ),
                dest_socket,
            )
        # now to handle the command
        if cmd == EXIT or cmd == "":  # if exit or empty message
            return (
                error_msg(
                    f"Exit command not executed properly by client",
                    num=INVALID_COMMAND),
                dest_socket,
            )
        elif cmd == "GET_NAMES":
            return get_names(client_names), dest_socket
    else:  # meaning NAME, MSG - commands with arguments
        info = info[1:]  # remove command from list, as already handled
        if cmd == "NAME":
            return create_name(current_socket, client_names, info)
        elif cmd == "MSG":
            return handle_msg(current_socket, client_names, info)
    return reply, dest_socket


def error_msg(err: str, num: str = UNKNOWN_MESSAGE):
    return f"ERROR: {num} {err}"


def get_names(client_names: dict):
    """returns names separated by spaces"""
    if len(client_names) == 0:  # no clients
        return "No clients connected"
    return " ".join(client_names.keys())  # key = socket is the goal


def handle_msg(current_socket, client_names, data):
    """Handle user message including verifying that it fits within protocol specs
    ensure user has their own name registered, doesn't send to self, and target exists
    """
    if len(data) < 2:  # <name> <message text> so this is too small
        return (
            error_msg(
                err="Message text not provided (not appended to MSG command)",
                num=APPEND_ERROR,
            ),
            current_socket,
        )
    target_name = data[0]  # name is 1st word, as 0th is command
    # message is everything after name - we went from array to string
    if ALLOW_SPACES_MSG:  # allow spaces in message
        msg = " ".join(data[1:])
    else:  # disregard anything after 1st word
        msg = data[1]

    if target_name not in client_names.keys():  # target - RECEIVER doesn't exist
        return (
            error_msg(
                err=f"Target name {target_name} does not exist",
                num=USER_NOT_FOUND),
            current_socket,
        )

    # If the current_socket is not found, sender_name will be None
    sender_name = next(
        (sock for sock, name in client_names.items() if name == current_socket), None
    )  # Check if the sender name is in the dictionary
    if sender_name is None:  # no sender name found
        return (
            error_msg(
                err="Please register your name before sending (sender name not found)",
                num=USER_NOT_FOUND,
            ),
            current_socket,
        )
    elif target_name == sender_name:
        return (
            error_msg(err="Cannot send message to self", num=INVALID_COMMAND),
            current_socket,
        )
    else:
        # message to send, and destination socket
        if len(msg) > 0:  # message is not empty
            return f"{sender_name} sent {msg}", client_names[target_name]
        else:  # message is empty
            return (
                error_msg(
                    err="Message text not provided (not appended to MSG command)",
                    num=APPEND_ERROR,
                ),
                current_socket,
            )


def create_name(current_socket, client_names, data):
    """create name for client on server"""
    if len(data) < 1:  # recall that cmd was stripped out
        return (
            error_msg(
                err="Name not provided (not appended to NAME command)",
                num=APPEND_ERROR),
            current_socket,
        )
    elif len(data) > 1:  # 1 word only
        return (
            error_msg(
                err="Name too long (only one word allowed)",
                num=LENGTH_SIZE_ISSUE),
            current_socket,
        )
    # now we get length of exactly 1
    name = data[0]
    if name in client_names.keys():  # already there ;( )
        return (
            error_msg(err=f"Name {name} already exists", num=DUPLICATE_USER),
            current_socket,
        )
    elif current_socket in client_names.values():
        return (
            error_msg(err="You already claimed a name", num=DUPLICATE_USER),
            current_socket,
        )
    else:
        if not name.isalpha():  # only allow english letters
            return (
                error_msg(
                    err="Name must be only english characters",
                    num=INVALID_COMMAND),
                current_socket,
            )
        client_names[name] = current_socket  # add name to DICT
        # return success message to client
        return f"Hello {name}", current_socket


if __name__ == "__main__":
    main()
