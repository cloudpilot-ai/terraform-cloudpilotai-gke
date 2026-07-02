# Complete Example

This example demonstrates a full GKE CloudPilot deployment that installs both:

- the GKE node autoscaler through `cloudpilotai_gke_cluster`
- the shared Workload Autoscaler

It is intended for real-cluster validation, including destroy with restore back to the original GKE nodepool size.

## What This Example Does

- installs `cloudpilotai_gke_cluster`
- installs `cloudpilotai_workload_autoscaler`
- creates one recommendation policy and one disabled autoscaling policy for Workload Autoscaler CRUD validation
- configures one GKE nodepool template with a custom node label:

  - `workload=cloudpilot-managed`

- includes [trigger-managed-node.yaml](trigger-managed-node.yaml), a helper manifest that can be applied after Terraform install to force CloudPilot to provision at least one managed node

## Inputs

Required:

- `cloudpilotai_api_key`
- `cluster_name`
- `region`

Recommended for this example:

- `restore_node_number = 2`

Optional:

- `cloudpilotai_api_endpoint`
- `project_id`
- `cluster_uid`
- `cluster_location`
- `kubeconfig`
- `skip_restore`

## Usage

1. Enter the example directory:

   ```bash
   cd examples/complete
   ```

2. Copy the example tfvars file:

   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

3. Edit `terraform.tfvars` with your cluster values.

4. Initialize and apply:

   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

5. After install, apply the helper manifest to trigger a CloudPilot-managed node:

   ```bash
   kubectl apply -f trigger-managed-node.yaml
   ```

6. When you are ready to validate restore-on-destroy, run:

   ```bash
   terraform destroy
   ```

With `restore_node_number = 2`, destroy should restore the regular GKE nodepool back to a total of 2 ready nodes before CloudPilot is fully removed.
