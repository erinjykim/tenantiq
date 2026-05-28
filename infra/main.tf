terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = "tenantiq-497707"
  region  = "us-central1"
}

resource "google_cloud_run_service" "tenantiq" {
  name     = "tenantiq"
  location = "us-central1"

  template {
    spec {
      containers {
        image = "gcr.io/tenantiq-497707/tenantiq"
        resources {
          limits = {
            memory = "1Gi"
            cpu    = "1000m"
          }
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

resource "google_cloud_run_service_iam_member" "public" {
  service  = google_cloud_run_service.tenantiq.name
  location = google_cloud_run_service.tenantiq.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "service_url" {
  value = google_cloud_run_service.tenantiq.status[0].url
}