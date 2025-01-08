"""Encrypted socket client implementation
   Author: Avi
   Only supports valid utf-8 characters ... hebrew is not supported
"""

import socket
import time

import protocol

# these are not shared and should be kept secret
RSA_P = 269  # calculated myself for RSA
RSA_Q = 271  # P*Q > 2^16

# MODUL = 72899 > 65536
# TOTIENT = 72360
# RSA keys - given in english assignment
# party a
PRIV_KEY = 55109
PUB_KEY = 1229

# initially used numbers given in assignment, but wanted to try my own and also pick a P and Q that fit the requirements for size
# changing back to original numbers will also work


def init_session():
    """
    connect to server and return working socket
    """
    try:
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        my_socket.connect(("127.0.0.1", protocol.PORT))
        return my_socket
    except AssertionError as e:
        print("Assertion error", e)
        return None
    except (ConnectionError, socket.error) as e:
        print("Connection/Socket error", e)
        return None
    except Exception as e:
        print("Unknown Exception", e)
        return None


def connect_and_retry() -> socket:
    """
    connect to server and retry if failed (similar code to what i wrote for smtp)...
    more for convenience if you start client script before server
    """
    my_socket = init_session()  # try to connect
    count = 1  # number of tries so far

    while my_socket is None and count <= protocol.FAILED_ATTEMPTS:
        # loop over till get successful connection or exceed the failed bounds
        # each time let's give it exponentially longer to wait
        snooze = count**2  # im tired
        print(f"Retry #{count}, sleeping {snooze} seconds")
        time.sleep(snooze)  # exponential backoff
        my_socket = init_session()  # re-try connection
        count += 1  # increment

    if (
        count > protocol.FAILED_ATTEMPTS and my_socket is None
    ):  # exceeded max attempts & failed
        print("Server is offline or not responding")
        print(f"Exiting after {count-1} unsuccessful attempts")
        return None  # we are done (including the 1st try before loop)

    if my_socket is not None:
        print("Connected to server successfully")
        return my_socket

    return None


def diffie_protocol(my_socket) -> int:
    """
    Diffie Hellman protocol
    returns shared secret
    """
    # Diffie Hellman
    # 1 - choose private key
    pr_key = protocol.diffie_hellman_choose_private_key()
    # 2 - calc public key
    pub_key = protocol.diffie_hellman_calc_public_key(pr_key)
    # 3 - interact with server and calc shared secret
    ms, valid = protocol.send_message(my_socket, str(pub_key))
    if not valid:
        raise AssertionError(f"Could not send public DH key to server {ms}")

    message, valid = protocol.get_msg(my_socket)  # get server's public key
    if not valid:
        raise AssertionError(f"Could not get server's public DH key {message}")

    server_dh = int(message)  # server's public key
    print(f"DH Server public key: {server_dh}, Client public key: {pub_key}")
    shared_sec = protocol.diffie_hellman_calc_shared_secret(
        server_dh, pr_key
    )  # calc shared secret
    print(f"DH Shared Secret {shared_sec}")
    return shared_sec  # return shared secret


def check_user_input(user_input: str) -> bool:
    """
    Check if user input is valid and not too big, return True if valid
    """
    if user_input == protocol.EXIT:
        return True  # exit command
    if not user_input.isascii():
        raise AssertionError("Only ascii characters are supported")
    if len(user_input) > protocol.MAX_LENGTH:
        raise AssertionError(
            f"Message size {len(user_input)} is too big, max size is {protocol.MAX_LENGTH}"
        )
    return True  # valid input


def init_rsa(my_socket, totient: int) -> int:
    """
    initialize the RSA protocol and return server's public key
    """
    print("Moving to RSA")
    # Pick public key (top of file)
    # Calculate matching private key
    priv_test = protocol.get_RSA_private_key(totient, PUB_KEY)
    if priv_test != PRIV_KEY:
        raise AssertionError(
            f"RSA private key for client is not correct {priv_test} != {PRIV_KEY}"
        )
    # Exchange RSA public keys with server
    sent, valid = protocol.send_message(my_socket, str(PUB_KEY))
    if not valid:
        raise AssertionError(f"Failed to send rsa public client key{sent}")

    server_rsa_pub, valid = protocol.get_msg(
        my_socket)  # get server's public key
    if not valid:
        raise AssertionError(
            f"Error: Could not get server's public RSA key {server_rsa_pub}"
        )

    server_rsa_pub = int(server_rsa_pub)
    valid_rsa = protocol.check_RSA_public_key(
        totient, server_rsa_pub
    )  # validation of server RSA
    if not valid_rsa:
        raise AssertionError(
            f"Server's public key {server_rsa_pub} is not valid according to RSA rules"
        )

    print(f"RSA Server Public Key: {server_rsa_pub}")
    return server_rsa_pub  # server rsa public key


def main():
    """
    Main function for dh and rsa communication
    """
    my_socket = None
    try:
        my_socket = connect_and_retry()
        assert my_socket is not None, "Could not connect to server"

        shared_sec = diffie_protocol(my_socket)
        # RSA
        totient, modulo = protocol.calc_totient_modulus(RSA_P, RSA_Q)

        server_rsa_pub = init_rsa(my_socket, totient)

        while True:
            user_input = input("Enter command\n")
            if not check_user_input(user_input):
                # tell server that error happened and quit
                protocol.send_message(my_socket, user_input)
                break
            # Add MAC (signature)
            # 1 - calc hash of user input
            hashed = protocol.calculate_hash(user_input)
            # 2 - calc the signature
            signature = protocol.calc_signature(hashed, PRIV_KEY, modulo)

            # Encrypt
            # apply symmetric encryption to the user's input
            sym = protocol.symmetric_encryption(user_input, shared_sec)
            # Send to server
            # Combine encrypted user's message to MAC, send to server
            sent, valid_msg = protocol.send_message(my_socket, sym + signature)
            assert valid_msg, f"Could not send message to server {sent}"

            if user_input == protocol.EXIT:
                break

            # Receive server's message
            message, valid_msg = protocol.get_msg(my_socket)
            assert valid_msg, "Server detected an error with their message"

            hash_worked, dec_message = protocol.check_other_side_message(
                message=message,
                shared_secret=shared_sec,
                other_rsa_public=server_rsa_pub,
                modulo=modulo,
            )
            assert hash_worked, "Message is not authentic (client check)"

            print(dec_message)  # Print server's message (echo)
    except AssertionError as e:
        print("Assertion error:", e)
    except (ConnectionError, socket.error) as e:
        print("Connection/Socket error:", e)
    except Exception as e:
        print("Unknown error:", e)
    finally:
        print("Closing client socket \n")
        if my_socket is not None:
            my_socket.close()


if __name__ == "__main__":
    main()
