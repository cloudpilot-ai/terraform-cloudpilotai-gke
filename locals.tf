locals {
  nodeclass_templates = var.nodeclass_templates == null ? [] : var.nodeclass_templates
  nodeclasses         = var.nodeclasses == null ? null : var.nodeclasses
  nodepool_templates  = var.nodepool_templates == null ? [] : var.nodepool_templates
  nodepools           = var.nodepools == null ? null : var.nodepools

  nodeclass_template_map = {
    for template in local.nodeclass_templates :
    try(template.template_name != null ? template.template_name : "", "") => {
      for key, value in template : key => value
      if key != "template_name" && value != null
    }
    if try(template.template_name != null ? template.template_name : "", "") != ""
  }

  rendered_nodeclasses = local.nodeclasses == null ? null : [
    for nodeclass in local.nodeclasses : merge(
      lookup(local.nodeclass_template_map, try(nodeclass.template_name != null ? nodeclass.template_name : "", ""), {}),
      {
        for key, value in nodeclass : key => value
        if key != "template_name" && value != null
      }
    )
  ]

  nodepool_template_map = {
    for template in local.nodepool_templates :
    try(template.template_name != null ? template.template_name : "", "") => {
      for key, value in template : key => value
      if key != "template_name" && value != null
    }
    if try(template.template_name != null ? template.template_name : "", "") != ""
  }

  rendered_nodepools = local.nodepools == null ? null : [
    for nodepool in local.nodepools : merge(
      lookup(local.nodepool_template_map, try(nodepool.template_name != null ? nodepool.template_name : "", ""), {}),
      {
        for key, value in nodepool : key => value
        if key != "template_name" && value != null
      }
    )
  ]

  effective_only_install_agent = var.only_install_agent != null ? var.only_install_agent : (
    var.enable_node_autoscaler != null ? !var.enable_node_autoscaler : null
  )
  effective_skip_restore          = var.skip_restore != null ? var.skip_restore : var.node_autoscaler_skip_restore
  effective_restore_desired_size  = var.restore_node_number != null ? var.restore_node_number : var.node_autoscaler_restore_desired_size
  effective_restore_desired_sizes = var.restore_desired_sizes != null ? var.restore_desired_sizes : var.node_autoscaler_restore_desired_sizes
}
