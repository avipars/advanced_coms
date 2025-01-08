"""Encrypted sockets implementation
   Author: Avi
   Only supports valid ascii characters ... hebrew is not supported
"""

from random import randint
from socket import \
    error as socket_error  # for socket errors, I want to handle it properly

LENGTH_FIELD_SIZE = 2
PORT = 8820

DIFFIE_HELLMAN_P = 101  # P is a big prime
DIFFIE_HELLMAN_G = 73  # n = G^k % P has to exist for some power k and each n

MAC_LENGTH = 15  # number of characters in the MAC
# send keys - fixed size - maybe can skip length protocol for the start

# length field - length field maker etc
LENGTH_FIELD_SIZE = 2
MAX_LENGTH = 99  # how long the message can be
MIN_LENGTH = 0

FAILED_ATTEMPTS = 5  # how many times to try to reconnect after a failure
ENCODING = "ascii"  # encoding for the messages
ERRORS = "replace"  # how to handle errors ( swap with ? if unknown char)
EXIT = "EXIT"  # exit command


def encode(msg: str) -> bytes:
    """Encode the message to ascii"""
    return msg.encode(encoding=ENCODING, errors=ERRORS)


def decode(msg) -> str:
    """Decode the message from ascii"""
    return msg.decode(encoding=ENCODING, errors=ERRORS)


def symmetric_encryption(input_data, key: int) -> str:
    """
    Return the encrypted/decrypted data using XOR method.
    key is 16 bits. If the length of the input data is odd, use only the bottom 8 bits of the key.
    """
    data_bytes = encode(input_data)  # to bytes
    key &= 0xFFFF  # convert the key to 16 bits (padded)

    if len(input_data) % 2 == 1:  # Check the length of the data
        key &= 0xFF  # Use only the bottom 8 bits of the key if data length is odd

    # Encrypt/Decrypt the data using XOR
    result = bytearray()  # prepare the result
    for byte in data_bytes:  # iterate over each byte in the data
        result.append(byte ^ key)  # XOR with the key
    return decode(result)  # return the result as a string


def diffie_hellman_choose_private_key() -> int:
    """Choose a 16 bit size private key"""
    return randint(1, 2**16 - 1)  # [0 to 2*16) ~ 16 bit size private key


def diffie_hellman_calc_public_key(private_key: int) -> int:
    """G**private_key mod P"""
    return pow(DIFFIE_HELLMAN_G, private_key, DIFFIE_HELLMAN_P)


def diffie_hellman_calc_shared_secret(
        other_side_public: int,
        my_private: int) -> int:
    """other_side_public**my_private mod P"""
    return pow(other_side_public, my_private, DIFFIE_HELLMAN_P)


def calculate_hash(message: str, prime: int = 23) -> int:
    """
    Create a hash value (up to 5 digits) to represent the message.
    The result will be up to 16 bits (0 to 65535).
    prime = 23 something to add to hash value (padding of sorts)
    """
    acc = 1  # accumulator
    for letter in message:
        # combine val of the character with the current hash value and other
        acc = (2 * ord(letter)) + ((acc << 1) - acc) + prime
        acc &= 0xFFFF  # ensure within required size by masking
    return acc


def calc_signature(hash_value, RSA_private_key: int, pq: int) -> str:
    """Calculate the signature, using RSA algorithm
    hash**RSA_private_key mod (P*Q)"""
    signature = pow(
        int(hash_value), int(RSA_private_key), pq
    )  # compute the RSA signature
    # Convert to string and pad MAC with leading zeros if needed to always be
    return str(signature).zfill(MAC_LENGTH)  # padding with leading zeros


def separate_mac(msg) -> tuple:
    """separate the msg and mac bit length of modulus
    return the message (1st) and the mac (2nd)"""
    return msg[:-MAC_LENGTH], msg[-MAC_LENGTH:]  # python slicing to the rescue


def create_msg(data) -> tuple:
    """Create a valid protocol message, with length field
    For example, if data = data = "hello world",
    then "11hello world" should be returned"""
    length = str(len(data))
    if not MIN_LENGTH < len(length) <= LENGTH_FIELD_SIZE:
        raise AssertionError(
            f"Message length size {len(data)} is out of range")

    msg = length.zfill(LENGTH_FIELD_SIZE) + data
    return encode(msg), True  # encode the message to ascii (bytes


def get_msg(my_socket) -> tuple:
    """Extract message from protocol, without the length field
    If length field does not include a number, returns False, "Error" """
    try:
        len_field = decode(my_socket.recv(LENGTH_FIELD_SIZE))

        len_field = len_field.lstrip("0")  # remove padding if single digit
        if len_field == "":  # if length field is empty
            raise AssertionError("Length field is empty")
        if not len_field.isdigit():  # if length field is not a digit
            raise AssertionError("Length field is not a digit")

        len_field = int(len_field)  # now can convert without any issues
        if not (
            MIN_LENGTH <= len_field <= MAX_LENGTH
        ):  # if length field is not within range
            raise AssertionError(
                "Length field size isn't within pre-declared range")

        msg = decode(
            my_socket.recv(len_field)
        )  # get message in the specified byte length

        if len(msg) != len_field:
            raise AssertionError(
                f"Length field isn't according to spec {len(msg)} != {len_field}"
            )
        return msg, True
    except AssertionError as ae:
        return f"{ae}", False
    except (ConnectionError, socket_error) as e:
        return f"Socket/Connection error: {e}", False
    except Exception as e:
        return f"General error {e}", False


def send_message(socket, data, create=True) -> tuple:
    """
    create and send message to socket conforming to the length field protocol
    encodes the message
    """
    try:
        if create:  # create and send in one go
            message, success = create_msg(data)
            if not success:  # if message creation failed
                return message, False  # return error message from create_message
            socket.send(message)  # send message over socket in bytes
            return message, True  # return message sent and true as its a success
        # send message that is already created (create is false)
        socket.send(data)  # send message over socket
        return data, True
    except AssertionError as ae:
        return f"{ae}", False
    except (ConnectionError, socket_error) as e:
        return f"Socket Connection Error: {e}", False
    except Exception as e:
        return f"Unknown error {e}", False


def check_RSA_public_key(totient: int, key: int) -> bool:
    """Check that the selected public key satisfies the conditions
    key is prime,
    key < totient,
    totient mod key != 0"""
    if (not is_prime(key)) or key >= totient or totient % key == 0:
        return False
    return True


def get_RSA_private_key(totient: int, public_key: int) -> int:
    """Calculate the pair of the RSA public key.
    Use the condition: Private*Public mod Totient == 1
    Totient = (p-1)(q-1)"""
    # pub^-1 mod totient = public
    return pow(public_key, -1, totient)  # modular inverse


def is_prime(n: int) -> bool:
    """Check if a number is prime"""
    if n < 2:  # we dont consider 1 as prime
        return False
    for i in range(2, int(n**0.5) + 1):  # iterate over till root n (included)
        if n % i == 0:  # if n is divisible by i then not prime
            return False
    return True  # has to be prime


def check_other_side_message(
    message: str, shared_secret: int, other_rsa_public: int, modulo: int
) -> tuple:
    """
    Decrypt message from other side and check if its valid/authentic
    return True if we find its valid along with the decrypted message

    """
    # 1 - separate the message and the MAC
    message, mac = separate_mac(message)
    # 2 - decrypt the message
    dec_message = symmetric_encryption(message, shared_secret)

    # 3 - calc hash of message
    hash_msg = calculate_hash(dec_message)
    # 4 - use other side's public RSA key to decrypt the MAC and get the
    decrypted_hash = calc_signature(mac, other_rsa_public, modulo)

    # 5 - check if both calculations end up with the same result
    hash_worked = hash_check(hash_msg, decrypted_hash)
    return hash_worked, dec_message


def hash_check(hash1, hash2) -> bool:
    """Checks if the hashes are the same or not"""
    hash1 = int(hash1)
    hash2 = int(hash2)
    if hash1 == hash2:
        return True
    print(f"Hashes do not match: {hash1} != {hash2}")
    return False


def calc_totient_modulus(p: int, q: int) -> tuple:
    """
    helper function to calculate totient [1] and modulus [2] for RSA
    put in protocol file just because both sides use it. protocol file doesn't store either p or q
    """
    return (p - 1) * (q - 1), p * q
