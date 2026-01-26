terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project     = var.project_id
  region      = var.region
  credentials = file(var.credentials_file)
}

# GCE용 서비스 계정
resource "google_service_account" "gce_sa" {
  account_id   = "bitcoin-pipeline-gce"
  display_name = "Bitcoin Pipeline GCE Service Account"
}

# Artifact Registry 읽기 권한
resource "google_project_iam_member" "gce_ar_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.gce_sa.email}"
}

resource "google_compute_instance" "bitcoin_pipeline" {
  name                      = "bitcoin-pipeline"
  machine_type              = "e2-medium"
  zone                      = var.zone
  tags                      = ["bitcoin-pipeline"]
  allow_stopping_for_update = true

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2404-lts-amd64"
      size  = 20
    }
  }

  network_interface {
    network = "default"
    access_config {}
  }

  service_account {
    email  = google_service_account.gce_sa.email
    scopes = ["cloud-platform"]
  }
}

# SSH 허용 (특정 IP만)
resource "google_compute_firewall" "allow_ssh" {
  name    = "bitcoin-pipeline-allow-ssh"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["${var.allowed_ssh_ip}/32"]
  target_tags   = ["bitcoin-pipeline"]
  priority      = 100
}

# 다른 모든 SSH 차단
resource "google_compute_firewall" "deny_ssh" {
  name    = "bitcoin-pipeline-deny-ssh"
  network = "default"

  deny {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["bitcoin-pipeline"]
  priority      = 200
}

# IAP를 통한 SSH 접속 허용 (GitHub Actions 및 외부 접속용)
resource "google_compute_firewall" "allow_iap_ssh" {
  name    = "bitcoin-pipeline-allow-iap-ssh"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  # 구글 IAP 서비스의 고정 IP 대역입니다.
  source_ranges = ["35.235.240.0/20"]
  target_tags   = ["bitcoin-pipeline"]
  priority      = 150 # deny_ssh(200)보다 우선순위가 높아야 합니다.
}

# Artifact Registry
resource "google_artifact_registry_repository" "bitcoin_pipeline" {
  location      = var.region
  repository_id = "bitcoin-pipeline"
  description   = "Docker images for Bitcoin data pipeline"
  format        = "DOCKER"
}