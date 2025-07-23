#!/usr/bin/env python3
"""
Integration test for AI Services Terraform module
Tests the module configuration and resource dependencies
"""

import json
import os
import re
from pathlib import Path

def test_resource_dependencies():
    """Test that resources have proper dependencies"""
    with open('main.tf', 'r') as f:
        content = f.read()
    
    tests = []
    
    # Test 1: Knowledge Base depends on required resources
    kb_resource = re.search(r'resource "awscc_bedrock_knowledge_base" "main" \{.*?\}', content, re.DOTALL)
    if kb_resource:
        kb_content = kb_resource.group(0)
        if 'depends_on' in kb_content:
            tests.append("✅ Knowledge Base has explicit dependencies")
        else:
            tests.append("⚠️  Knowledge Base should have explicit dependencies")
    
    # Test 2: IAM roles have proper assume role policies
    iam_roles = re.findall(r'resource "aws_iam_role" "(\w+)".*?assume_role_policy = jsonencode\((.*?)\)', content, re.DOTALL)
    for role_name, policy in iam_roles:
        if 'bedrock.amazonaws.com' in policy or 'lambda.amazonaws.com' in policy:
            tests.append(f"✅ IAM role {role_name} has proper assume role policy")
        else:
            tests.append(f"❌ IAM role {role_name} may have incorrect assume role policy")
    
    # Test 3: S3 bucket has security configurations
    s3_configs = ['aws_s3_bucket_versioning', 'aws_s3_bucket_server_side_encryption_configuration', 'aws_s3_bucket_public_access_block']
    for config in s3_configs:
        if config in content:
            tests.append(f"✅ S3 bucket has {config}")
        else:
            tests.append(f"❌ S3 bucket missing {config}")
    
    return tests

def test_variable_validations():
    """Test that variables have proper validations"""
    with open('variables.tf', 'r') as f:
        content = f.read()
    
    tests = []
    
    # Test validation blocks exist for critical variables
    critical_vars = ['environment', 'knowledge_base_embedding_model', 'knowledge_base_chunking_strategy']
    for var in critical_vars:
        var_block = re.search(f'variable "{var}".*?validation.*?\}}', content, re.DOTALL)
        if var_block:
            tests.append(f"✅ Variable {var} has validation")
        else:
            tests.append(f"⚠️  Variable {var} should have validation")
    
    return tests

def test_outputs_completeness():
    """Test that outputs provide necessary information"""
    with open('outputs.tf', 'r') as f:
        content = f.read()
    
    tests = []
    
    # Test essential outputs exist
    essential_outputs = [
        'knowledge_base_id',
        'knowledge_base_arn', 
        'lambda_bedrock_role_arn',
        'knowledge_base_s3_bucket_name'
    ]
    
    for output in essential_outputs:
        if f'output "{output}"' in content:
            tests.append(f"✅ Output {output} exists")
        else:
            tests.append(f"❌ Missing essential output: {output}")
    
    return tests

def test_security_best_practices():
    """Test security best practices implementation"""
    with open('main.tf', 'r') as f:
        content = f.read()
    
    tests = []
    
    # Test 1: IAM policies follow least privilege
    if 'bedrock:InvokeModel' in content and 'bedrock:*' not in content:
        tests.append("✅ IAM policies use specific permissions, not wildcards")
    else:
        tests.append("⚠️  Check IAM policies for least privilege principle")
    
    # Test 2: S3 bucket blocks public access
    if 'aws_s3_bucket_public_access_block' in content:
        tests.append("✅ S3 bucket blocks public access")
    else:
        tests.append("❌ S3 bucket should block public access")
    
    # Test 3: Encryption is enabled
    if 'server_side_encryption' in content or 'AES256' in content:
        tests.append("✅ Encryption is configured")
    else:
        tests.append("❌ Encryption should be configured")
    
    # Test 4: CloudWatch monitoring is set up
    if 'aws_cloudwatch_metric_alarm' in content:
        tests.append("✅ CloudWatch monitoring is configured")
    else:
        tests.append("⚠️  Consider adding CloudWatch monitoring")
    
    return tests

def main():
    """Run all tests"""
    print("🧪 Running AI Services Module Integration Tests\n")
    
    os.chdir(Path(__file__).parent)
    
    all_tests = []
    
    print("📋 Testing Resource Dependencies:")
    tests = test_resource_dependencies()
    all_tests.extend(tests)
    for test in tests:
        print(f"  {test}")
    
    print("\n🔧 Testing Variable Validations:")
    tests = test_variable_validations()
    all_tests.extend(tests)
    for test in tests:
        print(f"  {test}")
    
    print("\n📤 Testing Output Completeness:")
    tests = test_outputs_completeness()
    all_tests.extend(tests)
    for test in tests:
        print(f"  {test}")
    
    print("\n🔒 Testing Security Best Practices:")
    tests = test_security_best_practices()
    all_tests.extend(tests)
    for test in tests:
        print(f"  {test}")
    
    # Summary
    passed = len([t for t in all_tests if t.startswith("✅")])
    warnings = len([t for t in all_tests if t.startswith("⚠️")])
    failed = len([t for t in all_tests if t.startswith("❌")])
    
    print(f"\n📊 Test Summary:")
    print(f"  ✅ Passed: {passed}")
    print(f"  ⚠️  Warnings: {warnings}")
    print(f"  ❌ Failed: {failed}")
    
    if failed > 0:
        print("\n❌ Some tests failed. Please review the configuration.")
        return 1
    elif warnings > 0:
        print("\n⚠️  Tests passed with warnings. Consider addressing them.")
        return 0
    else:
        print("\n🎉 All tests passed!")
        return 0

if __name__ == "__main__":
    exit(main())