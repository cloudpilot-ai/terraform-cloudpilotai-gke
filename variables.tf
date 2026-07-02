################################################################################
# GKE Cluster - Required
################################################################################

variable "cluster_name" {
  description = "Name of the GKE cluster to be managed by CloudPilot AI."
  type        = string
}

variable "region" {
  description = "GCP region where the GKE cluster is located."
  type        = string
}

variable "project_id" {
  description = "Optional GCP project ID where the GKE cluster is located. When null, the provider first tries to infer it from discovered GKE metadata and then falls back to the active local gcloud project."
  type        = string
  default     = null
}

variable "cluster_uid" {
  description = "Optional Kubernetes cluster UID used by the provider to derive the CloudPilot cluster ID. For GKE, this matches the kube-system namespace UID. When null, the provider tries to read it from the target cluster through kubeconfig."
  type        = string
  default     = null
}

variable "cluster_id" {
  description = "Optional existing CloudPilot cluster ID. Useful for import/migration flows where the cluster is already registered."
  type        = string
  default     = null
}

################################################################################
# GKE Cluster - Optional Access / Behavior
################################################################################

variable "cluster_location" {
  description = "Optional GKE cluster location override for zonal clusters."
  type        = string
  default     = null
}

variable "kubeconfig" {
  description = "Optional kubeconfig path. When null, the provider generates one with gcloud during apply."
  type        = string
  default     = null
}

variable "disable_workload_uploading" {
  description = "Disable automatic uploading of workload information to CloudPilot AI."
  type        = bool
  default     = false
}

variable "only_install_agent" {
  description = "Only install the CloudPilot AI agent without additional GKE node autoscaler management. Leave as null to use the default full-management path."
  type        = bool
  default     = null
}

variable "enable_upgrade" {
  description = "Enable CloudPilot component upgrades when the provider reports the cluster needs upgrade."
  type        = bool
  default     = false
}

variable "cluster_setting" {
  description = <<-EOT
    Optional cluster-level setting object. When null, this module does not manage
    /api/v1/clusters/{cluster_id}/setting. Supported fields:
    - enable_node_repair
    - enable_disk_monitor
    - discount
    - pre_run_command
    - post_run_command
  EOT
  type        = any
  default     = null
}

################################################################################
# GKE Node Autoscaler / Cluster Optimization
################################################################################

variable "enable_node_autoscaler" {
  description = "Deprecated compatibility alias for the old two-resource module shape. When set to false, this maps to only_install_agent = true."
  type        = bool
  default     = null
}

variable "enable_rebalance" {
  description = "Enable CloudPilot node autoscaler / rebalance behavior for the cluster resource."
  type        = bool
  default     = false
}

variable "skip_restore" {
  description = "EKS-style alias for skipping restore during GKE Node Autoscaler destroy. When set, this takes precedence over node_autoscaler_skip_restore."
  type        = bool
  default     = null
}

variable "restore_node_number" {
  description = "EKS-style alias for restoring a uniform desired node count during GKE Node Autoscaler destroy. When set, this maps to GKE restore_desired_size and takes precedence over node_autoscaler_restore_desired_size."
  type        = number
  default     = null
}

variable "node_autoscaler_skip_restore" {
  description = "When true, skip restoring regular GKE node pools during GKE Node Autoscaler destroy. Takes precedence over the restore size inputs below."
  type        = bool
  default     = null
}

variable "node_autoscaler_restore_desired_size" {
  description = "Optional desired total node count to restore for each regular GKE node pool during GKE Node Autoscaler destroy. Leave as 0 to skip restore unless per-pool overrides are set."
  type        = number
  default     = null
}

variable "node_autoscaler_restore_desired_sizes" {
  description = "Deprecated compatibility alias for restore_desired_sizes."
  type        = map(number)
  default     = null
}

variable "restore_desired_sizes" {
  description = "Optional per-node-pool desired total node counts used during GKE cluster destroy. Keys are GKE node-pool names; values are desired total nodes for that pool."
  type        = map(number)
  default     = null
}

variable "nodeclasses" {
  description = <<-EOT
    List of GCE NodeClass objects managed by the GKE cluster resource.
    Each object supports the typed fields exposed by the provider, including:
    - name (Required)
    - template_name, enable_image_accelerator, service_account, disks, image_selector_terms, subnet_range_name,
      kubelet_configuration, labels, metadata, network_tags,
      confidential_instance_type, network_config, auto_gpu_taint,
      gpu_driver_version, origin_nodeclass_json (all Optional)
  EOT
  type        = any
  default     = []
}

variable "nodeclass_templates" {
  description = <<-EOT
    List of GKE NodeClass template objects for reuse across nodeclasses. Each object supports:
    - template_name (Required) - Template identifier
    - enable_image_accelerator, service_account, disks, image_selector_terms, subnet_range_name,
      kubelet_configuration, labels, metadata, network_tags,
      confidential_instance_type, network_config, auto_gpu_taint,
      gpu_driver_version, origin_nodeclass_json (all Optional)
  EOT
  type        = any
  default     = []
}

variable "nodepools" {
  description = <<-EOT
    List of GCE NodePool objects managed by the GKE cluster resource.
    Each object supports the typed fields exposed by the provider, including:
    - name (Required)
    - template_name, enable, enable_image_accelerator, nodeclass, enable_gpu, provision_priority,
      instance_family, instance_arch, capacity_type, zone,
      instance_cpu_min, instance_cpu_max, instance_memory_min,
      instance_memory_max, labels, taints, node_disruption_limit,
      node_disruption_delay, origin_nodepool_json (all Optional)
  EOT
  type        = any
  default     = []
}

variable "nodepool_templates" {
  description = <<-EOT
    List of GKE NodePool template objects for reuse across nodepools. Each object supports:
    - template_name (Required) - Template identifier
    - enable, enable_image_accelerator, nodeclass, enable_gpu, provision_priority,
      instance_family, instance_arch, capacity_type, zone,
      instance_cpu_min, instance_cpu_max, instance_memory_min,
      instance_memory_max, labels, taints, node_disruption_limit,
      node_disruption_delay, origin_nodepool_json (all Optional)
  EOT
  type        = any
  default     = []
}

################################################################################
# Workload Autoscaler - General
################################################################################

variable "enable_workload_autoscaler" {
  description = "Whether to deploy the shared CloudPilot Workload Autoscaler on this cluster."
  type        = bool
  default     = true
}

variable "wa_storage_class" {
  description = "StorageClass name for VictoriaMetrics persistent volume. If empty, the cluster default StorageClass is used."
  type        = string
  default     = ""
}

variable "wa_enable_node_agent" {
  description = "Whether to enable the Node Agent DaemonSet for per-node metrics collection."
  type        = bool
  default     = true
}

variable "wa_enable_new_workloads_proactive_update" {
  description = "Enable proactive update automatically for new workloads once recommendations are ready."
  type        = bool
  default     = false
}

variable "wa_limiter_quota_per_window" {
  description = "Workload Autoscaler limiter quota per window."
  type        = number
  default     = 5
}

variable "wa_limiter_burst" {
  description = "Workload Autoscaler limiter burst."
  type        = number
  default     = 10
}

variable "wa_limiter_window_seconds" {
  description = "Workload Autoscaler limiter window in seconds."
  type        = number
  default     = 30
}

variable "wa_enable_preempted_pod_gc" {
  description = "Enable garbage collection for preempted pods."
  type        = bool
  default     = true
}

variable "wa_preempted_pod_gc_ttl" {
  description = "TTL for preempted pod garbage collection, for example 30m."
  type        = string
  default     = "30m"
}

variable "wa_enable_initial_optimization_data_window_check" {
  description = "Require initial optimization data window before enabling update paths for new workloads."
  type        = bool
  default     = true
}

################################################################################
# Workload Autoscaler - Recommendation Policies
################################################################################

variable "recommendation_policies" {
  description = <<-EOT
    List of RecommendationPolicy objects. Each object supports:
    - name (Required)
    - history_window_cpu, history_window_memory, evaluation_period (Required)
    - strategy_type, percentile_cpu, percentile_memory, buffer_cpu, buffer_memory,
      request_min_cpu, request_min_memory, request_max_cpu, request_max_memory,
      jvm_heap_buffer, jvm_min_heap_xms_ratio_of_memory,
      jvm_recent_non_heap_window, jvm_heap_used_percentile (all Optional)
  EOT
  type        = any
  default     = []
}

################################################################################
# Workload Autoscaler - Autoscaling Policies
################################################################################

variable "autoscaling_policies" {
  description = <<-EOT
    List of AutoscalingPolicy objects. Each object supports:
    - name (Required)
    - recommendation_policy_name (Required)
    - enable, priority, target_refs, update_schedules, limit_policies,
      update_resources, drift_threshold_cpu, drift_threshold_memory,
      on_policy_removal, startup_boost_enabled, startup_boost_min_boost_duration,
      startup_boost_min_ready_duration, startup_boost_multiplier_cpu,
      startup_boost_multiplier_memory, disable_runtime_optimization,
      target_refs.label_selector, in_place_fallback_default_policy,
      in_place_fallback_reason_policies (all Optional)
  EOT
  type        = any
  default     = []
}

################################################################################
# Workload Autoscaler - Proactive Optimization
################################################################################

variable "enable_proactive" {
  description = <<-EOT
    List of workload filter objects to enable proactive optimization. Each object supports:
    - namespaces, workload_kinds, workload_name, workload_state,
      autoscaling_policy_names, optimization_states, disable_proactive_update,
      recommendation_policy_names, runtime_languages, optimized (all Optional)
  EOT
  type        = any
  default     = []
}

variable "disable_proactive" {
  description = <<-EOT
    List of workload filter objects to disable proactive optimization. Each object supports:
    - namespaces, workload_kinds, workload_name, workload_state,
      autoscaling_policy_names, optimization_states, disable_proactive_update,
      recommendation_policy_names, runtime_languages, optimized (all Optional)
  EOT
  type        = any
  default     = []
}
