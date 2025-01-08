def remove_duplicates(filename, output):
    total = 0
    with open(filename, "r") as f:
        lines = f.readlines()
        total = len(lines)
        lines_set = set(lines)
        non_duplicates = len(lines_set)
        # sort alphabetically
        lines_set = sorted(lines_set)
        with open(output, "w") as file:
            for line in lines_set:
                file.write(line)
    print(f"Duplicates removed and written to {output}")
    print(f"Total lines: {total}")
    print(f"Non-duplicates: {non_duplicates}")
    print(f"Duplicates: {total - non_duplicates}")


def main():
    filen = input("Enter filename: ")

    remove_duplicates(filen, "result_sorted.txt")


if __name__ == "__main__":
    main()
