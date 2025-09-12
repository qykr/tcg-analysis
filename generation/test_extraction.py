#!/usr/bin/env python3
"""Test script for code extraction functionality."""

from prompts import extract_python_code, get_naive_coder_prompt, get_reasoner_prompt, get_reasoner_schema

def test_code_extraction():
    """Test the code extraction functionality."""
    print("🧪 Testing code extraction...")
    
    test_text = '''
Here is some explanation.

```python
def hello():
    return 'world'
```

More text here.

```python
def goodbye():
    return 'universe'
```
'''
    
    code = extract_python_code(test_text)
    print(f"Extracted code: {repr(code)}")
    
    expected = "def goodbye():\n    return 'universe'"
    if code == expected:
        print("✅ Code extraction test passed!")
    else:
        print(f"❌ Code extraction test failed!")
        print(f"Expected: {repr(expected)}")
        print(f"Got: {repr(code)}")

def test_prompts():
    """Test the prompt functions."""
    print("\n🧪 Testing prompt functions...")
    
    # Test naive coder prompt
    naive_prompt = get_naive_coder_prompt("Test problem", "Test input format")
    print(f"Naive coder prompt length: {len(naive_prompt)}")
    
    # Test reasoner prompt  
    reasoner_prompt = get_reasoner_prompt("Test problem", "Test input format")
    print(f"Reasoner prompt length: {len(reasoner_prompt)}")
    
    # Test schema
    schema = get_reasoner_schema()
    print(f"Schema has {len(schema['properties'])} properties")
    
    print("✅ Prompt functions test passed!")

if __name__ == "__main__":
    test_code_extraction()
    test_prompts()
    print("\n🎉 All tests completed!")
