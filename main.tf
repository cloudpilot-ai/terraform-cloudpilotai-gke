resource "cloudpilotai_gke_cluster" "this" {
  cluster_id       = var.cluster_id
  cluster_name     = var.cluster_name
  region           = var.region
  project_id       = var.project_id
  cluster_uid      = var.cluster_uid
  cluster_location = var.cluster_location
  kubeconfig       = var.kubeconfig

  disable_workload_uploading = var.disable_workload_uploading
  only_install_agent         = local.effective_only_install_agent
  enable_upgrade             = var.enable_upgrade
  enable_rebalance           = var.enable_rebalance
  skip_restore               = local.effective_skip_restore
  restore_node_number        = local.effective_restore_desired_size
  restore_desired_sizes      = local.effective_restore_desired_sizes

  cluster_setting = var.cluster_setting
  nodeclasses     = local.rendered_nodeclasses
  nodepools       = local.rendered_nodepools
}

resource "cloudpilotai_workload_autoscaler" "this" {
  count = var.enable_workload_autoscaler ? 1 : 0

  cluster_id = cloudpilotai_gke_cluster.this.cluster_id
  kubeconfig = cloudpilotai_gke_cluster.this.kubeconfig

  storage_class     = var.wa_storage_class
  enable_node_agent = var.wa_enable_node_agent

  enable_new_workloads_proactive_update         = var.wa_enable_new_workloads_proactive_update
  limiter_quota_per_window                      = var.wa_limiter_quota_per_window
  limiter_burst                                 = var.wa_limiter_burst
  limiter_window_seconds                        = var.wa_limiter_window_seconds
  enable_preempted_pod_gc                       = var.wa_enable_preempted_pod_gc
  preempted_pod_gc_ttl                          = var.wa_preempted_pod_gc_ttl
  enable_initial_optimization_data_window_check = var.wa_enable_initial_optimization_data_window_check

  recommendation_policies = var.recommendation_policies
  autoscaling_policies    = var.autoscaling_policies
  enable_proactive        = var.enable_proactive
  disable_proactive       = var.disable_proactive
}
