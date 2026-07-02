variable "cloudpilotai_api_endpoint" {
  type    = string
  default = "https://api.cloudpilot.ai"
}

variable "cloudpilotai_api_key" {
  type      = string
  sensitive = true
}

variable "cluster_name" {
  type = string
}

variable "region" {
  type = string
}

variable "project_id" {
  type    = string
  default = null
}

variable "cluster_uid" {
  type    = string
  default = null
}

variable "cluster_location" {
  type    = string
  default = null
}

variable "kubeconfig" {
  type    = string
  default = null
}

variable "skip_restore" {
  type    = bool
  default = false
}

variable "restore_node_number" {
  type    = number
  default = 2
}
