# Avi
import re
import sys
import time

from scapy.all import *
from scapy.layers.dns import DNS, DNSQR
from scapy.layers.inet import IP, UDP

DEFAULT_DNS = "8.8.8.8"  # Google's public DNS server - only used for first SOA query
TIMEOUT = 10  # timeout for all DNS queries

# RUN THE PROGRAM IN THE SAME DIRECTORY AS wordlist.txt


def dns_query(
    domain: str,
    dns: str = DEFAULT_DNS,
    qt: str = "A",
    timeout: int = TIMEOUT,
    verb: int = 0,
):
    """
    send from random port each time to look less suspicious and also so each query is unique (in theory)
    verb: verbose response - 1 is on
    qt: query type... we use A or SOA here
    qdcount: unsigned fields query count
    rd:    recursion desired flag set
    """
    # stacking the layer cake
    query = (
        IP(dst=dns)
        / UDP(sport=RandShort(), dport=53)
        / DNS(id=RandShort(), qdcount=1, rd=1, qd=DNSQR(qname=domain, qtype=qt))
    )

    if verb == 1:  # verbose mode
        print("Domain: " + domain)
        print("DNS server: " + dns)
        print("Query/Record type: " + qt)
        print("Your Interfaces:")
        print(IFACES)
        print("Crafting a DNS query packet...")
        query.show()
        print("Sending the DNS query packet...")

    response = sr1(
        query, timeout=timeout, verbose=verb
    )  # send the query and wait for a response

    if verb == 1:  # verbose mode
        print("Received response:")
        response.show()  # might print twice if verbose is on
    return response


def extract_ip(response):
    ip_list = []
    if (
        response.haslayer(DNS) and response.getlayer(DNS).qr == 1
    ):  # check if DNS layer is present and if it is a response
        for i in range(
            response[DNS].ancount
        ):  # check answer count and execute for each item received
            answer = response[DNS].an[i]  # get the answer section
            if (
                isinstance(answer, DNSRR) and answer.type == 1
            ):  # ensure the answer is a DNS resource record
                # get the IP address and add to list
                ip_list.append(answer.rdata)
    return ip_list


def is_private(ip):
    """
    regex to check if ip address is in private range or public
    credit to:
    https://stackoverflow.com/questions/2814002/private-ip-address-identifier-in-regular-expression
    """
    rfc1918 = re.compile(
        "^(10(\\.(25[0-5]|2[0-4][0-9]|1[0-9]{1,2}|[0-9]{1,2})){3}|((172\\.(1[6-9]|2[0-9]|3[01]))|192\\.168)(\\.(25[0-5]|2[0-4][0-9]|1[0-9]{1,2}|[0-9]{1,2})){2})$"
    )
    return rfc1918.match(ip)


def get_print_ip(response, ending=" "):
    """
    gets ip list, prints it and returns it
    """
    count = 0  # local counter for ip addresses for this subdomain
    # local counter for private IPs for this subdomain (gets returned so
    # parent can add to total)
    internal_count = 0
    ip_list = extract_ip(response)
    for i in ip_list:
        count += 1  # count the ip addresses
        print(f"IP address #{count}: {i}", end=ending)
        if is_private(i):
            internal_count += 1  # count the internal IP addresses
            print("warning: internal IP address disclosed", end="\n")
    print()  # print a newline
    return (
        ip_list,
        internal_count,
    )  # return the ip list and internal count for the parent function to use


def soa_finder(dom):
    """
    step 1 get the primary_ip name server
    """
    response = dns_query(
        domain=dom,
        qt="SOA")  # use public dns resolver 1st time
    if response is None:  # no response
        return False, "No response received."
    elif DNS not in response:  # no DNS in response
        return False, "DNS not in response."
    elif response[DNS].rcode == 5:
        return False, "Server refused to complete the DNS request."
    elif response[DNS].rcode == 4:
        return False, "Feature not implemented."
    elif response[DNS].rcode == 3:  # answer to step 2
        return False, "Domain does not exist."
    elif response[DNS].rcode == 2:
        return False, "Server failed to complete the DNS request."
    elif response[DNS].rcode == 1:
        return False, "Format error in the DNS query."
    elif response[DNS].ancount == 0:
        return False, "No answer in response."
    elif response[DNS].rcode == 0:  # all good
        res = response[DNS].an  # get the primary_ip name server
        if res is None:
            return False, "No primary name server"  # but no primary_ip name server
        elif res.type != 6:
            return False, "Not a SOA record"  # not a SOA record
        return True, res.mname.decode(
            "utf-8"
        )  # extract domain + convert from byte string to string
    else:
        return False, f"Error {response[DNS].rcode} in the DNS request."


def main():
    if len(sys.argv) != 2:  # check that 1 and only 1 arg was sent
        print("We require exactly 1 argument, which is the domain name.")
        sys.exit(1)

    dom = sys.argv[1]  # get the domain name from the command line

    valid, soa = soa_finder(dom)  # stage 1 get the primary name server
    if not valid:
        print(soa)  # prints error to user
        sys.exit(1)

    print(f"Primary name server: {soa}")  # print the primary name server
    response = dns_query(
        domain=dom, dns=soa, qt="A"
    )  # query the primary name server for the domain ip (to print mainly)
    if response is None:
        print("No response received.")
        sys.exit(1)
    elif DNS in response and response[DNS].ancount == 0:  # no record found
        print("No dns ip record found in response.")
        sys.exit(1)

    print("Name server", end=" ")  # print the ip(s) of primary name server
    ip_list, ic = get_print_ip(
        response, ending="\n"
    )  # throw away the internal count for now

    primary_ip = ip_list[0]  # take 1st ip
    # stage 1.2 try to contact the primary name server to ensure its live and
    # then do enumeration
    verifying = dns_query(domain=dom, dns=soa, qt="A")
    if verifying is None:
        print("No response received.")
        sys.exit(1)
    else:
        ip_ver = verifying[DNS].an.rdata  # get verifying ip
        if ip_ver != primary_ip:  # compare ip from 2nd query to 1st query
            print(
                f"Primary name server IP: {ip_ver} is different from the one we got {primary_ip}"
            )

    subdomain_count = 0  # stats/counters
    ip_count = 0  # all ip addresses
    internal_count = 0  # private ip addresses
    start = time.time()  # track how long it takes to enumerate

    print(f"Avi's DNS Network Mapper")
    print("Searching (sub)domains for jct.ac.il using built-in wordlists (h and tla)\n")

    # NOTE THAT THIS NEEDS TO BE RUN IN THE SAME DIRECTORY AS wordlist.txt
    with open("wordlist.txt", "r") as file:
        full_list = file.readlines()  # now enumerate the domain
        for item in full_list:
            item = item.strip()  # remove newline and spaces
            site = f"{item}.{dom}"  # sub.domain.tld
            response = dns_query(domain=site, dns=soa, qt="A")
            if (
                response is not None and DNS in response
            ):  # we got something and didn't timeout
                if (response[DNS].ancount >= 1 and response[DNS].an[0].type ==
                        1):  # check that response is valid and has answer
                    print(f"{site}")
                    subdomain_count += 1
                    ip_list, ic = get_print_ip(
                        response, ending="\n"
                    )  # print the ip(s) of subdomain
                    ip_count += len(ip_list)  # got >1 response
                    internal_count += ic  # count internal ip addresses, 0 if none

        end = time.time()  # end of enumeration
        print(f"{subdomain_count} subdomains found")
        print(f"{ip_count} ip addresses found")  # all ip addresses
        # private ip addresses
        print(f"{internal_count} internal IP addresses found")
        res = end - start  # time delta
        print(
            f"Enumeration completion time: {res:.2f} seconds = {((res)/60):.2f} minutes"
        )  # print time taken rounded to 2 decimal places


if __name__ == "__main__":
    main()
