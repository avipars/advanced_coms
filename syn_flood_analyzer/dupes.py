import ipaddress


def read_ip_addresses(file_path):
    """
    Reads IP addresses from a file and returns a set of unique IPs.
    """
    with open(file_path, "r") as file:
        ip_addresses = file.read().splitlines()
    return set(ip.strip() for ip in ip_addresses)


def write_results(file_path, unique_ips, duplicates=None):
    """
    Writes the results to a file.
    """
    with open(file_path, "w") as file:
        if duplicates:
            file.write("Duplicates found and removed:\n")
            file.write("\n".join(duplicates) + "\n\n")
        file.write("Unique IP addresses:\n")
        file.write(
            "\n".join(
                sorted(
                    unique_ips,
                    key=ipaddress.ip_address)) +
            "\n")


def compare_ip_lists(file1, file2):
    """
    Reads IP addresses from two files, removes duplicates, sorts them,
    and identifies IP addresses that are unique to each file.
    """
    ip_list1 = read_ip_addresses(file1)
    ip_list2 = read_ip_addresses(file2)

    print(f"Number of IP addresses in {file1}: {len(ip_list1)}")
    print(f"Number of IP addresses in {file2}: {len(ip_list2)}")
    duplicates1 = [ip for ip in ip_list1 if list(ip_list1).count(ip) > 1]
    duplicates2 = [ip for ip in ip_list2 if list(ip_list2).count(ip) > 1]

    unique_ips1 = ip_list1 - ip_list2
    unique_ips2 = ip_list2 - ip_list1

    if duplicates1:
        print(f"Duplicates found in {file1} and removed.")
    if duplicates2:
        print(f"Duplicates found in {file2} and removed.")

    if unique_ips1:
        count = len(unique_ips1)
        print(f"{count} IP addresses unique to {file1}:")
        for ip in sorted(unique_ips1, key=ipaddress.ip_address):
            print(ip)
    else:
        print(f"No unique IP addresses in {file1}.")

    if unique_ips2:
        count = len(unique_ips2)
        print(f"{count} IP addresses unique to {file2}:")

        for ip in sorted(unique_ips2, key=ipaddress.ip_address):
            print(ip)
    else:
        print(f"No unique IP addresses in {file2}.")


def main():
    file1 = "attackersListFiltered.txt"
    file2 = input("Enter the path to the second file: ")
    compare_ip_lists(file1, file2)


if __name__ == "__main__":
    main()
