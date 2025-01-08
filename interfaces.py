from scapy.all import *

# Get the dictionary of interfaces
interfaces = iface.findall()

# Loop through the interfaces and identify the wireless one (usually
# starts with wlan)
for name, info in interfaces.items():
    if name.startswith("wlan"):
        wireless_iface = name
        break

# Print the wireless interface name
print(f"Wireless interface: {wireless_iface}")
