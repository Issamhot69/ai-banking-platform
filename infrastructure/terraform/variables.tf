variable "project_name" {
  description = "Nom du projet"
  type        = string
  default     = "ai-banking"
}

variable "environment" {
  description = "Environnement"
  type        = string
  default     = "production"
}

variable "aws_region" {
  description = "AWS Region"
  type        = string
  default     = "eu-west-1"
}

variable "db_password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
}

variable "redis_password" {
  description = "Redis auth token"
  type        = string
  sensitive   = true
}
