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
        self.assertIn('post_run_command = ""', out)
        self.assertIn("only_install_agent = null", out)
        self.assertIn("enable_rebalance = true", out)
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
