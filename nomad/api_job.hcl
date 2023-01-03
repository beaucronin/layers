// A Nomad job file for running the Layers API server via uvicorn. This is currently implemented as a raw_exec job, so it runs directly on the host machine. 
// It's not a Docker container, so it doesn't need to be built and pushed to a registry.

job "api" {
  region      = "global"
  datacenters = ["dc1"]

  type = "service"

  group "main" {
    count = 1

    network {
      port "http" {
        static = 8001
      }

      port "https" {}
    }

    task "uvicorn" {
      driver = "raw_exec"

      config {
        command = "/Users/beau/venv/bin/uvicorn"
        args    = ["app.routes:app", "--port", "8001", "--host", "192.168.7.158", "--app-dir", "/Users/beau/layers/api"]
      }
      env {
        VIRTUAL_ENV = "/Users/beau/venv"
        LAYERS_SECRET_KEY = "FIXME"
        DB_CREDS = "FIXME"
      }
    }
  }
}