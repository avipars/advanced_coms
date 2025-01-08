# ESMTP protocol
PORT = 25  # or 587 for encrypted mail (newer addition)
SMTP_SERVICE_READY = "220"
REQUESTED_ACTION_COMPLETED = "250"
COMMAND_SYNTAX_ERROR = "501"
INCORRECT_AUTH = "535"
ENTER_MESSAGE = "354"
AUTH_INPUT = "334"
AUTH_SUCCESS = "235"
# <CRLF>.<CRLF> ",\n" # Find which combination of chars indicates email end
EMAIL_END = "\r\n.\r\n"
GOODBYE = "221"  # quit from server
CLIENT_QUIT = "QUIT\r\n"


# bonus
AUTH_LOGIN = "AUTH LOGIN\r\n"
RCPT = "RCPT TO:"
MAIL_FROM = "MAIL FROM: "
DATA = "DATA\r\n"
EHLO = "EHLO"
MSG_TOO_LONG = "552"


# client side
CLIENT_NAME = "client.net"
FAILED_ATTEMPTS = 5  # how many times to try to reconnect after a failure
CLIENT_IP = "127.0.0.1"  # or localhost
# email configurations
USER = "barbie"
RCPT = "ken"
DOMAIN = "mattel.com"
PASSWORD = "helloken"

# server side
SERVER_NAME = "SMTP_server.com"
SERVER_ADDRESS = "127.0.0.1"
SOCKET_TIMEOUT = 10  # give it some time to connect - server side

# not part of protocol but good for client/server to share
MAX_MESSAGES = 100  # how many fragmented messages are allowed (content)

MSG_SIZE = 1024  # set a magic number for byte size max to accept at each end point
