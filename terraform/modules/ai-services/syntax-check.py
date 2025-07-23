#!/usr/bin/env python3
"""
Simple HCL syntax validation script for AI Services module
This script performs basic syntax checks on Terraform files
"""

import os
import re
import sys
from pathlib import Path

def check_hcl_syntax(file_path):
    """Basic HCL syntax validation"""
    errors = []
    
    with open(file_path, 'r') as f:
        content = f.read()
        lines = content.split('\n')
    
    # Check for balanced braces
    brace_count = 0
    bracket_count = 0
    paren_count = 0
    
    for line_num, line in enumerate(lines, 1):
        # Skip comments
        if line.strip().startswith('#'):
            continue
            
        # Count braces, brackets, parentheses
        brace_count += line.count('{') - line.count('}')
        bracket_count += line.count('[') - line.count(']')
        paren_count += line.count('(') - line.count(')')
        
        # Check for common syntax issues
        if '=' in line and not re.search(r'["\w\]]\s*=\s*["\w\[\{]', line):
            if not line.strip().endswith('=') and '==' not in line:
                errors.append(f"Line {line_num}: Possible assignment syntax issue")
    
    # Check final balance
    if brace_count != 0:
        errors.append(f"Unbalanced braces: {brace_count}")
    if bracket_count != 0:
        errors.append(f"Unbalanced brackets: {bracket_count}")
    if paren_count != 0:
        errors.append(f"Unbalanced parentheses: {paren_count}")
    
    return errors

def check_terraform_structure(directory):
    """Check Terraform module structure"""
    required_files = ['main.tf', 'variables.tf', 'outputs.tf']
    errors = []
    
    for file in required_files:
        file_path = os.path.join(directory, file)
        if not os.path.exists(file_path):
            errors.append(f"Missing required file: {file}")
        else:
            file_errors = check_hcl_syntax(file_path)
            if file_errors:
                errors.extend([f"{file}: {error}" for error in file_errors])
    
    return errors

def main():
    """Main validation function"""
    module_dir = Path(__file__).parent
    print(f"Validating AI Services module in: {module_dir}")
    
    errors = check_terraform_structure(module_dir)
    
    if errors:
        print("❌ Validation failed with errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("✅ Basic syntax validation passed!")
        print("Note: This is a basic check. Run 'terraform validate' for full validation.")

if __name__ == "__main__":
    main()