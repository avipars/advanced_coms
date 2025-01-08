# my own server to communcate with the exe (after changing the IP in the hosts file)
import http.server
import json
import socketserver


# Define the request handler
class MyRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Handle GET request for the root path
        if self.path == "/":
            response = {"message": "hello world", "Success": True}
            response_data = json.dumps(response).encode("utf-8")

            # Send a 200 OK response
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Content-Length", len(response_data))
            self.end_headers()

            # Write the response content
            self.wfile.write(response_data)
        else:
            # Serve other files normally
            super().do_GET()


# Define the server address and port
HOST = "127.0.0.1"
PORT = 8200

# Create the server
with socketserver.TCPServer((HOST, PORT), MyRequestHandler) as httpd:
    print(f"Serving at http://{HOST}:{PORT}")
    # Serve until interrupted
    httpd.serve_forever()
