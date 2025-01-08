import hashlib
import time

with open("hash/hi.txt", "r") as f:
    data = f.read()
    # print(data)
    start = time.time()
    print(hashlib.md5(data.encode()).hexdigest())
    print(time.time() - start)
    # print(hashlib.sha256(data.encode()).hexdigest())

with open("hash/hi1.txt", "r") as f:
    data = f.read()
    # print(data)
    start2 = time.time()
    # print(hashlib.md5(data.encode()).hexdigest())
    print(hashlib.sha256(data.encode()).hexdigest())
    print(time.time() - start2)

# comparing MD5, SHA and speed of hashing
