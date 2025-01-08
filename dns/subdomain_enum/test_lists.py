from scapy.all import *

import hw4.subdoms.H_LIST as H_LIST
import hw4.subdoms.TLA_LIST as TLA_LIST

print("Interfaces:")
answer = sr1(IP(dst="8.8.8.8") / UDP(dport=53) / DNS(rd=1,
                                                     qd=DNSQR(qname="www.example.com")), verbose=0, timeout=10, )
print(answer[DNS].summary())

full_list = set(
    H_LIST.H_LIST + TLA_LIST.TLA_LIST
)  # combine the lists and remove duplicates

print(len(H_LIST.H_LIST))
print(len(set(H_LIST.H_LIST)))
print(len(TLA_LIST.TLA_LIST))
print(len(set(TLA_LIST.TLA_LIST)))

print(len(H_LIST.H_LIST + TLA_LIST.TLA_LIST))
print(len(full_list))
