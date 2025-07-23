package test

import (
	"testing"

	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/stretchr/testify/assert"
)

func TestAIServicesModule(t *testing.T) {
	t.Parallel()

	// Define the Terraform options
	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		// Path to the Terraform code that will be tested
		TerraformDir: "../",

		// Variables to pass to the Terraform code using -var options
		Vars: map[string]interface{}{
			"project_name":             "test-ai-assistant",
			"environment":              "test",
			"aws_region":               "us-east-1",
			"vpc_id":                   "vpc-12345678",
			"private_subnet_ids":       []string{"subnet-12345678", "subnet-87654321"},
			"lambda_security_group_id": "sg-12345678",
			"tags": map[string]string{
				"Environment": "test",
				"Project":     "test-ai-assistant",
			},
		},

		// Disable colors in Terraform commands so it's easier to parse stdout/stderr
		NoColor: true,
	})

	// Clean up resources with "terraform destroy" at the end of the test
	defer terraform.Destroy(t, terraformOptions)

	// Run "terraform init" and "terraform plan"
	terraform.InitAndPlan(t, terraformOptions)

	// Run "terraform apply"
	terraform.Apply(t, terraformOptions)

	// Test outputs
	testOutputs(t, terraformOptions)
}

func testOutputs(t *testing.T, terraformOptions *terraform.Options) {
	// Test S3 bucket outputs
	s3BucketName := terraform.Output(t, terraformOptions, "knowledge_base_s3_bucket_name")
	assert.Contains(t, s3BucketName, "test-ai-assistant-test-knowledge-base-data")

	s3BucketArn := terraform.Output(t, terraformOptions, "knowledge_base_s3_bucket_arn")
	assert.Contains(t, s3BucketArn, "arn:aws:s3:::test-ai-assistant-test-knowledge-base-data")

	// Test OpenSearch collection outputs
	opensearchEndpoint := terraform.Output(t, terraformOptions, "opensearch_collection_endpoint")
	assert.NotEmpty(t, opensearchEndpoint)

	opensearchArn := terraform.Output(t, terraformOptions, "opensearch_collection_arn")
	assert.Contains(t, opensearchArn, "arn:aws:aoss:")

	// Test IAM role outputs
	bedrockRoleArn := terraform.Output(t, terraformOptions, "bedrock_knowledge_base_role_arn")
	assert.Contains(t, bedrockRoleArn, "arn:aws:iam::")
	assert.Contains(t, bedrockRoleArn, "test-ai-assistant-test-bedrock-kb-role")

	lambdaRoleArn := terraform.Output(t, terraformOptions, "lambda_bedrock_role_arn")
	assert.Contains(t, lambdaRoleArn, "arn:aws:iam::")
	assert.Contains(t, lambdaRoleArn, "test-ai-assistant-test-lambda-bedrock-role")

	// Test Knowledge Base outputs
	knowledgeBaseId := terraform.Output(t, terraformOptions, "knowledge_base_id")
	assert.NotEmpty(t, knowledgeBaseId)

	knowledgeBaseArn := terraform.Output(t, terraformOptions, "knowledge_base_arn")
	assert.Contains(t, knowledgeBaseArn, "arn:aws:bedrock:")

	// Test CloudWatch log group outputs
	bedrockLogGroup := terraform.Output(t, terraformOptions, "bedrock_api_log_group_name")
	assert.Equal(t, "/aws/bedrock/test-ai-assistant-test", bedrockLogGroup)

	kbLogGroup := terraform.Output(t, terraformOptions, "knowledge_base_log_group_name")
	assert.Equal(t, "/aws/bedrock/knowledge-base/test-ai-assistant-test", kbLogGroup)
}

func TestAIServicesModuleValidation(t *testing.T) {
	t.Parallel()

	// Test with invalid environment
	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../",
		Vars: map[string]interface{}{
			"project_name":             "test-ai-assistant",
			"environment":              "invalid-env",
			"aws_region":               "us-east-1",
			"vpc_id":                   "vpc-12345678",
			"private_subnet_ids":       []string{"subnet-12345678"},
			"lambda_security_group_id": "sg-12345678",
		},
		NoColor: true,
	})

	// This should fail due to validation
	_, err := terraform.InitAndPlanE(t, terraformOptions)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "Environment must be one of")
}

func TestAIServicesModuleWithCustomValues(t *testing.T) {
	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../",
		Vars: map[string]interface{}{
			"project_name":                      "custom-ai-assistant",
			"environment":                       "staging",
			"aws_region":                        "us-west-2",
			"vpc_id":                            "vpc-87654321",
			"private_subnet_ids":                []string{"subnet-11111111", "subnet-22222222"},
			"lambda_security_group_id":          "sg-87654321",
			"log_retention_days":                60,
			"knowledge_base_embedding_model":    "amazon.titan-embed-text-v1",
			"knowledge_base_chunking_strategy":  "FIXED_SIZE",
			"knowledge_base_chunk_size":         500,
			"knowledge_base_chunk_overlap":      30,
			"bedrock_models": []string{
				"amazon.nova-pro-v1:0",
				"amazon.nova-lite-v1:0",
			},
		},
		NoColor: true,
	})

	defer terraform.Destroy(t, terraformOptions)

	terraform.InitAndPlan(t, terraformOptions)
	terraform.Apply(t, terraformOptions)

	// Test custom values are applied
	embeddingModel := terraform.Output(t, terraformOptions, "embedding_model")
	assert.Equal(t, "amazon.titan-embed-text-v1", embeddingModel)
}