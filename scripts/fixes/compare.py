import os
import re

# check valid format: XX.XX (positive float, 2 decimals)
def is_valid(content):
    content = content.strip()
    return bool(re.fullmatch(r"(100\.00|[1-9]?\d\.\d{2})", content))


# get expected txt paths from dataset images
def get_expected_txt_files(dataset_root):
    image_exts = (".jpg", ".jpeg", ".png")
    expected = set()
    familyFacesCount = 0
    for root, dirs, files in os.walk(dataset_root):
        for file in files:
            if file.lower().endswith(image_exts):
                full_path = os.path.join(root, file)
                if any("FamilyFaces" in part for part in full_path.split(os.sep)):
                    familyFacesCount += 1
                    continue
                rel_path = os.path.relpath(full_path, dataset_root)
                rel_txt = os.path.splitext(rel_path)[0] + ".txt"
                expected.add(rel_txt)
    return expected, familyFacesCount


# scan results dataset
def scan_results(results_root):
    existing = set()
    empty_files = []
    invalid_files = []

    for root, dirs, files in os.walk(results_root):
        for file in files:
            if file.endswith(".txt"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, results_root)

                existing.add(rel_path)

                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    if not content.strip():
                        empty_files.append(rel_path)
                    elif not is_valid(content):
                        invalid_files.append(rel_path)

                except Exception as e:
                    print(f"Error reading {full_path}: {e}")

    return existing, empty_files, invalid_files


if __name__ == "__main__":
    dataset_root = r"C:\Mohit\Repositories\Samsung-Prism-Research\Dataset"
    results_root = r"C:\Mohit\Repositories\Samsung-Prism-Research\Results\Dataset"

    # step 1: expected vs existing
    expected, familyFacesCount = get_expected_txt_files(dataset_root)
    existing, empty_files, invalid_files = scan_results(results_root)

    missing = expected - existing

    # combine all problematic files
    combined = set(missing) | set(empty_files) | set(invalid_files)

    # print summary
    print("\n=== SUMMARY ===")
    print(f"Total images: {len(expected)}")
    print(f"Results found: {len(existing)}")
    print(f"Missing results: {len(missing)}")
    print(f"Empty files: {len(empty_files)}")
    print(f"Invalid files: {len(invalid_files)}")
    print(f"Total needing fix: {len(combined)}")

    # -----------------------------
    # save detailed report
    # -----------------------------
    with open("detailed_report.txt", "w", encoding="utf-8") as f:
        f.write("Missing results:\n")
        for file in sorted(missing):
            f.write(file + "\n")

        f.write("\nEmpty files:\n")
        for file in sorted(empty_files):
            f.write(file + "\n")

        f.write("\nInvalid files:\n")
        for file in sorted(invalid_files):
            f.write(file + "\n")

    # -----------------------------
    # save combined list
    # -----------------------------
    with open("needs_rerun.txt", "w", encoding="utf-8") as f:
        for file in sorted(combined):
            f.write(file + "\n")

    print("\nSaved:")
    print("- detailed_report.txt (separate categories)")
    print("- needs_rerun.txt (combined list)")
    
    print("Family Faces Count:", familyFacesCount)