# Minimal GKE Module Example

This example uses the published `cloudpilot-ai/gke/cloudpilotai` module to install and manage CloudPilot on a real GKE cluster.

It creates:

- `cloudpilotai_gke_cluster`
- shared `cloudpilotai_workload_autoscaler`

## What You Need

- Terraform
- `gcloud`
- `kubectl`
- a CloudPilot API key
- a GKE cluster that your local `gcloud` credential can access

For the minimal path, the only required inputs are:

- `cloudpilotai_api_key`
- `cluster_name`
- `region`

These are optional:

- `cloudpilotai_api_endpoint`
- `project_id`
- `cluster_uid`
- `cluster_location`
- `kubeconfig`

If your local `gcloud` project is already set correctly and the generated kubeconfig can access the cluster, the provider can usually infer both `project_id` and `cluster_uid` automatically.

## Step 1: Enter The Example Directory

```bash
cd examples/minimal
```

## Step 2: Copy The Example tfvars File

Create your working `terraform.tfvars` from the checked-in example:

```bash
cp terraform.tfvars.example terraform.tfvars
```

After copying, edit `terraform.tfvars`.

## Step 3: Fill In `terraform.tfvars`

Start with the required fields:

```hcl
cloudpilotai_api_key = "cp_..."
cluster_name         = "my-gke-cluster"
region               = "us-central1"
```

You can usually leave these commented or unset at first:

```hcl
# project_id    = "my-gcp-project"
# cluster_uid   = "kube-system-namespace-uid"
cluster_location = "us-central1"
kubeconfig       = null
```

A few notes:

- `cloudpilotai_api_endpoint` should usually stay as `https://api.cloudpilot.ai`
- `cluster_location` is optional, but it is still a good idea to set it explicitly if your cluster is zonal or if auto-detection may be ambiguous
- `kubeconfig = null` is the normal path; the provider will generate and use a local kubeconfig when needed
- set `project_id` explicitly if your active local `gcloud` project is not the target cluster's project
- set `cluster_uid` explicitly only if local discovery is not enough

If you want to pin `cluster_uid`, get it from `kube-system`:

```bash
kubectl get ns kube-system -o jsonpath='{.metadata.uid}'
```

## Step 4: Make Sure Local GCP Access Is Ready

Before running Terraform, it is worth checking that your local shell can already talk to the target cluster:

```bash
gcloud config get-value project
gcloud container clusters get-credentials <cluster-name> --location <region-or-location>
kubectl get nodes
```

If the first command prints the wrong project, either switch it:

```bash
gcloud config set project <project-id>
```

or set `project_id` explicitly in `terraform.tfvars`.

## Step 5: Initialize Terraform

```bash
terraform init
```

If you are using a local provider dev override, Terraform may print a warning about development overrides. That warning is expected.

## Step 6: Review The Plan

```bash
terraform plan
```

This example points the module `source` at the published registry module:

```hcl
source = "cloudpilot-ai/gke/cloudpilotai"
```

## Step 7: Apply

```bash
terraform apply
```

On a fresh install, the provider may:

- generate a local kubeconfig
- infer `project_id` from local `gcloud` context
- infer `cluster_uid` from the cluster after kubeconfig is available

## Step 8: Destroy

```bash
terraform destroy
```

By default, the GKE cluster destroy path does not enter an interactive restore flow. If you later want restore behavior before destroy, configure the module-level restore controls instead of expecting manual terminal input during Terraform execution.

## Example `terraform.tfvars`

```hcl
cloudpilotai_api_endpoint = "https://api.cloudpilot.ai"
cloudpilotai_api_key      = "cp_..."

cluster_name     = "my-gke-cluster"
region           = "us-central1"
cluster_location = "us-central1"
kubeconfig       = null

# Optional only when local discovery is not enough:
# project_id = "my-gcp-project"
# cluster_uid = "kube-system-namespace-uid"
```
