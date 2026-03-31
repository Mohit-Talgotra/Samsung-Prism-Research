import os

def parse_report(report_path):
    missing, empty, invalid = [], [], []
    current_section = None
    section_map = {
        "Missing results:": missing,
        "Empty files:": empty,
        "Invalid files:": invalid,
    }
    with open(report_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line in section_map:
                current_section = section_map[line]
            elif line and current_section is not None:
                current_section.append(line)
    return missing, empty, invalid

def delete_files(label, rel_paths, results_root):
    deleted = 0
    skipped = 0
    for rel_path in rel_paths:
        full_path = os.path.join(results_root, rel_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            deleted += 1
        else:
            print(f"[SKIPPED] {label}: {rel_path} — file not found")
            skipped += 1
    print(f"\n{label}: {deleted} deleted, {skipped} skipped (not found)")

if __name__ == "__main__":
    report_path  = "detailed_report.txt"
    results_root = r"C:\Mohit\Repositories\Samsung-Prism-Research\Results\Dataset"

    _, empty_paths, invalid_paths = parse_report(report_path)

    print(f"Empty files to delete   : {len(empty_paths)}")
    print(f"Invalid files to delete : {len(invalid_paths)}")
    confirm = input("Confirm deletion? (yes/no): ").strip().lower()

    if confirm == "yes":
        delete_files("EMPTY", empty_paths, results_root)
        delete_files("INVALID", invalid_paths, results_root)
    else:
        print("Aborted.")