# Terraform — demo EKS cluster

Creates a small EKS cluster for the agent: a VPC (2 AZs, one NAT gateway),
the EKS control plane, 2 t3.medium nodes and a `demo` namespace. It also creates
an ECR repo and a GitHub Actions role for the CI/CD demo.

## Cost warning

This is **not free**. Rough cost while it's running:
- EKS control plane: ~$0.10/hour (~$2.40/day)
- 2x t3.medium on-demand: ~$0.08/hour combined (~$2/day)
- 1x NAT gateway: ~$0.045/hour + data (~$1.10/day)

**Total: roughly $5/day.** Run `terraform destroy` as soon as you're done
with your demo/recording.

## Prerequisites

- AWS account with an IAM identity that can create VPCs, EKS clusters, IAM
  roles, and EC2 node groups (AdministratorAccess is simplest for a demo).
- AWS CLI v2 configured (`aws configure` or `aws sso login`).
- Terraform >= 1.5.
- `kubectl` and `helm` installed locally.

## Usage

```bash
cd terraform
terraform init
terraform plan
terraform apply -var="github_repo=YOUR-USERNAME/quote-api-demo"   # ~12-15 min

# point kubectl at the new cluster
$(terraform output -raw configure_kubectl)

kubectl get nodes         # should show 2 Ready nodes after a minute or two
```

Then install the telemetry layer and the chaos demo:

```bash
../k8s-manifests/install-prometheus.sh
../demo/inject_chaos.sh
```

And point the agent at it:

```bash
cd ..
export MOCK_MODE=false
export DEFAULT_NAMESPACE=demo
export ALLOWED_NAMESPACES=demo
python scripts/run_agent.py --namespace demo
```

## Tear down

```bash
cd terraform
terraform destroy -var="github_repo=YOUR-USERNAME/quote-api-demo"
```

Check the AWS console (EC2, VPC, EKS) afterwards to make sure nothing is left running.

## Customizing

All the knobs (region, cluster name, node size/count, Kubernetes version) are
in `variables.tf`. Override with a `terraform.tfvars` file or `-var` flags,
e.g.:

```bash
terraform apply -var="node_instance_type=t3.small" -var="node_desired_size=1"
```
