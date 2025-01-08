from scapy.all import *

# Define the domain name to look up
domain_name = "yahoo.com."

# Create an IP packet with UDP protocol and destination port 53 (DNS)
ip_packet = IP(dst="8.8.8.8") / UDP(dport=53)

# Create a DNS packet with recursion desired flag set
dns_packet = DNS(rd=1, qd=DNSQR(qname=domain_name))

# Combine layers to form the complete packet
packet = ip_packet / dns_packet

# Send the packet and receive the response
response = sr1(packet, timeout=20)

# Check if a response is received
if response:
    # Print a summary of the response packet
    print(response.summary())

    # Extract the IP address from the answer section (modify if looking for
    # other record types)
    for answer in response[DNS].an:
        print(answer.show())
        if answer.rrname == domain_name:
            print(f"IP address for {domain_name}: {answer.rdata}")
            break
else:
    print("No response received from DNS server")
