#!/usr/bin/env python3

import pathlib
import sys
import tempfile
import unittest

import generated_to_module


class GeneratedToModuleTest(unittest.TestCase):
    def test_build_module_file_with_cluster_managed_node_autoscaler_and_wa(self) -> None:
        cluster_body = """
  cluster_id = "cluster-1"
  cluster_name = "demo-gke"
  region = "us-central1"
  only_install_agent = null
  enable_rebalance = true
  cluster_setting = {
    enable_node_repair = true
    post_run_command = null
  }
  disable_workload_uploading = false
  enable_upgrade = true
  scheduled_rebalances = [
    {
      name = "nightly"
      cron = "0 3 * * *"
    }
  ]
  nodeclasses = []
  nodepools = []
"""
        wa_body = """
  cluster_id = "cluster-1"
  kubeconfig = "/tmp/kubeconfig"
  aws_assume_role = null
  aws_profile = null
  gcp_cluster_location = null
  gcp_project_id = null
  storage_class = "standard-rwo"
  enable_node_agent = true
  recommendation_policies = []
"""

        out = generated_to_module.build_module_file(
            cluster_body,
            wa_body,
            "cloudpilot-ai/gke/cloudpilotai",
        )

        self.assertIn('module "cloudpilotai_gke" {', out)
        self.assertIn("cluster_id = var.cluster_id", out)
        self.assertIn('cluster_name = "demo-gke"', out)
        self.assertIn('region = "us-central1"', out)
        self.assertIn('# project_id = "my-gcp-project"', out)
        self.assertIn("post_run_command = null", out)
        self.assertIn("only_install_agent = null", out)
        self.assertIn("enable_rebalance = true", out)
        self.assertIn("scheduled_rebalances = [", out)
        self.assertIn('name = "nightly"', out)
        self.assertIn("nodeclasses = []", out)
        self.assertIn("enable_workload_autoscaler = true", out)
        self.assertIn("wa_storage_class = \"standard-rwo\"", out)
        for provider_only_field in (
            "aws_assume_role",
            "aws_profile",
            "gcp_cluster_location",
            "gcp_project_id",
            "kubeconfig",
        ):
            self.assertNotRegex(out, rf"(?m)^  {provider_only_field}\s*=")

    def test_build_import_script_omits_optional_resources_when_absent(self) -> None:
        out = generated_to_module.build_import_script("cluster-1", False)
        self.assertIn("cloudpilotai_gke_cluster.this", out)
        self.assertIn('terraform_cli="${TERRAFORM_CLI:-terraform}"', out)
        self.assertIn('"$terraform_cli" import', out)
        self.assertNotIn("cloudpilotai_gke_node_autoscaler", out)
        self.assertNotIn("cloudpilotai_workload_autoscaler", out)

    def test_released_fields_and_null_values_survive_conversion(self) -> None:
        cluster_body = """
  cluster_name = "example-gke"
  region = "us-central1"
  cluster_setting = {
    disruption_cooldown = "5m"
    enable_node_repair = false
    pre_run_command = null
    post_run_command = null
    maintenance_enabled = true
    saving_report_baseline_start_at = "2026-01-01T00:00:00Z"
    saving_report_baseline_end_at = "2026-01-02T00:00:00Z"
  }
  workloads = [{
    name = "example-api"
    type = "deployment"
    namespace = "default"
    rebalance_able = false
    spot_friendly = null
    min_non_spot_replicas = 0
  }]
  nodeclasses = [{
    name = "example-class"
    ephemeral_storage_local_ssd = { auto_count = true, count = null }
    disks = [{ boot = true, size_gib = 80, size_policy = { per_vcpu_gib = 0, max_size_gib = 512 } }]
  }]
  nodepools = [{
    name = "example-pool"
    disruption_cooldown = "0s"
    job_nodepool_optimization = { min_active_nodes = null, provisioning_delay = "30s" }
  }]
"""
        wa_body = """
  storage_class = null
  enable_node_agent = null
  recommendation_policies = [{
    name = "example-policy"
    jvm_max_heap_xms = null
    jvm_min_heap_xmx = "256Mi"
    jvm_max_heap_xmx = "4Gi"
  }]
"""
        out = generated_to_module.build_module_file(cluster_body, wa_body, "../..")
        for expected in (
            'disruption_cooldown = "5m"',
            "enable_node_repair = false",
            "pre_run_command = null",
            "post_run_command = null",
            "workloads = [{",
            "rebalance_able = false",
            "spot_friendly = null",
            "min_non_spot_replicas = 0",
            "auto_count = true, count = null",
            "per_vcpu_gib = 0, max_size_gib = 512",
            "min_active_nodes = null",
            "wa_storage_class = null",
            "wa_enable_node_agent = null",
            "jvm_max_heap_xms = null",
            'jvm_min_heap_xmx = "256Mi"',
            'jvm_max_heap_xmx = "4Gi"',
        ):
            self.assertIn(expected, out)
        for excluded in (
            "maintenance_enabled",
            "saving_report_baseline_start_at",
            "saving_report_baseline_end_at",
        ):
            self.assertNotIn(excluded, out)

    def test_null_workloads_remain_unmanaged(self) -> None:
        out = generated_to_module.build_module_file("  workloads = null\n", None, "../..")
        self.assertIn("workloads = null", out)

    def test_unreleased_memory_settings_are_excluded(self) -> None:
        cluster_body = """
  cluster_setting = {
    memory_request_multiplier = 1.5
    zero_memory_request_mib = 128
    discount = 0
  }
"""
        out = generated_to_module.build_module_file(cluster_body, None, "../..")
        self.assertNotIn("memory_request_multiplier", out)
        self.assertNotIn("zero_memory_request_mib", out)
        self.assertIn("discount = 0", out)

    def test_main_writes_expected_files(self) -> None:
        generated_tf = """
# __generated__ by Terraform from "cluster-1"
resource "cloudpilotai_gke_cluster" "imported" {
  cluster_id = "cluster-1"
  cluster_name = "demo-gke"
  region = "us-central1"
  enable_rebalance = false
}
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = pathlib.Path(tmpdir)
            input_path = tmp / "generated.tf"
            output_path = tmp / "module.generated.tf"
            import_path = tmp / "import-module.sh"
            input_path.write_text(generated_tf)

            old_argv = sys.argv
            try:
                sys.argv = [
                    "generated_to_module.py",
                    "--input",
                    str(input_path),
                    "--output",
                    str(output_path),
                    "--import-script",
                    str(import_path),
                ]
                result = generated_to_module.main()
            finally:
                sys.argv = old_argv

            self.assertEqual(result, 0)
            self.assertTrue(output_path.exists())
            self.assertTrue(import_path.exists())
            self.assertIn("enable_rebalance = false", output_path.read_text())


if __name__ == "__main__":
    unittest.main()
