import os
from pathlib import Path

def generate_tree(startpath, output_file=None, ignore_patterns=None):
    """
    Generate a tree-like directory structure and optionally write to a file.
    
    Args:
        startpath (str): Root directory to start from
        output_file (str, optional): File to write the tree to. If None, prints to console
        ignore_patterns (list, optional): List of patterns to ignore (e.g., ['.git', '__pycache__'])
    """
    if ignore_patterns is None:
        ignore_patterns = ['.git', '__pycache__', '*.pyc', '.pytest_cache', 'venv', 'ENV']
    
    def should_ignore(path):
        return any(pattern in path for pattern in ignore_patterns)
    
    output_lines = []
    
    def add_line(line):
        if output_file:
            output_lines.append(line)
        else:
            print(line)
    
    add_line(startpath)
    
    for root, dirs, files in os.walk(startpath):
        if should_ignore(root):
            continue
            
        # Calculate the current depth and prefix
        level = root.replace(startpath, '').count(os.sep)
        indent = '│   ' * level
        
        # Filter out ignored directories
        dirs[:] = [d for d in dirs if not should_ignore(os.path.join(root, d))]
        
        # Add directories
        for d in dirs:
            if not should_ignore(os.path.join(root, d)):
                add_line(f'{indent}├── {d}/')
        
        # Add files
        for f in files:
            if not should_ignore(os.path.join(root, f)):
                add_line(f'{indent}├── {f}')
    
    # Write to file if specified
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        print(f"Tree structure written to {output_file}")

if __name__ == "__main__":
    # Get the current directory
    current_dir = os.getcwd()
    
    # Define patterns to ignore
    ignore_patterns = [
        '.git',
        '__pycache__',
        '*.pyc',
        '.pytest_cache',
        'venv',
        'ENV',
        '.idea',
        '.vscode',
        '*.egg-info'
    ]
    
    # Generate the tree and save to 'directory_structure.txt'
    generate_tree(
        current_dir,
        output_file='directory_structure.txt',
        ignore_patterns=ignore_patterns
    )