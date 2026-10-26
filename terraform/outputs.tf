output "cluster_name" {
  value = module.eks.cluster_name
}

output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "region" {
  value = var.aws_region
}

output "configure_kubectl" {
  description = "Run this to point kubectl/Helm/the AI SRE agent at the new cluster."
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}

output "ecr_repository_url" {
  value = aws_ecr_repository.app.repository_url
}

output "github_actions_role_arn" {
  value = aws_iam_role.github_ci.arn
}

output "github_actions_config" {
  description = "Paste these four into GitHub: repo Settings, Secrets and variables, Actions, Variables."
  value       = <<-EOT
    AWS_REGION      = ${var.aws_region}
    AWS_ROLE_ARN    = ${aws_iam_role.github_ci.arn}
    EKS_CLUSTER_NAME = ${module.eks.cluster_name}
    ECR_REPOSITORY  = ${var.app_name}
  EOT
}
