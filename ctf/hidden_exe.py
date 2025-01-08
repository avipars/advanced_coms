# Extract a hidden EXE from an image file

def remove_hex_until_mz(input_file_path, output_file_path):
    # Read the input file in binary mode
    with open(input_file_path, "rb") as input_file:
        data = input_file.read()

    # Locate the first occurrence of 'MZ' signature
    mz_signature = b"MZ"
    mz_index = data.find(mz_signature)

    if mz_index == -1:
        raise ValueError("MZ signature not found in the file.")

    # Extract the data from the 'MZ' signature to the end
    executable_data = data[mz_index:]

    # Save the extracted data to the new file
    with open(output_file_path, "wb") as output_file:
        output_file.write(executable_data)


# Example usage:
input_file_path = "ctf\\poison_apple.hex"
output_file_path = "outputfile.exe"
remove_hex_until_mz(input_file_path, output_file_path)
