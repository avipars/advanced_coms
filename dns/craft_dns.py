from scapy.all import *
from scapy.layers.dns import DNS, DNSQR


def craft_dns_packet(dns_server, domain, qtype="A"):
    # Create the DNS query packet
    dns_query = (
        IP(dst=dns_server)
        / UDP(dport=53)
        / DNS(rd=1, qd=DNSQR(qname=domain, qtype=qtype))
    )
    return dns_query


# Example usage
dns_server = "8.8.8.8"  # Google's DNS server
domain = "example.com"
dns_packet = craft_dns_packet(dns_server, domain)
dns_packet.show()  # Display the packet structure
