import os
from pathlib import Path

def convert_json_txt_to_json(dataset_root):
    dataset_path = Path(dataset_root)

    if not dataset_path.exists():
        print("Dataset path does not exist.")
        return

    renamed_count = 0

    for file_path in dataset_path.rglob("*.json.txt"):
        new_name = file_path.with_name(file_path.name.replace(".json.txt", ".json"))
        
        print(f"Renaming:\n  {file_path}\n  -> {new_name}\n")
        
        file_path.rename(new_name)
        renamed_count += 1

    print(f"Done. Total files renamed: {renamed_count}")

if __name__ == "__main__":
    dataset_root = r"C:\Mohit\My-Repositories\Samsung-Prism-Research\Dataset"
    convert_json_txt_to_json(dataset_root)