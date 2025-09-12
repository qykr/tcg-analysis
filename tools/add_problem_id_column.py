import json
import sys
from pathlib import Path


def main():
    project_root = Path(__file__).resolve().parents[1]
    src = project_root / 'data' / 'validation_problems.json'
    dst = project_root / 'data' / 'validation_problems_with_ids.json'

    if not src.exists():
        print(f'Source JSON not found: {src}', file=sys.stderr)
        sys.exit(1)

    # Load the JSON data
    with src.open('r', encoding='utf-8') as f:
        data = json.load(f)

    # The JSON structure already has problem indices as keys, so we just copy it
    # This tool is mainly for compatibility - the JSON format already has proper indices
    with dst.open('w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f'Wrote {dst}')
    print('Note: validation_problems.json already has proper problem indices as keys')


if __name__ == '__main__':
    main()


