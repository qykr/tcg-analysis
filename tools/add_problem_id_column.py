import csv
import sys
from pathlib import Path


def main():
    project_root = Path(__file__).resolve().parents[1]
    src = project_root / 'output.csv'
    dst = project_root / 'output_with_ids.csv'

    if not src.exists():
        print(f'Source CSV not found: {src}', file=sys.stderr)
        sys.exit(1)

    # Allow very large CSV fields
    try:
        csv.field_size_limit(sys.maxsize)
    except OverflowError:
        csv.field_size_limit(10 ** 9)

    with src.open('r', newline='', encoding='utf-8') as f_in, dst.open('w', newline='', encoding='utf-8') as f_out:
        reader = csv.reader(f_in)
        writer = csv.writer(f_out)

        try:
            header = next(reader)
        except StopIteration:
            print('Source CSV is empty', file=sys.stderr)
            sys.exit(1)

        # Prepend problem_id header
        writer.writerow(['problem_id'] + header)

        # Write rows with 1-based problem_id index
        for idx, row in enumerate(reader, start=1):
            writer.writerow([idx] + row)

    print(f'Wrote {dst}')


if __name__ == '__main__':
    main()


