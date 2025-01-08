from scapy.all import ARP, Ether, srp

# Define the target IP address
target_ip = "10.0.0.254"

# Create an ARP request packet
arp_request = ARP(pdst=target_ip)

# Create an Ethernet frame with a broadcast destination
ether = Ether(dst="ff:ff:ff:ff:ff:ff")

# Combine the ARP request with the Ethernet frame
arp_request_packet = ether / arp_request

# Send the packet and receive the response
result = srp(arp_request_packet, timeout=2, verbose=False)[0]

# Parse the response
for sent, received in result:
    print(f"IP Address: {received.psrc} | MAC Address: {received.hwsrc}")
