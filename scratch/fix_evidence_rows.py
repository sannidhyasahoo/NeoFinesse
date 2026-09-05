import json
import re
import csv
from pathlib import Path

# Paths
base_dir = Path(r"C:\Users\sanni\Desktop\Razorpay Hackathon\NeoFinesse")
ts_file = base_dir / "frontend" / "src" / "data" / "benchmarkData.ts"
demo_data_dir = base_dir / "data" / "demo_dataset"

# Load the TS file content
content = ts_file.read_text(encoding="utf-8")

# Extract the JSON part
match = re.search(r"export const benchmarkData: BenchmarkData = (\{.*\});?\s*$", content, re.DOTALL)
if not match:
    raise ValueError("Could not find JSON object in TS file")

json_str = match.group(1)
data = json.loads(json_str)

# Cache CSV rows to avoid re-reading
csv_cache = {}

def get_row_index(filename: str, entity_key: str) -> int:
    if filename not in csv_cache:
        file_path = demo_data_dir / filename
        if not file_path.exists():
            print(f"Warning: File {filename} not found.")
            return -1
        
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            csv_cache[filename] = list(reader)
            
    rows = csv_cache[filename]
    # Extract the base scenario identifier from entity_key, e.g. "scen_001" or "base_001"
    match = re.search(r"(scen_\d+|base_\d+|var-\d+|ag-\d+)", entity_key, re.IGNORECASE)
    search_key = match.group(1).lower() if match else entity_key.lower()

    for idx, row in enumerate(rows):
        # 1-indexed row number
        # Just search for the search_key anywhere in the row
        row_str = ",".join(row).lower()
        if search_key in row_str:
            return idx + 1
    return -1

updated = 0

for scenario in data.get("scenarios", []):
    for node_list in [scenario.get("evidence_nodes", []), scenario.get("rejected_decoys", [])]:
        for node in node_list:
            if "source_file" in node and "entity_key" in node:
                filename = node["source_file"]
                entity_key = node["entity_key"]
                
                real_row = get_row_index(filename, entity_key)
                if real_row != -1:
                    if node.get("row") != real_row:
                        old_row = node.get("row")
                        node["row"] = real_row
                        
                        # Update cell address (e.g. F31 -> F<real_row>)
                        cell = node.get("cell", "")
                        if cell:
                            # Match column letter(s)
                            cell_match = re.match(r"^([A-Za-z]+)\d+$", cell)
                            if cell_match:
                                col_letter = cell_match.group(1)
                                node["cell"] = f"{col_letter}{real_row}"
                                
                        print(f"Updated {entity_key} in {filename}: row {old_row} -> {real_row}")
                        updated += 1
                else:
                    print(f"Warning: Entity {entity_key} not found in {filename}")

if updated > 0:
    # Serialize back to TS format
    new_json_str = json.dumps(data, indent=2)
    # The TS file uses single quotes for some things, but JSON is fine
    new_content = content[:match.start(1)] + new_json_str + content[match.end(1):]
    ts_file.write_text(new_content, encoding="utf-8")
    print(f"Successfully updated {updated} cell references in benchmarkData.ts")
else:
    print("No updates needed or no matches found.")
