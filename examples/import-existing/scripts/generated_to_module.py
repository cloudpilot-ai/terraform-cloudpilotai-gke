#!/usr/bin/env python3

import argparse
import pathlib
import re
import stat
import sys


RESOURCE_HEADER_RE = re.compile(r'^resource\s+"([^"]+)"\s+"([^"]+)"\s+\{$', re.MULTILINE)
RESOURCE_WITH_ID_RE = re.compile(
    r'# __generated__ by (?:Terraform|OpenTofu) from "([^"]+)"\s+resource\s+"([^"]+)"\s+"([^"]+)"\s+\{',
    re.MULTILINE,
)
TOP_LEVEL_ATTR_RE = re.compile(r"^  ([a-zA-Z0-9_]+)\s+=\s+(.*)$")
WA_PROVIDER_ONLY_FIELDS = frozenset(
    {
        "aws_assume_role",
        "aws_profile",
        "gcp_cluster_location",
        "gcp_project_id",
        "kubeconfig",
    }
)


def extract_resource_block(text: str, resource_type: str) -> str | None:
    for match in RESOURCE_HEADER_RE.finditer(text):
        if match.group(1) != resource_type:
            continue
        start = match.end()
        depth = 1
        i = start
        while i < len(text):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i]
            i += 1
        raise ValueError(f"unterminated resource block for {resource_type}")
    return None


def split_top_level_chunks(body: str) -> list[tuple[str | None, str]]:
    chunks: list[tuple[str | None, str]] = []
    current_key: str | None = None
    current_lines: list[str] = []

    for line in body.splitlines(keepends=True):
        match = TOP_LEVEL_ATTR_RE.match(line)
        if match:
            if current_lines:
                chunks.append((current_key, "".join(current_lines)))
            current_key = match.group(1)
            current_lines = [line]
        else:
            if not current_lines and line.strip() == "":
                continue
            current_lines.append(line)

    if current_lines:
        chunks.append((current_key, "".join(current_lines)))

    return chunks


def rewrite_top_level_scalar(key: str, value: str) -> str:
    return f"  {key} = {value}\n"


def top_level_value(chunk: str) -> str | None:
    first_line = chunk.splitlines()[0]
    match = TOP_LEVEL_ATTR_RE.match(first_line)
    if not match:
        return None
    return match.group(2).strip()


def has_top_level_key(body: str, key: str) -> bool:
    return any(chunk_key == key for chunk_key, _ in split_top_level_chunks(body))


def transform_cluster_setting_chunk(chunk: str) -> str:
    return re.sub(
        r"^(\s+(?:pre_run_command|post_run_command)\s+=\s+)null$",
        r'\1""',
        chunk,
        flags=re.MULTILINE,
    )


def extract_chunk(body: str, key: str) -> str | None:
    for chunk_key, chunk in split_top_level_chunks(body):
        if chunk_key == key:
            return chunk
    return None


def extract_import_id(text: str, resource_type: str) -> str:
    for match in RESOURCE_WITH_ID_RE.finditer(text):
        import_id, matched_type, _ = match.groups()
        if matched_type == resource_type:
            return import_id
    raise ValueError(f'import ID not found for resource type "{resource_type}"')


def build_module_file(
    cluster_body: str,
    wa_body: str | None,
    source: str,
) -> str:
    lines = [
        "# Generated from generated.tf by scripts/generated_to_module.py.\n",
        "# Review this file before committing it.\n",
        "# Manual validation is still required before future cluster-side CRUD flows.\n",
        "# The provider now tries to auto-discover GKE kubeconfig for import-driven delete/upgrade flows,\n",
        "# so keep the config minimal first and only add project_id, cluster_uid, cluster_location,\n",
        "# or kubeconfig explicitly if your local gcloud context cannot infer them.\n",
        "\n",
        "module \"cloudpilotai_gke\" {\n",
        f"  source = \"{source}\"\n",
        "\n",
        rewrite_top_level_scalar("cluster_id", "var.cluster_id"),
    ]

    for key in ("cluster_name", "region"):
        chunk = extract_chunk(cluster_body, key)
        if chunk is not None:
            lines.append(chunk)

    lines.extend([
        "  # Optional manual follow-up only if GKE auto-discovery is insufficient:\n",
        "  # project_id = \"my-gcp-project\"\n",
        "  # cluster_uid = \"kube-system-namespace-uid\"\n",
        "  # cluster_location = \"us-central1-b\"\n",
        "  # kubeconfig = \"/absolute/path/to/kubeconfig\"\n",
    ])

    for key in (
        "only_install_agent",
        "enable_rebalance",
        "disable_workload_uploading",
        "enable_upgrade",
        "skip_restore",
        "restore_node_number",
        "restore_desired_sizes",
        "cluster_setting",
        "nodeclasses",
        "nodepools",
    ):
        chunk = extract_chunk(cluster_body, key)
        if chunk is None:
            if key in (
                "only_install_agent",
                "enable_rebalance",
                "disable_workload_uploading",
                "enable_upgrade",
                "skip_restore",
                "restore_node_number",
                "restore_desired_sizes",
            ):
                lines.append(rewrite_top_level_scalar(key, "null"))
            continue
        if key == "cluster_setting" and top_level_value(chunk) == "null":
            continue
        if key == "cluster_setting":
            chunk = transform_cluster_setting_chunk(chunk)
        lines.append(chunk)

    lines.append("\n")
    if wa_body is None:
        lines.append(rewrite_top_level_scalar("enable_workload_autoscaler", "false"))
    else:
        lines.append(rewrite_top_level_scalar("enable_workload_autoscaler", "true"))
        key_map = {
            "storage_class": "wa_storage_class",
            "enable_node_agent": "wa_enable_node_agent",
            "enable_new_workloads_proactive_update": "wa_enable_new_workloads_proactive_update",
            "limiter_quota_per_window": "wa_limiter_quota_per_window",
            "limiter_burst": "wa_limiter_burst",
            "limiter_window_seconds": "wa_limiter_window_seconds",
            "enable_preempted_pod_gc": "wa_enable_preempted_pod_gc",
            "preempted_pod_gc_ttl": "wa_preempted_pod_gc_ttl",
            "enable_initial_optimization_data_window_check": "wa_enable_initial_optimization_data_window_check",
        }
        for key, chunk in split_top_level_chunks(wa_body):
            if key is None or key == "cluster_id" or key in WA_PROVIDER_ONLY_FIELDS:
                continue
            if key in key_map:
                value = TOP_LEVEL_ATTR_RE.match(chunk.splitlines()[0]).group(2).strip()
                lines.append(rewrite_top_level_scalar(key_map[key], value))
                continue
            lines.append(chunk)

    lines.append("}\n")
    return "".join(lines)


def build_import_script(cluster_id: str, include_wa: bool) -> str:
    lines = [
        "#!/usr/bin/env bash\n",
        "set -euo pipefail\n",
        "\n",
        'terraform_cli="${TERRAFORM_CLI:-terraform}"\n',
        "\n",
        f'"$terraform_cli" import \'module.cloudpilotai_gke.cloudpilotai_gke_cluster.this\' \'{cluster_id}\'\n',
    ]
    if include_wa:
        lines.append(
            f'"$terraform_cli" import \'module.cloudpilotai_gke.cloudpilotai_workload_autoscaler.this[0]\' \'{cluster_id}\'\n'
        )
    return "".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert Terraform generated provider resources into terraform-cloudpilotai-gke module config."
    )
    parser.add_argument("--input", default="generated.tf", help="Path to the generated.tf file")
    parser.add_argument(
        "--output",
        default="module.generated.tf",
        help="Path to write the generated module configuration",
    )
    parser.add_argument(
        "--import-script",
        default="import-module.sh",
        help="Path to write the helper import script",
    )
    parser.add_argument(
        "--module-source",
        default="cloudpilot-ai/gke/cloudpilotai",
        help="Module source expression to use in the generated module block",
    )
    args = parser.parse_args()

    input_path = pathlib.Path(args.input)
    if not input_path.exists():
        print(f"input file not found: {input_path}", file=sys.stderr)
        return 1

    text = input_path.read_text()
    cluster_body = extract_resource_block(text, "cloudpilotai_gke_cluster")
    if cluster_body is None:
        print('generated.tf does not contain resource "cloudpilotai_gke_cluster"', file=sys.stderr)
        return 1

    wa_body = extract_resource_block(text, "cloudpilotai_workload_autoscaler")
    cluster_id = extract_import_id(text, "cloudpilotai_gke_cluster")

    module_text = build_module_file(cluster_body, wa_body, args.module_source)
    output_path = pathlib.Path(args.output)
    output_path.write_text(module_text)

    import_script = build_import_script(cluster_id, wa_body is not None)
    import_path = pathlib.Path(args.import_script)
    import_path.write_text(import_script)
    import_path.chmod(import_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    print(f"wrote module configuration to {output_path}")
    print(f"wrote helper import script to {import_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
