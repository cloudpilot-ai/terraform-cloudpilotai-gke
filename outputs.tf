output "cluster_id" {
  description = "CloudPilot unique identifier for the managed GKE cluster."
  value       = cloudpilotai_gke_cluster.this.cluster_id
}

output "cluster_name" {
  description = "Name of the GKE cluster."
  value       = cloudpilotai_gke_cluster.this.cluster_name
}

output "region" {
  description = "GCP region where the GKE cluster is located."
  value       = cloudpilotai_gke_cluster.this.region
}

output "project_id" {
  description = "GCP project ID where the cluster is located."
  value       = cloudpilotai_gke_cluster.this.project_id
}

output "cluster_uid" {
  description = "Native GKE cluster UID used to derive the CloudPilot cluster ID."
  value       = cloudpilotai_gke_cluster.this.cluster_uid
}

output "kubeconfig" {
  description = "Explicitly configured GKE kubeconfig path, or null when the provider generates execution-local kubeconfigs."
  value       = cloudpilotai_gke_cluster.this.kubeconfig
}

output "node_autoscaler_enabled" {
  description = "Whether the GKE cluster resource is managing the CloudPilot node autoscaler path instead of agent-only mode."
  value       = local.effective_only_install_agent == true ? false : true
}

output "enable_rebalance" {
  description = "Whether rebalance is enabled for the GKE cluster resource."
  value       = cloudpilotai_gke_cluster.this.enable_rebalance
}

output "agent_version" {
  description = "Version of the CloudPilot AI agent currently installed on the cluster."
  value       = cloudpilotai_gke_cluster.this.agent_version
}

output "onboard_manifest_version" {
  description = "Latest CloudPilot onboard manifest version reported by the service."
  value       = cloudpilotai_gke_cluster.this.onboard_manifest_version
}

output "need_upgrade" {
  description = "Whether CloudPilot currently reports that this cluster needs an upgrade."
  value       = cloudpilotai_gke_cluster.this.need_upgrade
}

output "workload_autoscaler_enabled" {
  description = "Whether the shared Workload Autoscaler resource was created."
  value       = var.enable_workload_autoscaler
}
