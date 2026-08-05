terraform {
  required_version = ">= 1.0"

  required_providers {
    cloudpilotai = {
      source  = "cloudpilot-ai/cloudpilotai"
      version = ">= 0.6.0"
    }
  }
}

provider "cloudpilotai" {
  api_endpoint = var.cloudpilotai_api_endpoint
  api_key      = var.cloudpilotai_api_key
}

module "cloudpilotai_gke" {
  source = "cloudpilot-ai/gke/cloudpilotai"

  cluster_name        = var.cluster_name
  region              = var.region
  project_id          = var.project_id
  cluster_uid         = var.cluster_uid
  cluster_location    = var.cluster_location
  kubeconfig          = var.kubeconfig
  skip_restore        = var.skip_restore
  restore_node_number = var.restore_node_number

  enable_upgrade             = true
  enable_rebalance           = true
  enable_workload_autoscaler = true

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
      capacity_type   = ["on-demand"]
      instance_arch   = ["amd64"]
      instance_family = ["e2", "n2", "n4"]
      labels = {
        codex-example = "complete"
        workload      = "cloudpilot-managed"
      }
    }
  ]

  recommendation_policies = [
    {
      name                  = "balanced"
      strategy_type         = "percentile"
      percentile_cpu        = 95
      percentile_memory     = 99
      history_window_cpu    = "24h"
      history_window_memory = "24h"
      evaluation_period     = "1h"
    }
  ]

  autoscaling_policies = [
    {
      name                       = "readonly"
      enable                     = false
      recommendation_policy_name = "balanced"
      priority                   = 0
      on_policy_removal          = "off"
      target_refs = [
        {
          api_version = "apps/v1"
          kind        = "Deployment"
          namespace   = "default"
        }
      ]
    }
  ]
}
