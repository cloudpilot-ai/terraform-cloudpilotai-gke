# Bootstrap import blocks used only for configuration discovery.
#
# Phase 1:
#   terraform plan -generate-config-out=generated.tf
#
# Phase 2:
#   Run scripts/generated_to_module.py, then delete this file and generated.tf.
#   After that, import directly into module.cloudpilotai_gke.* addresses.

import {
  to = cloudpilotai_gke_cluster.imported
  id = var.cluster_id
}

# Keep this second import block if the existing cluster already has the
# Workload Autoscaler installed. If the cluster does not have it, comment out
# this block before running terraform plan -generate-config-out=generated.tf.
import {
  to = cloudpilotai_workload_autoscaler.imported
  id = var.cluster_id
}
