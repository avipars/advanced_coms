from scapy.all import *

# IP layer packet. Need to set only the destination addr
ip = IP(dst="8.8.8.8")

# UDP layer packet. Need to set only the detination port
udp = UDP(dport=53)

# DNS layer packet.
# Need to set qd (question section). Set qname as the thing we want
dns = DNS(qd=DNSQR(qname="example.com", qtype="A"))

# stack up the layers
req = ip / udp / dns
# print the packet
req.show()

# send-and-receive once (sr1 is a great scapy function)
ans, unan = sr(req, verbose=1, timeout=10)

# print the answer packet
ans.show()
