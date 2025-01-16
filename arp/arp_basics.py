import scapy.all as scapy

request = scapy.ARP()

print("summary\n" + request.summary())
print("show request\n")
request.show()
print("ls\n")
print(scapy.ls(scapy.ARP()))