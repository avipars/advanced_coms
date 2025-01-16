# script to compare lists of ip addreses and find mismatches

import ipaddress
import sys


def meta_compare(list1: str, list2: str):
    try:
        with open(list1, "r") as file:
            data1 = file.read()
        with open(list2, "r") as file:
            data2 = file.read()
    except IOError as e:
        print(f"Error reading file: {e}")
        return None

    data1 = data1.split("\n")
    data2 = data2.split("\n")

    # remove duplicates
    data1 = list(set(data1))
    data2 = list(set(data2))

    data1 = sorted(data1)
    data2 = sorted(data2)

    # compare
    count = 0
    for i in range(len(data1)):
        data1[i] = data1[i].strip()
        data2[i] = data2[i].strip()
        if data1[i] != data2[i]:
            count += 1
            print(f"mismatch at line {i} : {data1[i]} != {data2[i]}")
            # return
    print(f"Number of mismatches: {count}")


def main():
    # get args from command line 1st arg is the official file, 2nd arg is the
    # file to compare
    args = sys.argv
    if len(args) == 3:
        print(f"Using official: {args[1]} and yours {args[2]}")
        meta_compare(args[1], args[2])
        return
    else:
        print("Using default files")

    official = "attackersListFiltered.txt"
    mine = "attack_file.txt"
    meta_compare(official, mine)


if __name__ == "__main__":
    main()
