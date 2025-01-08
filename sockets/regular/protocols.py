import socket

SERVER_IP = "127.0.0.1"
# protocol Very simple chatroom prot (but my own version) - random but
# https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.txt
SERVER_PORT = 3073


# shared things between client and server
# error messages
USER_NOT_FOUND = "404"
DUPLICATE_USER = "405"
INVALID_COMMAND = "406"
INVALID_LENGTH_FIELD = "407"
LENGTH_SIZE_ISSUE = "408"
CONNECTION_ERROR = "409"
EMPTY_MESSAGE = "410"
UNKNOWN_MESSAGE = "411"
APPEND_ERROR = "412"

EXIT = "EXIT"
ERROR = "ERROR"

# length field - length field maker etc
LENGTH_FIELD_SIZE = 2
MAX_LENGTH = 99
MIN_LENGTH = 0


def create_message(data):
    """
    create message to send to socket conforming to the length field protocol
    does not encode the message
    """
    length = str(len(data))
    length_bytes = len(length)
    if length_bytes > LENGTH_FIELD_SIZE:  # too many bytes
        return f"{LENGTH_SIZE_ISSUE} message length size is too big", False
    length_field = length.zfill(LENGTH_FIELD_SIZE)  # backfill with 0s
    # encode combined length field and data
    message = (length_field + data).encode()
    return message, True  # return message and true as its a success


def send_message(socket, data, create=True):
    """
    create and send message to socket conforming to the length field protocol
    encodes the message
    """
    try:
        if create:  # create and send in one go
            message, success = create_message(data)
            if not success:  # if message creation failed
                return message, False  # return error message from create_message
            else:
                socket.send(message)  # send message
                return message, True  # return message sent and true as its a success
        else:  # send message that is already created
            socket.send(data)  # send message over socket
            return data, True
    except ConnectionResetError as cre:
        return f"{CONNECTION_ERROR} connection reset error", False
    except ConnectionRefusedError as cree:
        return f"{CONNECTION_ERROR} connection refused error", False
    except ConnectionAbortedError as cae:
        return f"{CONNECTION_ERROR} connection aborted error", False
    except Exception as e:
        return f"{UNKNOWN_MESSAGE} {e}", False


def get_message(socket):
    """
    get message from socket conforming to the length field protocol
    - does decode the message too!
    tuple is returned (message, success) where success is a boolean
    """
    try:
        # only care about first x bytes
        length = socket.recv(LENGTH_FIELD_SIZE).decode()  # get length field
        if length == "":  # if length field is empty
            return f"{EMPTY_MESSAGE} length field is empty", False
        elif not length.isdigit():  # if length field is not a number
            return f"{INVALID_LENGTH_FIELD} message length field is not a number", False
        else:
            length_i = int(length)  # number of bytes as integer
            if (length_i < MIN_LENGTH) or (length_i > MAX_LENGTH):
                # return error message invalid length field
                return (
                    f"{LENGTH_SIZE_ISSUE} message length size is too big or small",
                    False,
                )
            else:  # valid
                message = socket.recv(length_i).decode()
                if (
                    len(message) < length_i or len(message) > length_i
                ):  # if message is less than length field size, return error
                    return (
                        f"{INVALID_LENGTH_FIELD} message length field doesn't match message size",
                        False,
                    )
                return message, True  # return message and success
    except ConnectionResetError as cre:
        return f"{CONNECTION_ERROR} connection reset error", False
    except ConnectionRefusedError as cree:
        return f"{CONNECTION_ERROR} connection refused error", False
    except ConnectionAbortedError as cae:
        return f"{CONNECTION_ERROR} connection aborted error", False
    except Exception as e:
        return f"{UNKNOWN_MESSAGE} {e}", False
