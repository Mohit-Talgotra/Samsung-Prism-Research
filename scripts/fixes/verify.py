import os
import re

def is_valid(content):
    content = content.strip()
    return bool(re.fullmatch(r"(100\.00|[1-9]?\d\.\d{2})", content))

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

def verify_report(report_path, results_root):
    missing_paths, empty_paths, invalid_paths = parse_report(report_path)

    correct = 0
    wrong = 0

    def check(label, rel_path, condition_fn):
        nonlocal correct, wrong
        full_path = os.path.join(results_root, rel_path)
        ok, reason = condition_fn(full_path)
        if ok:
            correct += 1
        else:
            wrong += 1
            print(f"[WRONG] {label}: {rel_path} — {reason}")

    # --- Missing: file should NOT exist ---
    def is_missing(full_path):
        if not os.path.exists(full_path):
            return True, ""
        return False, "file EXISTS in results (no longer missing)"

    # --- Empty: file should exist and be empty ---
    def is_empty(full_path):
        if not os.path.exists(full_path):
            return False, "file does NOT exist"
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        if not content.strip():
            return True, ""
        return False, f"file is NOT empty (content: {content.strip()[:30]!r})"

    # --- Invalid: file should exist and have invalid content ---
    def is_invalid(full_path):
        if not os.path.exists(full_path):
            return False, "file does NOT exist"
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        if not content.strip():
            return False, "file is EMPTY (not invalid)"
        if not is_valid(content):
            return True, ""
        return False, f"file is actually VALID (content: {content.strip()!r})"

    print(f"\nVerifying {len(missing_paths)} missing, {len(empty_paths)} empty, {len(invalid_paths)} invalid entries...\n")

    for p in missing_paths:
        check("MISSING", p, is_missing)
    for p in empty_paths:
        check("EMPTY", p, is_empty)
    for p in invalid_paths:
        check("INVALID", p, is_invalid)

    total = correct + wrong
    print(f"\n=== VERIFICATION SUMMARY ===")
    print(f"Total checked : {total}")
    print(f"Correct       : {correct}")
    print(f"Wrong         : {wrong}")

if __name__ == "__main__":
    report_path  = "detailed_report.txt"
    results_root = r"C:\Mohit\Repositories\Samsung-Prism-Research\Results\Dataset"

    verify_report(report_path, results_root)