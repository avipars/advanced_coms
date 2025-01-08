import msvcrt
import select
import socket

from protocols import *  # importing all the protocols, functions, etc

DEBUG = False


def communication_time(c_socket: socket, timeout):
    """
    After socket set up, now its time to communicate with the server
    """
    try:
        message = ""  # empty message to start
        while message != EXIT:  # stops when user types exit
            # r = wait till read ready, w = wait till write ready, x = wait for
            # exception
            read_list, write_list, error_list = select.select(
                [c_socket], [], [], timeout
            )
            # SEE IF SERVER IS STILL UP
            if c_socket.fileno() == -1:  # if server is down
                raise ValueError("Server closed connection")

            if read_list:  # we are expecting message
                data, res = get_message(c_socket)
                if res:  # if message is true == success
                    print(f"Server sent: {data}")
                else:
                    print(f"Error: {data}")  # print error message
                    end_comms(c_socket)  # close connection
            if msvcrt.kbhit():  # user input on client
                # get key press from user, support unicode as of now
                # get key press, we only want english characters (subset of
                # ascii)
                key = msvcrt.getch().decode(encoding="ascii", errors="ignore")
                # print key press and flush buffer
                print(key, flush=True, end="")
                if key == "\r":  # if user presses enter
                    print()  # new line
                    msg, res = send_message(c_socket, message)
                    message = ""  # reset message
                    if not res:  # if message creation/send failed
                        print(f"Error sending: {msg}", flush=True)
                        break  # break out of loop, which then has a fn call to close connection
                elif (
                    key == "\b" or key == "\x7f" or key == "\x08"
                ):  # backspace / delete key pressed
                    message = message[:-1]  # remove last character
                else:
                    message += key  # add key press to message
        end_comms(c_socket)  # after while loop ends, close connection
    except ValueError as ve:
        if DEBUG:
            print(f"Server closed connection forcibly: {ve}")
        else:
            print("Server closed connection")
    except Exception as e:
        print(f"Client Error: {e}")
        return


def end_comms(c_socket: socket):
    """
    End the communication with the server
    """
    try:
        send_message(c_socket, "")  # send exit message to server
        c_socket.close()  # close client socket
    except Exception as er:
        print(f"Client Error2: {er}")
        return


def main():
    debug = True
    c_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM)  # client socket
    try:
        c_socket.connect((SERVER_IP, SERVER_PORT))
        c_socket.setblocking(0)  # set to non-blocking
        if debug:
            print(f"Client connected to server at {SERVER_IP}:{SERVER_PORT}")
        else:
            print("Please enter command")

        # experiment with values, either a float or None (never time out)
        communication_time(c_socket=c_socket, timeout=0.1)
    except Exception as er:  # captures errors
        print(f"Client Error: {er}")
        return


if __name__ == "__main__":
    main()
