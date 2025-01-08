from scapy.all import ARP, sniff

# Define a callback function to process the sniffed packets
def process_packet(packet):
    if packet.haslayer(ARP):
        print(f"ARP Packet: {packet.summary()}")


# Start sniffing ARP packets
sniff(filter="arp", prn=process_packet, store=False)
