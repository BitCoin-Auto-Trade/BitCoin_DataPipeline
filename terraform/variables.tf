variable "project_id" {
  description = "GCP 프로젝트 ID"
  type        = string
}

variable "region" {
  description = "리전 (AWS의 region과 동일)"
  type        = string
  default     = "asia-northeast3" # 서울 (AWS는 ap-northeast-2)
}

variable "zone" {
  description = "존 (AWS의 Availability Zone과 동일)"
  type        = string
  default     = "asia-northeast3-a"
}

variable "credentials_file" {
  description = "GCP 서비스 계정 키 파일 경로"
  type        = string
  default     = "../keys/gcp-key.json"
}

variable "allowed_ssh_ip" {
  description = "SSH 접속 허용 IP"
  type        = string
  sensitive   = true
}
