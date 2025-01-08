from scapy.all import *


def ping(host):
    try:
        packet = IP(dst=host) / ICMP() / b"You are the best"
        print(packet.show())
        response = sr1(packet, timeout=2, verbose=0)
        if response:
            print("Response: ", response.summary())

        if response[ICMP].type == 0:
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False


if __name__ == "__main__":

    worked = ping("example.com")
    if worked:
        print("Ping successful")
    else:
        print("Ping failed")
