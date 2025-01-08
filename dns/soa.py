from config import *
from scapy.all import *
from scapy.layers.dns import DNS, DNSQR
from scapy.layers.inet import IP, UDP


def trial():
    dns_packet = (
        IP(dst=DEFAULT_DNS)
        / UDP(sport=LOCAL_PORT, dport=53)
        / DNS(qdcount=1, rd=1)
        / DNSQR(qname="www.example.com", qtype="SOA")
    )
    dns_packet.show()
    send(dns_packet, verbose=1, iface=LOCAL_INTERFACE)
    print(IFACES)


def main():
    dns_server_request = (
        IP(dst="PUT SOA SERVER HERE") #YOU NEED TO PUT SOA SERVER IN
        / UDP(dport=53)
        / DNS(rd=1, qd=DNSQR(qname="SUBDOMAIN.example.com", qtype="A"))
    )
    ans = sr1(dns_server_request, verbose=1)
    ans.show()


if __name__ == "__main__":
    main()
