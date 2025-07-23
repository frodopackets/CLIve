package test

import (
	"fmt"
	"strings"
	"testing"
	"time"

	"github.com/gruntwork-io/terratest/modules/aws"
	"github.com/gruntwork-io/terratest/modules/random"
	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestFrontendHostingModule tests the frontend hosting module
func TestFrontendHostingModule(t *testing.T) {
	t.Parallel()

	// Generate a random suffix for unique resource names
	uniqueID := random.UniqueId()
	projectName := fmt.Sprintf("test-ai-cli-%s", strings.ToLower(uniqueID))
	
	// AWS region for testing
	awsRegion := "us-east-1"
	
	// Terraform options
	terraformOptions := &terraform.Options{
		TerraformDir: "../modules/frontend-hosting",
		Vars: map[string]interface{}{
			"project_name":                     projectName,
			"environment":                      "test",
			"aws_region":                       awsRegion,
			"s3_force_destroy":                 true,
			"s3_versioning_enabled":            false,
			"enable_deployment_pipeline":       false, // Disable pipeline for testing
			"enable_cloudwatch_monitoring":     false, // Disable monitoring for testing
			"cloudfront_price_class":           "PriceClass_100",
			"tags": map[string]string{
				"Environment": "test",
				"Project":     projectName,
				"ManagedBy":   "terratest",
			},
		},
		RetryableTerraformErrors: map[string]string{
			"RequestError: send request failed": "Temporary AWS API error",
		},
		MaxRetries:         3,
		TimeBetweenRetries: 5 * time.Second,
	}

	// Clean up resources after test
	defer terraform.Destroy(t, terraformOptions)

	// Deploy the infrastructure
	terraform.InitAndApply(t, terraformOptions)

	// Test S3 bucket creation
	t.Run("S3BucketExists", func(t *testing.T) {
		bucketName := terraform.Output(t, terraformOptions, "s3_bucket_name")
		require.NotEmpty(t, bucketName)
		
		// Verify bucket exists
		aws.AssertS3BucketExists(t, awsRegion, bucketName)
		
		// Verify bucket has website configuration
		websiteConfig := aws.GetS3BucketWebsiteConfiguration(t, awsRegion, bucketName)
		assert.Equal(t, "index.html", websiteConfig.IndexDocument.Suffix)
		assert.Equal(t, "index.html", websiteConfig.ErrorDocument.Key)
	})

	// Test CloudFront distribution creation
	t.Run("CloudFrontDistributionExists", func(t *testing.T) {
		distributionID := terraform.Output(t, terraformOptions, "cloudfront_distribution_id")
		require.NotEmpty(t, distributionID)
		
		// Verify distribution exists and is enabled
		distribution := aws.GetCloudFrontDistribution(t, distributionID)
		assert.True(t, *distribution.Enabled)
		assert.Equal(t, "index.html", *distribution.DefaultRootObject)
		assert.Equal(t, "PriceClass_100", *distribution.PriceClass)
	})

	// Test outputs
	t.Run("OutputsAreValid", func(t *testing.T) {
		// Test S3 outputs
		bucketName := terraform.Output(t, terraformOptions, "s3_bucket_name")
		bucketArn := terraform.Output(t, terraformOptions, "s3_bucket_arn")
		websiteEndpoint := terraform.Output(t, terraformOptions, "s3_website_endpoint")
		
		assert.NotEmpty(t, bucketName)
		assert.Contains(t, bucketArn, bucketName)
		assert.Contains(t, websiteEndpoint, bucketName)
		
		// Test CloudFront outputs
		distributionID := terraform.Output(t, terraformOptions, "cloudfront_distribution_id")
		distributionArn := terraform.Output(t, terraformOptions, "cloudfront_distribution_arn")
		domainName := terraform.Output(t, terraformOptions, "cloudfront_domain_name")
		distributionURL := terraform.Output(t, terraformOptions, "cloudfront_distribution_url")
		
		assert.NotEmpty(t, distributionID)
		assert.Contains(t, distributionArn, distributionID)
		assert.NotEmpty(t, domainName)
		assert.Equal(t, fmt.Sprintf("https://%s", domainName), distributionURL)
	})

	// Test security configuration
	t.Run("SecurityConfiguration", func(t *testing.T) {
		bucketName := terraform.Output(t, terraformOptions, "s3_bucket_name")
		
		// Verify bucket public access is blocked
		publicAccessBlock := aws.GetS3BucketPublicAccessBlock(t, awsRegion, bucketName)
		assert.True(t, *publicAccessBlock.BlockPublicAcls)
		assert.True(t, *publicAccessBlock.BlockPublicPolicy)
		assert.True(t, *publicAccessBlock.IgnorePublicAcls)
		assert.True(t, *publicAccessBlock.RestrictPublicBuckets)
		
		// Verify bucket encryption
		encryption := aws.GetS3BucketEncryption(t, awsRegion, bucketName)
		assert.NotEmpty(t, encryption.Rules)
		assert.Equal(t, "AES256", *encryption.Rules[0].ApplyServerSideEncryptionByDefault.SSEAlgorithm)
	})
}

// TestFrontendHostingModuleWithPipeline tests the frontend hosting module with deployment pipeline enabled
func TestFrontendHostingModuleWithPipeline(t *testing.T) {
	t.Parallel()

	// Generate a random suffix for unique resource names
	uniqueID := random.UniqueId()
	projectName := fmt.Sprintf("test-ai-cli-pipeline-%s", strings.ToLower(uniqueID))
	
	// AWS region for testing
	awsRegion := "us-east-1"
	
	// Terraform options
	terraformOptions := &terraform.Options{
		TerraformDir: "../modules/frontend-hosting",
		Vars: map[string]interface{}{
			"project_name":                     projectName,
			"environment":                      "test",
			"aws_region":                       awsRegion,
			"s3_force_destroy":                 true,
			"s3_versioning_enabled":            false,
			"enable_deployment_pipeline":       true,
			"enable_cloudwatch_monitoring":     true,
			"cloudfront_price_class":           "PriceClass_100",
			"github_repo_owner":                "test-owner",
			"github_repo_name":                 "test-repo",
			"github_branch":                    "main",
			"tags": map[string]string{
				"Environment": "test",
				"Project":     projectName,
				"ManagedBy":   "terratest",
			},
		},
		RetryableTerraformErrors: map[string]string{
			"RequestError: send request failed": "Temporary AWS API error",
		},
		MaxRetries:         3,
		TimeBetweenRetries: 5 * time.Second,
	}

	// Clean up resources after test
	defer terraform.Destroy(t, terraformOptions)

	// Deploy the infrastructure
	terraform.InitAndApply(t, terraformOptions)

	// Test CodeBuild project creation
	t.Run("CodeBuildProjectExists", func(t *testing.T) {
		projectName := terraform.Output(t, terraformOptions, "codebuild_project_name")
		require.NotEmpty(t, projectName)
		
		// Verify CodeBuild project exists
		project := aws.GetCodeBuildProject(t, awsRegion, projectName)
		assert.Equal(t, projectName, *project.Name)
		assert.Equal(t, "BUILD_GENERAL1_SMALL", *project.Environment.ComputeType)
		assert.Equal(t, "LINUX_CONTAINER", *project.Environment.Type)
	})

	// Test CodePipeline creation
	t.Run("CodePipelineExists", func(t *testing.T) {
		pipelineName := terraform.Output(t, terraformOptions, "codepipeline_name")
		require.NotEmpty(t, pipelineName)
		
		// Verify CodePipeline exists
		pipeline := aws.GetCodePipeline(t, awsRegion, pipelineName)
		assert.Equal(t, pipelineName, *pipeline.Name)
		assert.Len(t, pipeline.Stages, 2) // Source and Build stages
	})

	// Test artifacts bucket creation
	t.Run("ArtifactsBucketExists", func(t *testing.T) {
		bucketName := terraform.Output(t, terraformOptions, "artifacts_bucket_name")
		require.NotEmpty(t, bucketName)
		
		// Verify artifacts bucket exists
		aws.AssertS3BucketExists(t, awsRegion, bucketName)
	})

	// Test CloudWatch monitoring
	t.Run("CloudWatchMonitoring", func(t *testing.T) {
		logGroupName := terraform.Output(t, terraformOptions, "cloudwatch_log_group_name")
		alarm4xxName := terraform.Output(t, terraformOptions, "cloudwatch_4xx_alarm_name")
		alarm5xxName := terraform.Output(t, terraformOptions, "cloudwatch_5xx_alarm_name")
		
		assert.NotEmpty(t, logGroupName)
		assert.NotEmpty(t, alarm4xxName)
		assert.NotEmpty(t, alarm5xxName)
		
		// Verify log group exists
		logGroup := aws.GetCloudWatchLogGroup(t, awsRegion, logGroupName)
		assert.Equal(t, logGroupName, *logGroup.LogGroupName)
	})
}

// TestFrontendHostingModuleWithCustomDomain tests the frontend hosting module with custom domain
func TestFrontendHostingModuleWithCustomDomain(t *testing.T) {
	t.Parallel()

	// Generate a random suffix for unique resource names
	uniqueID := random.UniqueId()
	projectName := fmt.Sprintf("test-ai-cli-domain-%s", strings.ToLower(uniqueID))
	customDomain := fmt.Sprintf("test-%s.example.com", strings.ToLower(uniqueID))
	
	// AWS region for testing
	awsRegion := "us-east-1"
	
	// Terraform options
	terraformOptions := &terraform.Options{
		TerraformDir: "../modules/frontend-hosting",
		Vars: map[string]interface{}{
			"project_name":                     projectName,
			"environment":                      "test",
			"aws_region":                       awsRegion,
			"s3_force_destroy":                 true,
			"s3_versioning_enabled":            false,
			"enable_deployment_pipeline":       false,
			"enable_cloudwatch_monitoring":     false,
			"cloudfront_price_class":           "PriceClass_100",
			"domain_name":                      customDomain,
			"domain_aliases":                   []string{fmt.Sprintf("www.%s", customDomain)},
			"tags": map[string]string{
				"Environment": "test",
				"Project":     projectName,
				"ManagedBy":   "terratest",
			},
		},
		RetryableTerraformErrors: map[string]string{
			"RequestError: send request failed": "Temporary AWS API error",
		},
		MaxRetries:         3,
		TimeBetweenRetries: 5 * time.Second,
	}

	// Clean up resources after test
	defer terraform.Destroy(t, terraformOptions)

	// Deploy the infrastructure
	terraform.InitAndApply(t, terraformOptions)

	// Test custom domain configuration
	t.Run("CustomDomainConfiguration", func(t *testing.T) {
		distributionID := terraform.Output(t, terraformOptions, "cloudfront_distribution_id")
		customDomainURL := terraform.Output(t, terraformOptions, "custom_domain_url")
		domainAliases := terraform.OutputList(t, terraformOptions, "domain_aliases")
		
		require.NotEmpty(t, distributionID)
		assert.Equal(t, fmt.Sprintf("https://%s", customDomain), customDomainURL)
		assert.Contains(t, domainAliases, customDomain)
		assert.Contains(t, domainAliases, fmt.Sprintf("www.%s", customDomain))
		
		// Verify CloudFront distribution has the custom domain configured
		distribution := aws.GetCloudFrontDistribution(t, distributionID)
		assert.Contains(t, distribution.Aliases.Items, &customDomain)
	})
}