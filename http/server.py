# Ex 4.4 - HTTP Server Shell
# Author: Barak Gonen
# Purpose: Provide a basis for Ex. 4.4
# Note: The code is written in a simple way, without classes, log files or other utilities, for educational purpose
# Usage: Fill the missing functions and constants
import os.path
import socket
import sys

# Edited and improved by avi


# constants
IP = "0.0.0.0"  # listen on all local interfaces
PORT = 80  # http port
SOCKET_TIMEOUT = 5  # in seconds
MAX_LENGTH = 1024  # max msg length in bytes, we are expecting small get requests, so this is plenty ... at same time, don't set too low as we don't want to miss data
# if we wanted POST, then we would need to increase to handle larger image
# uploads

VER = "HTTP/1.1"  # HTTP version we are using


def calc_area(msg: str):
    """
    Calculate the area of a triangle given the height and width
    """
    if "&" not in msg or msg.count("=") != 2:  # check for correct format
        print("Invalid query string")
        return False, "Invalid query"  # error

    in1 = msg.split("&")  # split the query string
    if len(in1) != 2:  # check for correct number of parameters
        print("Invalid query parameter count")
        return False, "Wrong number of parameters"  # error
    before = in1[0].split("=")  # split the parameters
    after = in1[1].split("=")

    f_num = to_float(before[1])  # convert to float
    s_num = to_float(after[1])

    if f_num and s_num:  # both are numbers
        first = before[0]
        second = after[0]  # verify order and parameter names
        # in this case if height and width was swapped , area is the same but
        # we are able to handle a different order of the params
        if first == "height" and second == "width":  # make sure to get the right args
            height = f_num
            width = s_num
        elif first == "width" and second == "height":  # handle alternative order
            height = s_num
            width = f_num
        else:
            print("Invalid parameter names")
            return False, "Invalid parameter names"  # error
    elif f_num <= 0 or s_num <= 0:
        print("We only accept positive numbers")
        return False, "We only accept positive numbers"  # error not natural
    else:
        print(f"Invalid result {f_num} {s_num}")
        return (
            False,
            "At least one of the inputs is not a valid number",
        )  # todo throw some error

    print(f"height: {height}, width: {width}")  # print the values
    return True, str((height * width) / 2)


def calc_next(query: str, url: str):
    """
    if query is a number, increment it by 1 and return the result as a string
    """
    if (
        query.startswith("num=") and query.count("=") == 1
    ):  # num is the only parameter, and only 1 equal sign and nothing after num
        worked, num = to_int(url.split("=")[1])  # get the number
        if worked:
            return worked, str(num + 1)  # increment
        else:
            return worked, "Parameter num is not a natural number"
    else:
        return False, "First (and only) parameter should be num"


def get_file_data(filename: str):
    """Get data from file"""
    try:  # read as binary file
        with open(filename, "rb") as file:
            data = file.read()
            # print(data)
        return True, data  # return data and success
    except IOError as e:
        print("IOError: ", e)
    except Exception as e:
        print("General Error: ", e)
    return False, None


def to_float(msg: str):
    """
    check if the string is a number, if so, return the float value, otherwise return False (remove 1 decimal and then check if numeric, then can convert and keep decimal)
    """
    return float(msg) if msg.replace(".", "", 1).isnumeric() else False


def to_int(msg: str):
    """
    check if the string is a number, if so, return the integer value, otherwise return False
    """
    s = msg.replace(" ", "")  # remove whitespace
    if s == "0" or s == "0.0" or s == "0.0":  # allow 0 as a number
        return True, 0
    elif s.isnumeric():
        return True, int(s)
    else:
        print("Not a number")
        return False, None


def length_bytes(s) -> str:
    """
    each char can have a variable length... so sys.getsizeof doesn't help here
    function returns the length of object in bytes as a string
    """
    # https://stackoverflow.com/questions/30686701/python-get-size-of-string-in-bytes
    # fall back to str of length if not a string
    # encode to utf-8 if string, otherwise just get the length
    return str(len(s.encode("utf-8"))) if isinstance(s, str) else str(len(s))


def handle_client_request(resource: str, client_socket, file_path: str):
    """Check the required resource, generate proper HTTP response and send to client"""
    DEFAULT_URL = "/index.html"

    if resource in (
        "",
        "/",
        "/index",
        "/index.htm",
        "/home",
    ):  # these should give a 200 ok, and "redirect" but not a 302
        url = DEFAULT_URL
    else:
        url = resource

    # check if URL had been redirected, not available or other error code. For
    # example:
    REDIRECTION_DICTIONARY = {
        "/a.html": "/avi.html",
        "/a": "/avi.html",
        "/favicon.ico": "/imgs/favicon.ico",
        "/blue.png": "/imgs/blue.png",
        "/red": "/imgs/blue.png",
    }

    if url in REDIRECTION_DICTIONARY:
        url = REDIRECTION_DICTIONARY[
            url
        ]  # we search by key and trade variables for value
        client_socket.send(
            f"{VER} 302 Found\r\nLocation: {url}\r\n".encode()
        )  # send 302 redirection response and location for the new url
        return  # we don't need to process further

    def_type = "text/plain"  # default to this type
    # extract requested file type from URL (html, jpg etc)
    TYPES = {
        "html": "text/html",
        "txt": def_type,
        "text": def_type,
        "js": "text/javascript",
        "css": "text/css",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "ico": "image/x-icon",
        "gif": "image/gif",
    }  # favicon, can either be x-icon or a microsoft format

    # get last element (if there are multiple dots, we only care about
    # extension)
    filetype = url.split(".")[-1]
    if filetype in TYPES:
        filetype = TYPES[filetype]  # via dictionary, get the correct type
    else:
        filetype = def_type  # all other headers

    header = f"{VER} 200 OK\r\nContent-Type: {filetype}"
    if filetype in (
        "html",
        "txt",
        "text",
        "js",
            "css"):  # human readable files (text)
        header += (
            "charset=UTF-8"  # add charset utf-8 encoding to text related files only
        )

    header += "\r\nContent-Length: "  # for any valid request, we add this
    print(f"filename requested: {url}")

    if "?" in url:  # query param exists
        quest = url.split("?")
        page = quest[0]
        query = quest[1]
        if page == "/calculate-next":
            worked, response = calc_next(query, url)
            handle_question(worked, response, header, client_socket)
            return
        elif page == "/calculate-area":  # send to calc area function
            worked, response = calc_area(query)
            handle_question(worked, response, header, client_socket)
            return
    else:  # resource as file
        user_file = file_path + url  # add file_path before filename
        if os.path.isfile(user_file):
            res, data = get_file_data(
                user_file
            )  # read the data from the file (current working directory)
            if not res:  # issue with file
                print("Error reading file - likely permissions issue")
                client_socket.send(
                    error_response("403 Forbidden")
                )  # file with no read permissions
                return
            elif data is None:
                print("No data in file")
                client_socket.send(
                    error_response("204 No Content")
                )  # file with no data
                return
        else:
            client_socket.send(error_response("404 Not Found"))  # not a file
            return

        # append length of data to header
        header += f"{length_bytes(data)}\r\n\r\n"
        print(header)
        # encode http_header before concatenating with data
        client_socket.send(
            header.encode() + data
        )  # data is a file in binary format, so no need to encode that part


def handle_question(worked: bool, response: str, header: str, client_socket):
    """handle the end result for /calculate-x requests"""
    if worked:
        # concatenate the header with the response
        header += f"{length_bytes(response)}\r\n\r\n{response}"
        print(f"Result is: {header}")  # print the header
        client_socket.send(header.encode())  # encode and then
    else:
        client_socket.send(
            error_response("500 Internal Server Error", False, response)
        )  # fallback to error


def error_response(
        error: str = "404 Not Found",
        page: bool = True,
        details: str = ""):
    """Generate an error response with the given error code and details"""
    deet = ""
    if page:
        if details != "" and details is not None:
            deet = f"<p>{details}</p>"  # add details to page

        data = f"""<html><body><h1>{error}</h1>{deet}<a href="http://127.0.0.1:80">Go Back Home</a></body></html>
                    """  # simple error page
    else:
        data = details + "\r\n\r\n"  # not a page, just a text/plain response
    return (f"{VER} {error}\r\n\r\n{data}").encode()


def validate_http_request(request: str):
    """
    validate the http request, check if it is a valid http request and return the resource and method
    """
    request = request.split("\r\n")[0]  # drop user-agent, cookies, etc
    parts = request.split(" ")
    def_res = False, None, None  # default response, invalid
    if (
        len(parts) != 3
    ):  # we expect 3 parts, if there aren't, we fail early as we don"t want index out of range
        return def_res

    method = parts[0]  # get the method
    if method not in (
        "GET",
        "POST",
        "HEAD",
        "PUT",
        "DELETE",
        "OPTIONS",
        "TRACE",
        "CONNECT",
        "PATCH",
    ):  # this is for validating http requests, we will take care of what specifically is allowed later
        return def_res

    resource = parts[1]  # get the resource
    if not resource or not resource.startswith(
            "/"):  # Check if a resource is requested
        return def_res

    ver = parts[2]  # version of http if exists to handle
    if ver not in ("HTTP/1.0", VER, "HTTP/1.2"):  # handle common versions
        return def_res

    return True, resource, method  # return success, resource, and method


def handle_client(client_socket, file_path: str):
    """Handles client requests: verifies client"s requests are legal HTTP, calls function to handle the requests"""
    print("Client connected")

    # default error response
    invalid = error_response("500 Internal Server Error")
    try:
        while True:
            client_request = client_socket.recv(MAX_LENGTH).decode()
            valid_http, resource, method = validate_http_request(
                client_request)
            if valid_http:
                print("Got a valid HTTP request")
                if method == "GET":  # only handling GET requests
                    handle_client_request(resource, client_socket, file_path)
                elif method in (
                    "POST",
                    "HEAD",
                    "PUT",
                    "DELETE",
                    "OPTIONS",
                    "TRACE",
                    "CONNECT",
                    "PATCH",
                ):  # all http methods (except GET) are not implemented (501 Not Implemented
                    print(
                        f"Got a {method} request, we don't need to handle these")
                    client_socket.send(error_response("501 Not Implemented"))
                else:
                    print("Error: Not a valid HTTP request method")
                    client_socket.send(invalid)
                break  # any request handled will break the loop
            else:
                print("Error: Not a valid HTTP request")
                client_socket.send(invalid)
                break
    except socket.timeout:
        print("Socket timed out")
    except Exception as e:
        print("Error: ", e)
    finally:
        print("Closing connection")
        client_socket.close()


def meta_code() -> str:
    """
    Code to easily ensure that the script has access to webroot - not really required as part of course...
    """
    # webroot folder is in the current working directory (cwd), if you want to
    # hardcode path, please change the below line
    file_path = os.path.join(
        os.getcwd(), "webroot"
    )  # ie C:\Networking\webroot , using os path join to please other OSes
    if not os.path.exists(
        file_path
    ):  # check if webroot folder exists, if not then, print error and let user enter path
        print(
            "ERROR: webroot folder not found, try to run the server code from the correct directory or enter the path via the prompt below\n"
        )
        file_path = input("Enter hardcoded path to webroot folder:\n")
        if not os.path.exists(file_path):  # check if the path is valid
            print("ERROR: Invalid path, exiting")
            sys.exit(1)  # exit with error code
        else:
            print("Path accepted, continuing...")
    return file_path  # I expect the user to point the code to the right directory, this function is just to try to make it easier


def main():

    # can replace meta_code call with the absolute path to the webroot folder
    # instead - # ie hw5\webroot or C:\Networking\webroot
    file_path = meta_code()

    # regular server stuff
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((IP, PORT))
    server_socket.listen()
    print(f"Listening for connections on port {PORT}")
    try:
        while True:
            client_socket, client_ip = server_socket.accept()
            print(f"New connection received: {client_ip}")
            client_socket.settimeout(SOCKET_TIMEOUT)
            handle_client(client_socket, file_path)
    except Exception as e:
        print("MError: ", e)
        server_socket.close()
        sys.exit(1)


if __name__ == "__main__":
    main()  # Call the main handler function
