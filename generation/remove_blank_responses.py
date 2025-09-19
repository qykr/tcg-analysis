import json

def remove_blank_responses(input_file: str = "../data/responses.jsonl", output_file: str = "../data/responses.jsonl"):
    """Remove blank responses from the JSONL file."""
    responses = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            stripped_line = line.strip()
            if stripped_line and json.loads(stripped_line)['trace'] != '':
                responses.append(stripped_line)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for response in responses:
            f.write(response + '\n')

if __name__ == "__main__":
    remove_blank_responses(input_file="../data/responses.jsonl", output_file="../data/responses.jsonl")
    remove_blank_responses(input_file="../data/test_responses.jsonl", output_file="../data/test_responses.jsonl")