
import json
import sys
from collections import Counter
from pathlib import Path


def analyze_results(json_path: str):
    """Analyze evaluation results JSON for failure patterns."""
    path = Path(json_path)
    if not path.exists():
        print(f"Error: {json_path} not found.")
        return

    try:
        results = json.loads(path.read_text())
    except json.JSONDecodeError:
        print(f"Error: Could not decode {json_path}")
        return

    total = len(results)
    correct = sum(1 for r in results if r["matched"])
    rejected = sum(1 for r in results if r["is_rejected"])
    errors = [r for r in results if not r["matched"]]

    # Error buckets
    error_types = Counter()

    for i, r in enumerate(results):
        if r["matched"]:
            continue

        pred = str(r["pred"]).strip()
        gold = str(r["gold"]).strip()

        # Heuristics

        # 1. Empty/Safety
        if not pred or "n/a" in pred.lower() or "limit" in pred.lower():
            error_types["Safety/Refusal (Empty/N/A)"] += 1
            continue

        try:
            # Normalize for math checks
            p_val = float(pred.replace("$","").replace(",","").replace("%",""))
            g_val = float(gold.replace("$","").replace(",","").replace("%",""))

            # 2. Unit Scaling (x1000, x1000000)
            if g_val != 0:
                ratio = p_val / g_val
                if 900 < ratio < 1100 or 900000 < ratio < 1100000 or 0.0009 < ratio < 0.0011:
                    error_types["Unit Scaling Issue"] += 1
                    continue
                # Inverted Ratio
                if abs(p_val - (1/g_val)) < 0.01:
                    error_types["Inverted Ratio"] += 1
                    continue

            # 3. Sign Error
            if abs(p_val + g_val) < 0.001 and abs(p_val) > 0.001:
                error_types["Sign Error"] += 1
                continue

            # 4. Percentage Format
            if abs(p_val * 100 - g_val) < 0.1 or abs(p_val - g_val * 100) < 0.1:
                error_types["Percentage Format"] += 1
                continue

            # 5. Propagation Check (Is this Q2+ and did Q[n-1] fail?)
            # We look at previous result in the list if it belongs to same record
            if i > 0 and results[i-1]["record_id"] == r["record_id"] and not results[i-1]["matched"]:
                # Simple heuristic: if previous failed, this might be propagation
                error_types["Likely Propagation Error"] += 1
                continue

            # 6. Extraction Error (Pred exists in text/table but is wrong)
            # Flatten context for searching
            context = str(r.get("pre_text", "")) + str(r.get("post_text", "")) + str(r.get("table", ""))
            if pred in context:
                error_types["Extraction Error (Values Swapped/Wrong Row)"] += 1
                continue

            # 7. Gold Ambiguity (Gold value NOT found in source text/table)
            # If gold is not in context, it might be a derived value or external knowledge
            if gold not in context:
                # Be careful, gold might be formatted differently, simple check
                error_types["Gold Ambiguity (Value not in source)"] += 1
                continue

            error_types["Value Mismatch (Other)"] += 1

        except ValueError:
            error_types["Non-Numeric Mismatch"] += 1

    print(f"═══ ANALYSIS: {path.name} ═══")
    print(f"Total: {total}")
    print(f"Accuracy: {correct}/{total} ({correct/total:.2%})")
    print(f"Rejected (N/A): {rejected} ({rejected/total:.2%})")
    print(f"Total Errors: {len(errors)}")
    print("\n═══ FAILURE PATTERNS ═══")
    for etype, count in error_types.most_common():
        print(f"{etype}: {count} ({count/len(errors):.1%} of errors)")

    # Optional: Print samples of "Value Mismatch" if verbose
    # (Simplified for now)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_results.py <results.json>")
    else:
        analyze_results(sys.argv[1])
