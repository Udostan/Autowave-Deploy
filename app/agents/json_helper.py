"""
Helper functions for JSON parsing and cleanup.
"""

import re
import json

def clean_json_string(json_str):
    """
    Clean up a JSON string to make it more likely to parse correctly.
    
    Args:
        json_str (str): The JSON string to clean
        
    Returns:
        str: The cleaned JSON string
    """
    # Remove any leading/trailing whitespace
    json_str = json_str.strip()
    
    # Remove backticks (common in LLM responses)
    json_str = json_str.replace('`', '')
    
    # Remove any trailing commas before closing brackets (common JSON error)
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)
    
    # Fix escaped quotes inside strings (common when LLMs generate JSON)
    json_str = re.sub(r'\\"', '"', json_str)
    
    # Fix unescaped quotes inside strings
    json_str = re.sub(r'(?<!\\)"(?=[^"]*"\s*:)', '\\"', json_str)
    
    # Fix backslash escaping issues
    json_str = json_str.replace('\\n', '\n')
    json_str = json_str.replace('\\t', '\t')
    
    # Fix common JSON syntax errors
    json_str = re.sub(r'"([a-zA-Z0-9_]+)"\s*:', r'"\1":', json_str)  # Fix spacing in keys
    
    # Replace single quotes with double quotes (another common LLM error)
    json_str = re.sub(r"'([^']*)'\\s*:", r'"\1":', json_str)  # Fix single quotes in keys
    json_str = re.sub(r":\\s*'([^']*)'([,}])", r':"\1"\2', json_str)  # Fix single quotes in values
    
    return json_str

def extract_json_from_text(text, pattern=None):
    """
    Extract JSON from text using multiple approaches.
    
    Args:
        text (str): The text to extract JSON from
        pattern (str, optional): A specific pattern to look for. Defaults to None.
        
    Returns:
        str: The extracted JSON string
    """
    # Try to find JSON in code blocks with json tag
    json_match = re.search(r'```(?:json)\s*({.*?})\s*```', text, re.DOTALL)
    if json_match:
        return json_match.group(1)
    
    # Try to find JSON between triple backticks without json tag
    json_match = re.search(r'```\s*({\s*"files".*?})\s*```', text, re.DOTALL)
    if json_match:
        return json_match.group(1)
    
    # Try to find JSON in code blocks with any tag
    json_match = re.search(r'```\w*\s*({\s*"files"\s*:\s*\[.*?\]\s*})\s*```', text, re.DOTALL)
    if json_match:
        return json_match.group(1)
    
    # Try to find any JSON object with a files array
    json_match = re.search(r'({\s*"files"\s*:\s*\[.*?\]\s*})', text, re.DOTALL)
    if json_match:
        return json_match.group(1)
    
    # Try to find any array of file objects
    json_match = re.search(r'"files"\s*:\s*(\[\s*{.*?}\s*\])', text, re.DOTALL)
    if json_match:
        files_array = json_match.group(1)
        return '{"files": ' + files_array + '}'
    
    # If a specific pattern is provided, try that
    if pattern:
        json_match = re.search(pattern, text, re.DOTALL)
        if json_match:
            return json_match.group(1)
    
    # Use the entire text as a last resort
    return text

def parse_json_safely(json_str):
    """
    Parse a JSON string safely, with multiple fallback approaches.
    
    Args:
        json_str (str): The JSON string to parse
        
    Returns:
        dict or None: The parsed JSON object, or None if parsing failed
    """
    # Clean the JSON string first
    json_str = clean_json_string(json_str)
    
    try:
        # Try to parse the JSON directly
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Initial JSON parsing failed: {str(e)}")
        
        # Try to extract just the files array if present
        files_match = re.search(r'"files"\s*:\s*(\[.*?\])(?:,|\s*})', json_str, re.DOTALL)
        if files_match:
            files_array = files_match.group(1)
            try:
                files_data = json.loads(files_array)
                return {"files": files_data}
            except:
                pass
        
        # Try to fix common JSON syntax errors and try again
        try:
            # Replace single quotes with double quotes
            fixed_str = json_str.replace("'", '"')
            return json.loads(fixed_str)
        except:
            pass
        
        # Try to parse line by line for array items
        if '[' in json_str and ']' in json_str:
            try:
                # Extract content between square brackets
                array_content = re.search(r'\[(.*)\]', json_str, re.DOTALL)
                if array_content:
                    content = array_content.group(1)
                    # Split by items that look like they might be separate objects
                    items = re.split(r'},\s*{', content)
                    if len(items) > 1:
                        # Reconstruct items
                        fixed_items = []
                        for i, item in enumerate(items):
                            if i == 0:
                                if not item.startswith('{'):
                                    item = '{' + item
                            else:
                                if not item.startswith('{'):
                                    item = '{' + item
                            if i == len(items) - 1:
                                if not item.endswith('}'):
                                    item = item + '}'
                            else:
                                if not item.endswith('}'):
                                    item = item + '}'
                            try:
                                # Try to parse each item
                                json.loads(item)
                                fixed_items.append(item)
                            except:
                                # If it fails, try to clean it more aggressively
                                cleaned_item = re.sub(r'[^{}[\],:"0-9a-zA-Z_.\-+]', '', item)
                                fixed_items.append(cleaned_item)
                        
                        # Reconstruct the array
                        fixed_array = '[' + ','.join(fixed_items) + ']'
                        try:
                            files_data = json.loads(fixed_array)
                            return {"files": files_data}
                        except:
                            pass
            except:
                pass
    
    # If all parsing attempts fail, return None
    return None
