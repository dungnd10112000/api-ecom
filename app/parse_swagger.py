import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

file_path = r"C:\Users\ADMIN\.gemini\antigravity-ide\brain\c7663ee4-1f45-4931-9ba5-2fa3105de98c\.system_generated\steps\287\content.md"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

start_idx = content.find('"swaggerDoc":')
if start_idx != -1:
    brace_start = content.find('{', start_idx)
    if brace_start != -1:
        brace_count = 0
        end_idx = -1
        for i in range(brace_start, len(content)):
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i + 1
                    break
        
        if end_idx != -1:
            json_str = content[brace_start:end_idx]
            try:
                swagger_doc = json.loads(json_str)
                components = swagger_doc.get("components", {})
                schemas = components.get("schemas", {})
                print("All schema models in SwaggerDoc:")
                for s in sorted(schemas.keys()):
                    print(f"  Schema: {s}")
                    props = schemas[s].get("properties", {})
                    for pk, pv in props.items():
                        print(f"    - {pk}: {pv.get('type')} ({pv.get('description', '')})")
            except Exception as e:
                print("Failed to parse JSON:", e)
        else:
            print("Could not find matching closing brace.")
else:
    print("Could not find swaggerDoc key.")
