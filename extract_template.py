import re
import json
import sys

def main():
    try:
        with open("frontend/src/data/benchmarkData.ts", "r", encoding="utf-8") as f:
            content = f.read()

        # Remove the typescript specific export stuff
        content = re.sub(r'import.*?;\n+', '', content)
        content = re.sub(r'export const benchmarkData.*?=\s*', '', content)
        content = re.sub(r';\s*$', '', content)

        # Let's verify it can be parsed as JSON
        data = json.loads(content)
        
        # Write it back cleanly
        with open("benchmark_data_template.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            
        print("Successfully created benchmark_data_template.json")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
