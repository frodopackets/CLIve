# Outputs for security module

output "lambda_security_group_id" {
  description = "ID of the Lambda security group"
  value       = awscc_ec2_security_group.lambda.id
}

output "api_gateway_security_group_id" {
  description = "ID of the API Gateway security group"
  value       = awscc_ec2_security_group.api_gateway.id
}

output "vpc_endpoints_security_group_id" {
  description = "ID of the VPC endpoints security group"
  value       = awscc_ec2_security_group.vpc_endpoints.id
}

output "waf_web_acl_id" {
  description = "ID of the WAF Web ACL"
  value       = aws_wafv2_web_acl.api_protection.id
}

output "waf_web_acl_arn" {
  description = "ARN of the WAF Web ACL"
  value       = aws_wafv2_web_acl.api_protection.arn
}

output "waf_log_group_name" {
  description = "Name of the WAF CloudWatch log group"
  value       = aws_cloudwatch_log_group.waf_logs.name
}