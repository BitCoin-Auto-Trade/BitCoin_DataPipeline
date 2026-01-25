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

resource "google_compute_instance" "bitcoin_pipeline" {
  name         = "bitcoin-pipeline"
  machine_type = "e2-medium"
  zone         = var.zone
  tags         = ["bitcoin-pipeline"]

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
