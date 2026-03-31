import os
from pathlib import Path

# Concatenate all .txt files recursively into one file
def concatenate_text_files(root_folder, output_file):
    root_path = Path(root_folder)
    output_path = Path(output_file)

    with open(output_path, 'w', encoding='utf-8') as outfile:
        for txt_file in root_path.rglob("*.txt"):
            try:
                with open(txt_file, 'r', encoding='utf-8') as infile:
                    content = infile.read().strip()

                outfile.write("=" * 60 + "\n")
                outfile.write(f"FILE: {txt_file}\n")
                outfile.write("=" * 60 + "\n\n")
                outfile.write(content + "\n\n")

            except Exception as e:
                outfile.write("=" * 60 + "\n")
                outfile.write(f"FILE: {txt_file}\n")
                outfile.write("=" * 60 + "\n")
                outfile.write(f"ERROR READING FILE: {e}\n\n")

    print(f"\nAll text files concatenated into: {output_path}")


if __name__ == "__main__":
    root_folder = r"C:\Mohit\My-Repositories\Samsung-Prism-Research\Results"
    output_file = r"C:\Mohit\My-Repositories\Samsung-Prism-Research\all_results_combined.txt"

    concatenate_text_files(root_folder, output_file)