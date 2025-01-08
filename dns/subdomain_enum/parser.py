"""
sources:
https://github.com/makefu/dnsmap/blob/master/wordlist_TLAs.txt - first
https://github.com/makefu/dnsmap/blob/master/dnsmap.h - 2
"""


def load_tla_list(filename):
    """
    This function reads a text file containing TLAs (three-letter acronyms)
    and returns them as a list of strings.

    Args:
        filename: The path to the text file containing TLAs.

    Returns:
        A list of strings, where each string is a TLA.
    """
    tla_list = []
    count = 0
    try:
        with open(filename, "r") as f:
            for line in f:
                tla = line.strip()  # Remove leading/trailing whitespace
                if tla:  # Skip empty lines
                    count += 1
                    tla_list.append(tla)
    except FileNotFoundError:
        print(f"Error: File not found - {filename}")

    if count != len(tla_list):
        print(
            f"Warning: File contains {count} TLAs, but only {len(tla_list)} were loaded."
        )

    return tla_list, count


def load_h_file_as_txt(filename):
    # subdomains = []
    count = 0
    # write to new file as txt
    with open("wordlist2s.txt", "w") as file:
        with open(filename, "r") as f:
            lines = f.readlines()
            for line in lines:
                stripped_line = line.strip()
                # remove quotes and commas
                stripped_line = stripped_line.replace('"', "").replace(",", "")
                count += 1
                file.write(stripped_line + "\n")
                # subdomains.append(stripped_line)

    return count
    # return subdomains, count


def load_h_file(filename):
    subdomains = []
    count = 0
    with open(filename, "r") as f:
        lines = f.readlines()

    # Look for the line defining the sub array
    for line in lines:
        if line.strip().startswith("char sub[][MAXSUBSIZE]"):
            # Extract the subdomain definitions from the next lines
            for next_line in lines[lines.index(line) + 1:]:
                stripped_line = next_line.strip()
                if (
                    stripped_line
                    and not stripped_line.startswith("//")
                    and stripped_line[0] in "'\""
                    or stripped_line[0] in '"'
                ):  # Check for quotes and non-comment lines
                    count += 1
                    subdomains.append(
                        stripped_line[1:-1]
                    )  # Extract subdomain without quotes

    if count != len(subdomains):
        print(
            f"Warning: File contains {count} TLAs, but only {len(subdomains)} were loaded."
        )

    return subdomains, count


def output_tla_list(tla_list, output_filename, tla=True):
    """
    This function writes a list of subdomains to a text file.

    Args:
        tla_list: A list of strings, where each string is a TLA.
        output_filename: The path to the output text file.
    """
    with open(output_filename, "w") as f:
        if tla:
            f.write("TLA_LIST = " + str(tla_list).replace("'", '"'))
        else:
            f.write(
                "H_LIST = " +
                str(tla_list).replace(
                    '"',
                    "").replace(
                    "'",
                    '"'))
    print(f"written to: {output_filename}")


def tla():
    # Assuming the file is saved as "wordlist_TLAs.txt" in the same directory
    filename = "wordlist_TLAs.txt"
    tla_list, t_count = load_tla_list(filename)
    if tla_list:
        print(f"List of {t_count} TLAs")
        # output to txt file but store as python list
        output_tla_list(tla_list, "output_tla_list1.py")
    else:
        print("No TLAs found in the file.")


def dot_h():
    filename = "dnsmap.h.txt"
    h_count = load_h_file_as_txt(filename)
    print(f"List of {h_count} subdomains")


def main():
    dot_h()


if __name__ == "__main__":
    main()
