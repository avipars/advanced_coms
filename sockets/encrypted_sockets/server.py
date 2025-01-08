"""Encrypted socket server implementation
   Author: Avi
   Only supports valid ascii characters ... hebrew is not supported
"""

import socket

import protocol

# these are not shared and should be kept secret
RSA_P = 269  # explained in client.py
RSA_Q = 271

# party b RSA keys
PRIV_KEY = 44507
PUB_KEY = 2003


def create_server_rsp(cmd: str) -> str:
    """Based on the command, create a proper response - this gets sent to the client"""
    return f"Server Response: {cmd}"


def init_connection():
    """
    bind to the port and allow client to connect
    """
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(("0.0.0.0", protocol.PORT))
        server_socket.listen(1)  # only handle 1 connection at a time
        print(f"Server is up and running on port: {protocol.PORT}")
        (client_socket, client_address) = server_socket.accept()
        print(f"Client connected: {client_address}")
        return server_socket, client_socket
    except AssertionError as e:
        print("Assertion error", e)
        return None, None
    except (ConnectionError, socket.error) as e:
        print("Connection or socket error", e)
        return None, None
    except Exception as e:
        print("Other error", e)
        return None, None


def diffie_protocol(client_socket) -> int:
    """
    Diffie Hellman key exchange protocol and return the shared secret after calculation and exchange
    """
    # Diffie Hellman
    print("Moving to Diffie Hellman")
    # 1 - choose private key
    pr_key = protocol.diffie_hellman_choose_private_key()
    # 2 - calc public key (mine)
    pub_key = protocol.diffie_hellman_calc_public_key(pr_key)
    # 3 - interact with client and calc shared secret
    message, valid = protocol.get_msg(client_socket)  # get client's public key
    if not valid:
        raise AssertionError(
            f"Error: Something went wrong with getting client's DH public key {message}"
        )

    client_pub = int(message)  # client's public key

    sent, valid = protocol.send_message(client_socket, str(pub_key))
    if not valid:
        raise AssertionError(
            f"Error: Could not send public DH key to client {sent}")

    # pub key to client
    print(f"Server public key: {pub_key}, Client public key: {message}")

    shared_sec = protocol.diffie_hellman_calc_shared_secret(client_pub, pr_key)

    print(f"Shared Secret: {shared_sec}")
    return shared_sec


def init_rsa(client_socket, totient: int, modulo: int) -> int:
    """
    RSA key exchange protocol and return the client's public key
    """
    print("Moving to RSA")
    # we chose the keys already, so here just verify that the calculation is correct...
    # theoretically I can also remove the priv key from top of file and
    # calculate it here
    priv_test = protocol.get_RSA_private_key(totient, PUB_KEY)
    if priv_test != PRIV_KEY:
        raise AssertionError(
            f"RSA private key for server is not correct {priv_test} != {PRIV_KEY}"
        )
    print(f"Modulo Bit Length: {(modulo).bit_length()}")  # for debugging

    msg, valid = protocol.get_msg(client_socket)  # get client's public key

    if not valid:
        raise AssertionError(
            f"Error: Something went wrong with getting client's public key {msg}"
        )

    # Calculate matching private key
    # Exchange RSA public keys with client
    client_rsa = int(msg)  # clients public rsa key
    valid_rsa = protocol.check_RSA_public_key(
        totient, client_rsa
    )  # validation of client RSA
    if not valid_rsa:
        raise AssertionError(
            f"Clients's public key {client_rsa} is not valid according to RSA"
        )

    print(f"RSA Client's Public Key: {client_rsa}")

    sent, valid = protocol.send_message(client_socket, str(PUB_KEY))

    if not valid:
        raise AssertionError(f"Failed to send rsa public key{sent}")
    return client_rsa


def main():
    """
    main function for server
    """
    server_socket = None  # init values
    client_socket = None
    try:
        # communication setup
        server_socket, client_socket = init_connection()
        assert server_socket is not None, "Server socket is not set up"
        assert client_socket is not None, "Client socket is not set up"
        # DH key exchange
        shared_sec = diffie_protocol(client_socket)

        # RSA
        totient, modulo = protocol.calc_totient_modulus(RSA_P, RSA_Q)

        client_rsa = init_rsa(client_socket, totient=totient, modulo=modulo)
        while True:
            # Receive client's message
            message, valid = protocol.get_msg(client_socket)
            assert valid, "Client detected an error with their message"

            # 5 - check if both calculations end up with the same result
            hash_worked, dec_message = protocol.check_other_side_message(
                message,
                shared_secret=shared_sec,
                other_rsa_public=client_rsa,
                modulo=modulo,
            )

            assert hash_worked, "Message is not authentic (server check)"
            print(f"Client sent: {dec_message}")
            if dec_message == protocol.EXIT:  # exit command - will close the connection
                break

            # Create response. The response would be the echo of client's
            # message
            response = create_server_rsp(dec_message)
            # Encrypt
            signature = protocol.calc_signature(
                protocol.calculate_hash(response), PRIV_KEY, modulo
            )
            # apply symmetric encryption to the server's message
            # Send to client
            # Combine encrypted user's message to MAC, send to client
            sent, res = protocol.send_message(
                client_socket, protocol.symmetric_encryption(
                    response, shared_sec) + signature, )
            assert res, f"Could not send message to client as {sent}"
    except AssertionError as e:
        print("Assertion error:", e)
    except (ConnectionError, socket.error) as e:
        print("Connection error:", e)
    except Exception as e:
        print("General error:", e)
    finally:
        print("Closing both sockets\n")
        if client_socket is not None:
            client_socket.close()
        if server_socket is not None:
            server_socket.close()


if __name__ == "__main__":
    main()
