import os
import re
import json
import sys


def parse_function_signatures(pr_file):
    """
    Parse function definitions in a file to extract function names and return signatures.
    """
    functions = {}
    try:
        with open(pr_file, 'r') as file:
            content = file.readlines()
            for line in content:
                # Match function definitions with return types
                match = re.match(r'^\s*func\s+([a-zA-Z0-9_]+)\s*\(.*\)\s*\((.*)\)\s*{', line)
                if match:
                    func_name = match.group(1)
                    return_signature = match.group(2).split(",") if match.group(2) else []
                    functions[func_name] = [r.strip() for r in return_signature]
    except Exception as e:
        print(f"Error parsing file {pr_file}: {str(e)}")
    return functions


def check_function_calls(pr_file, helper_signatures):
    """
    Check if function calls in a file match the helper function return signatures.
    """
    notes = []
    try:
        with open(pr_file, 'r') as file:
            content = file.readlines()
            for line in file:
              print(f"Processing line: {content.strip()}")
            for i, line in enumerate(content):
                # Match function calls like `var, err := helper()`
                match = re.match(r'\s*(?:(?:[a-zA-Z0-9_]+, )*[a-zA-Z0-9_]+\s*):=\s*([a-zA-Z0-9_]+)\s*\(', line)
                if match:
                    func_name = match.group(1)
                    if func_name in helper_signatures:
                        # Get the expected return count
                        expected_count = len(helper_signatures[func_name])

                        # Count variables in the test
                        assigned_vars = line.split(":=")[0].split(",")
                        actual_count = len([v.strip() for v in assigned_vars if v.strip()])

                        if actual_count != expected_count:
                            notes.append({
                                "file": pr_file,
                                "line": i + 1,
                                "comment": f"Function '{func_name}' is expected to return {expected_count} value(s), but the test assigns {actual_count} variable(s)."
                            })
    except Exception as e:
        notes.append({
            "file": pr_file,
            "line": 0,
            "comment": f"Error reading file {pr_file}: {str(e)}"
        })
    return notes


def check_function_names(pr_file):
    """
    Check if function names follow Go standards, i.e., camelCase letters.
    """
    notes = []
    try:
        with open(pr_file, 'r') as file:
            content = file.readlines()
            for line in file:
              print(f"Processing line: {content.strip()}")
            for i, line in enumerate(content):
                # Match function definitions
                match = re.match(r'^\s*func\s+([a-zA-Z0-9_]+)\s*\(', line)
                if match:
                    func_name = match.group(1)

                    # Check if function is public or private
                    is_public = func_name[0].isupper()

                    # Check if function name is in CamelCase
                    if not re.match(r'^[A-Z]?[a-zA-Z0-9]+$', func_name):
                        notes.append({
                            "file": pr_file,
                            "line": i + 1,
                            "comment": f"{'Public' if is_public else 'Private'} function '{func_name}' does not follow CamelCase naming convention."
                        })
    except Exception as e:
        notes.append({
            "file": pr_file,
            "line": 0,
            "comment": f"Error reading file {pr_file}: {str(e)}"
        })
    print("These are the notes from check_function_names")
    print(notes)
    return notes


def check_public_functions_missing_comments(pr_file):
    """
    Check if public functions have missing comments in Go files.
    """
    notes = []
    try:
        if pr_file.endswith("_test.go"):
            return notes  # Skip `_test.go` files
    
        with open(pr_file, 'r') as file:
            content = file.readlines()
            for line in file:
              print(f"Processing line: {content.strip()}")
            for i, line in enumerate(content):
                # Match public functions
                public_func_match = re.match(r'^\s*func\s+([A-Z][a-zA-Z0-9_]*)\s*\(', line)
                if public_func_match:
                    func_name = public_func_match.group(1)
                    # Check if the line above is a comment
                    if i == 0 or not content[i - 1].strip().startswith("//"):
                        notes.append({
                            "file": pr_file,
                            "line": i + 1,
                            "comment": f"Public function '{func_name}' is missing a comment."
                        })
    except Exception as e:
        notes.append({
            "file": pr_file,
            "line": 0,
            "comment": f"Error reading file {pr_file}: {str(e)}"
        })
    print("These are the notes from check_function_names")
    print(notes)
    return notes


def check_err_usage(pr_file):
    """
    Check for unused `err` variables in the code.
    """
    notes = []
    try:
        with open(pr_file, 'r') as file:
            content = file.readlines()
            for line in file:
              print(f"Processing line: {content.strip()}")
            for i, line in enumerate(content):
                line = line.strip()

                if re.match(r'\s*return\s+err\b', line):
                    continue

                if re.match(r'\s*(?:[a-zA-Z_]+, )?err\s*(?::=|=)\s*.*', line):
                    if i + 1 < len(content):
                        next_line = content[i + 1].strip()
                        if not re.search(r'(require\.NoError\(err\)|assert\.Error\(err\)|require\.Error\(err\))', next_line):
                            notes.append({
                                "file": pr_file,
                                "line": i + 2,
                                "comment": "Detected `err` assignment without proper error handling on the next line."
                            })
    except Exception as e:
        notes.append({
            "file": pr_file,
            "line": 0,
            "comment": f"Error reading file {pr_file}: {str(e)}"
        })
    print("These are the notes from check_function_names")
    print(notes)
    return notes

def check_unused_parameters(pr_file):
    """
    Check if function definitions contain parameters that are not used in the function body.
    """
    notes = []
    try:
        with open(pr_file, 'r') as file:
            content = file.readlines()
            in_function = False
            current_function = None
            parameters = []
            function_body = []

            for i, line in enumerate(content):
                # Match function definitions
                func_match = re.match(r'^\s*func\s+[a-zA-Z0-9_]+\s*\((.*)\)\s*', line)
                if func_match:
                    in_function = True
                    current_function = i + 1
                    function_body = []
                    params = func_match.group(1)

                    # Parse parameters (e.g., "a int, b string" -> ["a", "b"])
                    parameters = [
                        param.split()[-1].strip()
                        for param in params.split(",") if param.strip()
                    ]
                    continue

                # End of function body
                if in_function and line.strip() == "}":
                    in_function = False

                    # Check for unused parameters
                    for param in parameters:
                        if param not in " ".join(function_body):
                            notes.append({
                                "file": pr_file,
                                "line": current_function,
                                "comment": f"Parameter '{param}' is defined but not used in the function."
                            })
                    parameters = []
                    function_body = []
                    continue

                # Collect function body lines
                if in_function:
                    function_body.append(line.strip())
    except Exception as e:
        notes.append({
            "file": pr_file,
            "line": 0,
            "comment": f"Error reading file {pr_file}: {str(e)}"
        })
    return notes

def check_recurring_run_comment(file_path):
    """
    Check if a `_test.go` file contains any line starting with `//go:build`.
    """
    notes = []
    try:
        with open(file_path, 'r') as file:
            content = file.readlines()
            print("printing contents in recurring function", content)
            has_go_build_comment = any(line.strip().startswith("//go:build") for line in content)

            if not has_go_build_comment:
                notes.append({
                    "file": file_path,
                    "line": 0,  
                    "line": 0,  
                    "comment": "Missing required `//go:build` comment."
                })
    except Exception as e:
        notes.append({
            "file": file_path,
            "line": 0,
            "comment": f"Error reading file {file_path}: {str(e)}"
        })
    return notes

def parse_structured_changes(file_path, helper_signatures):
    notes = []
    file_contents_map = {}

    try:
        with open(file_path, "r") as file:
            current_file = None
            diff_lines = []
            for line in file:
                # Match file header lines
                if re.search(r".*\.go:", line):
                    current_file = line.split(".go:")[0].strip()
                    if current_file not in file_contents_map:
                        file_contents_map[current_file] = []
                else:
                    if current_file:
                        file_contents_map[current_file].append(line.strip())
                    else:
                        print(f"Warning: Found a line without a valid file header: {line.strip()}")
            # Process the last file
            notes.extend(process_file(file_contents_map, helper_signatures))
    except Exception as e:
        notes.append({
            "file": file_path,
            "line": 0,
            "comment": f"Error reading structured changes: {str(e)}"
        })
    return notes


def process_file(file_contents_map, helper_signatures=None):
    notes = []

    print("IN process_file, this is diff lines and filename")

    for filename, contents in file_contents_map.items():
        # Create a temporary file with the file's contents
        print("contenst in process_file", contents)
        temp_file = f"/tmp/{filename.replace('/', '_')}"
        with open(temp_file, "w") as temp:
            processed_contents = [line.replace("+", "") for line in contents]
            temp.write("\n".join(processed_contents))
    

        if filename.endswith("_test"):
            
    #     if helper_signatures:
    #         notes.extend(check_function_calls(temp_file, helper_signatures))
    #     else:
    #         print(f"Skipping function call checks for {filename} (no helper signatures available)")
            notes.extend(check_recurring_run_comment(temp_file))


        notes.extend(check_function_names(temp_file))
        notes.extend(check_public_functions_missing_comments(temp_file))
        notes.extend(check_err_usage(temp_file))
        notes.extend(check_unused_parameters(temp_file))

    return notes

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 pr_review_script.py <structured_changes_file>")
        sys.exit(1)

    structured_file = sys.argv[1]

    # Debugging: Print structured file
    print(f"Processing structured changes file: {structured_file}")


    helper_signatures = {}

    changed_files = []  

    with open(structured_file, "r") as file:
        print("COntent of the structured_file: ")
        print(file)

    # Extract helper function signatures from non-test `.go` files
    for pr_file in changed_files:
        if pr_file.endswith(".go") and not pr_file.endswith("_test.go"):
            print(f"Parsing helper signatures from: {pr_file}")
            helper_signatures.update(parse_function_signatures(pr_file))

    # Debugging: Print collected helper signatures
    print("Collected helper signatures:")
    print(helper_signatures)

    review_notes = parse_structured_changes(structured_file, helper_signatures)

    # Output review notes to a JSON file
    print("Generated review notes:")
    print(review_notes)
    with open("review_notes.json", "w") as notes_file:
        json.dump(review_notes, notes_file, indent=2)

