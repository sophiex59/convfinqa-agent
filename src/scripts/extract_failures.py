import re
from pathlib import Path

def extract_failures(log_path: str, output_path: str):
    """Extracts the 'DETAILED LOGS' section from the evaluation log."""
    log_file = Path(log_path)
    if not log_file.exists():
        print(f"Error: {log_path} not found.")
        return

    content = log_file.read_text(encoding="utf-8")
    
    # regex to find the start of the detailed logs section
    # It looks like: ═══ DETAILED LOGS FOR FAILED RECORDS (37) ═══
    match = re.search(r"═══ DETAILED LOGS FOR FAILED RECORDS .*?═══", content)
    
    if not match:
        print("Could not find 'DETAILED LOGS FOR FAILED RECORDS' section in the log.")
        return

    start_index = match.start()
    detailed_logs = content[start_index:]
    
    # Optional: Clean up or parse further if needed. 
    # For now, just dumping the raw section is what was requested (the "details bit").
    
    Path(output_path).write_text(detailed_logs, encoding="utf-8")
    print(f"Extracted failure logs to {output_path}")
    print(f"Section Header: {match.group(0)}")

if __name__ == "__main__":
    extract_failures("eval_final.log", "failure_details.txt")
