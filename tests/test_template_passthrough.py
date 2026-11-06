import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest


MODULE_ROOT = pathlib.Path(__file__).resolve().parents[1]


class TemplatePassthroughTest(unittest.TestCase):
    def available_clis(self):
        available = [cli for cli in ("terraform", "tofu") if shutil.which(cli)]
        if not available:
            self.skipTest("Terraform or OpenTofu is required for template evaluation")
        return available

    def render(self, cli, variables):
        with tempfile.TemporaryDirectory(prefix="cloudpilot-gke-locals-") as directory:
            root = pathlib.Path(directory)
            for filename in ("variables.tf", "locals.tf"):
                shutil.copyfile(MODULE_ROOT / filename, root / filename)
            values = {"cluster_name": "illustrative-gke", "region": "us-central1", **variables}
            (root / "inputs.tfvars.json").write_text(json.dumps(values))
            result = subprocess.run(
                [cli, "console", "-no-color", "-var-file=inputs.tfvars.json"],
                input="jsonencode({nodeclasses=local.rendered_nodeclasses,nodepools=local.rendered_nodepools,workloads=var.workloads})\n",
                cwd=root, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(result.stdout.strip(), result.stderr)
            return json.loads(json.loads(result.stdout.strip()))

    def test_explicit_null_overrides_template_fields(self):
        for cli in self.available_clis():
            with self.subTest(cli=cli):
                result = self.render(cli, {
                    "nodeclass_templates": [{"template_name": "base", "enable_image_accelerator": True, "ephemeral_storage_local_ssd": {"auto_count": True}}],
                    "nodeclasses": [{"name": "illustrative-class", "template_name": "base", "enable_image_accelerator": None, "ephemeral_storage_local_ssd": None}],
                    "nodepool_templates": [{"template_name": "base", "disruption_cooldown": "5m", "job_nodepool_optimization": {"min_active_nodes": 2}}],
                    "nodepools": [{"name": "illustrative-pool", "template_name": "base", "disruption_cooldown": None, "job_nodepool_optimization": None}],
                    "workloads": None,
                })
                self.assertIsNone(result["nodeclasses"][0]["enable_image_accelerator"])
                self.assertIsNone(result["nodeclasses"][0]["ephemeral_storage_local_ssd"])
                self.assertIsNone(result["nodepools"][0]["disruption_cooldown"])
                self.assertIsNone(result["nodepools"][0]["job_nodepool_optimization"])

    def test_released_fields_inherit_without_losing_null_false_or_zero(self):
        disks = [{"boot": True, "size_gib": 80, "size_policy": {"per_vcpu_gib": 0, "max_size_gib": 512}}]
        local_ssd = {"auto_count": True, "count": None}
        job_policy = {"min_active_nodes": None, "provisioning_delay": "30s"}
        workloads = [{"name": "illustrative-app", "type": "deployment", "namespace": "default", "rebalance_able": False, "spot_friendly": None, "min_non_spot_replicas": 0}]
        for cli in self.available_clis():
            with self.subTest(cli=cli):
                result = self.render(cli, {
                    "nodeclass_templates": [{"template_name": "base", "disks": disks, "ephemeral_storage_local_ssd": local_ssd}],
                    "nodeclasses": [{"name": "illustrative-class", "template_name": "base"}],
                    "nodepool_templates": [{"template_name": "base", "disruption_cooldown": "0s", "job_nodepool_optimization": job_policy}],
                    "nodepools": [{"name": "illustrative-pool", "template_name": "base", "enable": False}],
                    "workloads": workloads,
                })
                self.assertEqual(result["nodeclasses"][0]["disks"], disks)
                self.assertEqual(result["nodeclasses"][0]["ephemeral_storage_local_ssd"], local_ssd)
                self.assertEqual(result["nodepools"][0]["job_nodepool_optimization"], job_policy)
                self.assertEqual(result["nodepools"][0]["disruption_cooldown"], "0s")
                self.assertIs(result["nodepools"][0]["enable"], False)
                self.assertEqual(result["workloads"], workloads)

    def test_explicit_empty_policies_override_template_fields(self):
        template_disks = [{
            "boot": True, "size_gib": 80,
            "size_policy": {"per_vcpu_gib": 4, "max_size_gib": 512},
        }]
        reset_disks = [{"boot": True, "size_policy": {}}]
        for cli in self.available_clis():
            with self.subTest(cli=cli):
                result = self.render(cli, {
                    "nodeclass_templates": [{
                        "template_name": "base", "ephemeral_storage_local_ssd": {"auto_count": True},
                        "disks": template_disks,
                    }],
                    "nodeclasses": [{
                        "name": "illustrative-class", "template_name": "base",
                        "ephemeral_storage_local_ssd": {}, "disks": reset_disks,
                    }],
                    "nodepool_templates": [{
                        "template_name": "base", "disruption_cooldown": "5m",
                        "job_nodepool_optimization": {"min_active_nodes": 2},
                    }],
                    "nodepools": [{
                        "name": "illustrative-pool", "template_name": "base",
                        "disruption_cooldown": "", "job_nodepool_optimization": {},
                    }],
                })
                self.assertEqual(result["nodeclasses"][0]["ephemeral_storage_local_ssd"], {})
                self.assertEqual(result["nodeclasses"][0]["disks"], reset_disks)
                self.assertEqual(result["nodepools"][0]["job_nodepool_optimization"], {})
                self.assertEqual(result["nodepools"][0]["disruption_cooldown"], "")

    def test_heterogeneous_templates_preserve_optional_fields(self):
        disks = [{"boot": True, "size_gib": 80, "size_policy": {"max_size_gib": 512}}]
        local_ssd = {"auto_count": True}
        job = {"min_active_nodes": 2}
        for cli in self.available_clis():
            with self.subTest(cli=cli):
                result = self.render(cli, {
                    "nodeclass_templates": [
                        {"template_name": "disk", "disks": disks},
                        {"template_name": "ssd", "ephemeral_storage_local_ssd": local_ssd},
                    ],
                    "nodeclasses": [
                        {"name": "disk-class", "template_name": "disk"},
                        {"name": "ssd-class", "template_name": "ssd"},
                    ],
                    "nodepool_templates": [
                        {"template_name": "cooldown", "disruption_cooldown": "5m"},
                        {"template_name": "job", "job_nodepool_optimization": job},
                    ],
                    "nodepools": [
                        {"name": "cooldown-pool", "template_name": "cooldown"},
                        {"name": "job-pool", "template_name": "job"},
                    ],
                })
                self.assertEqual(result["nodeclasses"], [
                    {"name": "disk-class", "disks": disks},
                    {"name": "ssd-class", "ephemeral_storage_local_ssd": local_ssd},
                ])
                self.assertEqual(result["nodepools"], [
                    {"name": "cooldown-pool", "disruption_cooldown": "5m"},
                    {"name": "job-pool", "job_nodepool_optimization": job},
                ])

    def test_null_templates_leave_concrete_objects_unchanged(self):
        nodeclass = {"name": "plain-class", "enable_image_accelerator": False}
        nodepool = {"name": "plain-pool", "disruption_cooldown": None}
        for cli in self.available_clis():
            with self.subTest(cli=cli):
                result = self.render(cli, {
                    "nodeclass_templates": None, "nodeclasses": [nodeclass],
                    "nodepool_templates": None, "nodepools": [nodepool],
                })
                self.assertEqual(result["nodeclasses"], [nodeclass])
                self.assertEqual(result["nodepools"], [nodepool])

    def test_null_lists_remain_null(self):
        for cli in self.available_clis():
            with self.subTest(cli=cli):
                result = self.render(cli, {"nodeclasses": None, "nodepools": None, "workloads": None})
                self.assertEqual(result, {"nodeclasses": None, "nodepools": None, "workloads": None})


if __name__ == "__main__":
    unittest.main()
