import sys

from scapy.all import *


def filter_dns(pkt):
    return "DNS" in pkt or DNS in pkt

def print_query_name(dns_packet):
    print(dns_packet["DNSQR"].qname)

# make dns packet
def main():
    packets = sniff(count=2, lfilter=filter_dns)
    packets.summary()

if __name__ == "__main__":
    main()
