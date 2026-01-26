output "instance_ip" {
  description = "VM 외부 IP 주소"
  value       = google_compute_instance.bitcoin_pipeline.network_interface[0].access_config[0].nat_ip
}

output "ssh_command" {
  description = "SSH 접속 명령어 (IAP 터널 사용)"
  value       = "gcloud compute ssh bitcoin-pipeline --zone=${var.zone} --tunnel-through-iap"
}

output "artifact_registry_url" {
  description = "Artifact Registry URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.bitcoin_pipeline.repository_id}"
}