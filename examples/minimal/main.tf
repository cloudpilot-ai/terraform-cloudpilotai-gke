terraform {
  required_version = ">= 1.0"

  required_providers {
    cloudpilotai = {
      source  = "cloudpilot-ai/cloudpilotai"
      version = ">= 0.5.0"
    }
  }
}

provider "cloudpilotai" {
  api_endpoint = var.cloudpilotai_api_endpoint
  api_key      = var.cloudpilotai_api_key
}

module "cloudpilotai_gke" {
  source = "cloudpilot-ai/gke/cloudpilotai"

  cluster_name     = var.cluster_name
  region           = var.region
  project_id       = var.project_id
  cluster_uid      = var.cluster_uid
  cluster_location = var.cluster_location
  kubeconfig       = var.kubeconfig

  enable_upgrade   = true
  enable_rebalance = true

  cluster_setting = {
    enable_node_repair  = true
    enable_disk_monitor = true
    discount            = 0.15
  }

  nodeclasses = [
    {
      name = "cloudpilot"
    }
  ]

  nodepools = [
    {
      name            = "cloudpilot-general"
      enable          = true
      nodeclass       = "cloudpilot"
      capacity_type   = ["spot", "on-demand"]
      instance_arch   = ["amd64"]
      instance_family = ["n4", "n2", "e2"]
    }
  ]
}
