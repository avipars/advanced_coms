"""SYN Flood Attack Detector
   Author: Avi
"""

import time
from collections import defaultdict

from scapy.all import *
from scapy.layers.inet import IP, TCP

ENCODE = "utf-8"


def syn_flood_checker(
    pcap_file: str, syn_threshold: int = 10, rate_threshold: float = 1
) -> dict:
    """
    SYN Flood Attack Detector.

    This function analyzes a pcapng file for potential SYN flood attacks.

    Parameters:
        pcap_file (str): Path to the pcapng file to analyze.
        syn_threshold (int): Minimum number of SYN packets from a single IP to consider it a potential attacker.
        rate_threshold (float): Minimum packet sending rate (packets per second) to consider suspicious activity.

    Returns:
        dict: Dictionary of potential attackers with their metrics.
    """
    potential_attackers = defaultdict(
        lambda: {
            "syn_count": 0,
            "ack_count": 0,
            "timestamps": [],
            "target_ips": set(),
            "source_range": set(),
        }
    )

    with PcapReader(pcap_file) as capture:
        for pkt in capture:
            if pkt.haslayer(TCP) and IP in pkt:
                src_ip = pkt[IP].src
                dst_ip = pkt[IP].dst
                current_time = time.time()

                if pkt[TCP].flags == "S":  # SYN packet
                    potential_attackers[src_ip]["syn_count"] += 1
                    potential_attackers[src_ip]["timestamps"].append(
                        current_time)
                    potential_attackers[src_ip]["target_ips"].add(dst_ip)
                    potential_attackers[src_ip]["source_range"].add(src_ip)
                elif pkt[TCP].flags == "A":  # ACK packet
                    potential_attackers[src_ip]["ack_count"] += 1

                # Filter out potential attackers based on various criteria
    filtered_attackers = {}
    for ip, metrics in potential_attackers.items():
        # Calculate packet sending rate
        if len(metrics["timestamps"]) > 1:
            duration = metrics["timestamps"][-1] - metrics["timestamps"][0]
            rate = len(metrics["timestamps"]) / duration if duration > 0 else 0
        else:
            rate = 0

        # Check if the IP meets the criteria for being a potential attacker
        if metrics["syn_count"] >= syn_threshold:
            filtered_attackers[ip] = {
                "syn_count": metrics["syn_count"],
                "ack_count": metrics["ack_count"],
                "target_ips": list(metrics["target_ips"]),
                "source_range": list(metrics["source_range"]),
            }

    return filtered_attackers


def parse_attackers(my_dict: dict, file_name: str, fancy_print: bool = False):
    """
    Parse the attackers dictionary and output the results to a file.

    Parameters:
        my_dict (dict): Dictionary of potential attackers with their metrics.
        threshold (int): Minimum number of SYN packets to consider an attacker.
        file_name (str): Path to the output file.
        fancy_print (bool): If True, write the results in a formatted way.
    """
    with open(file_name, "w", encoding=ENCODE) as file:
        for ip, metrics in my_dict.items():
            if fancy_print:
                file.write(
                    f"IP: {ip}\n  SYN Count: {metrics['syn_count']}\n  ACK Count: {metrics['ack_count']}\n  Packet Rate: {metrics['packet_rate']:.2f} pps\n  Target IPs: {metrics['target_ips']}\n  Source Range: {metrics['source_range']}\n  SYN/ACK Ratio: {metrics['syn_ack_ratio']:.2f}\n"
                )
            else:
                file.write(f"{ip}\n")


def main():
    """
    main function
    """
    wireshark_file = "SYNflood.pcapng"
    results = "results.txt"

    print("Analyzing SYN flood attacks...")
    attackers = syn_flood_checker(
        wireshark_file,
        syn_threshold=10,
        rate_threshold=0.1)
    print(f"Number of potential attackers: {len(attackers)}")
    parse_attackers(my_dict=attackers, file_name=results, fancy_print=False)
    print(f"Results saved to: {results}")


if __name__ == "__main__":
    main()
