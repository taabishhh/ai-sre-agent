variable "aws_region" {
  description = "AWS region to deploy the demo EKS cluster into."
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "Name of the demo EKS cluster."
  type        = string
  default     = "ai-sre-demo"
}

variable "cluster_version" {
  description = "Kubernetes version for the EKS control plane."
  type        = string
  default     = "1.30"
}

variable "vpc_cidr" {
  description = "CIDR block for the demo VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "node_instance_type" {
  description = "EC2 instance type for the worker node group. Keep small to control cost."
  type        = string
  default     = "t3.medium"
}

variable "node_desired_size" {
  description = "Desired number of worker nodes."
  type        = number
  default     = 2
}

variable "node_min_size" {
  type    = number
  default = 1
}

variable "node_max_size" {
  type    = number
  default = 3
}

variable "demo_namespace" {
  description = "Namespace the agent is allowed to act in and where the chaos demo deploys checkout-service."
  type        = string
  default     = "demo"
}

variable "github_repo" {
  description = "The GitHub repository allowed to deploy, as OWNER/REPO (for example taabish10s/quote-api-demo)."
  type        = string
}

variable "app_name" {
  description = "Name of the sample app. Also the name of its ECR repository."
  type        = string
  default     = "quote-api"
}

variable "create_github_oidc_provider" {
  description = "Create the GitHub OIDC identity provider. Set false if your AWS account already has one."
  type        = bool
  default     = true
}
