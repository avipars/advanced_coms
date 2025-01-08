def fnv1a_hash(string):
    # FNV-1a constants
    FNV_prime = 0x01000193
    offset_basis = 0x811C9DC5

    # Convert string to bytes, handling different encodings
    if isinstance(string, str):
        string = string.encode("utf-8")

    # Initialize hash
    hash_value = offset_basis

    # Perform FNV-1a hash algorithm
    for byte in string:
        hash_value ^= byte
        hash_value *= FNV_prime
        hash_value &= 0xFFFFFFFF  # Ensure hash_value remains within 32 bits

    return hash_value


def hash_function(input_string):
    # Get the FNV-1a hash
    full_hash = fnv1a_hash(input_string)
    print("f h", full_hash)
    # full_hash = input_string.encode('utf-8')
    # Reduce to 14 bits by masking out the upper bits
    # 0x3FFF is 14 bits (0011 1111 1111 1111)
    reduced_hash = full_hash & 0x3FFF

    # Add the 2 constant bits (for example, 10) to form the final 16-bit hash
    constant_bits = 0b10
    final_hash = (reduced_hash << 2) | constant_bits

    return final_hash


def calculate_hash(message):
    # Convert the message to bytes if it's not already
    if isinstance(message, (str, int)):
        message = message.encode("UTF-8", errors="ignore")  # convert to bytes
    # Initialize the hash value
    hash_value = 0

    # Iterate over each byte in the message
    for byte in message:
        # Combine the byte value with the current hash value using bitwise
        # operations
        hash_value = (hash_value << 5) ^ byte | hash_value >> 10
        # hash_value *= 0x0000005
        hash_value |= 0b10
        # Ensure the hash value remains within 16 bits
        hash_value &= 0xFFFF

    # return the hash value as a 5-digit string
    return str(hash_value).zfill(5)


def fancy_hash(message):
    sm = 71  # initial val
    for i in range(len(message)):  # iterate over the message
        sm += ord(message[i]) * (i + 23) + (ord(message[0]) - 8) // (sm + 97)
    return int(sm ^ 97) % 99999  # return the hash value as a 5-digit string


def calc_hash(message):
    """Create some sort of hash from the message
    Result must have a fixed size of 16 bits"""
    return sum([ord(c) for c in message]) % (2**16)
    # % 20687


def calculate_hash2(message: str):
    """
    Create a hash value (up to 5 digits) to represent the message.
    The result will be up to 16 bits (0 to 65535).
    """
    hash_value = 1
    prime = 23
    for letter in message:
        # Combine the ASCII value of the character with the current hash value
        hash_value = (2 * ord(letter)) + \
            ((hash_value << 1) - hash_value) + prime
        hash_value &= 0xFFFF  # ensure within required size
    return hash_value
