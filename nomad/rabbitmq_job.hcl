// This is a Nomad job file that deploys a RabbitMQ server for communication between the various services.
// It is currently implemented as a raw_exec job, but should be implemented as another type of job in the future.

job "rabbitmq" {
  datacenters = ["dc1"]
  type = "service"
  group "rabbitmq" {
    count = 1
    network {
      port "amqp" {
        static = 5672
      }
    }
    task "rabbitmq" {
      driver = "raw_exec"
      config {
        command = "/usr/local/opt/rabbitmq/sbin/rabbitmq-server"
      }
      resources {
        cpu    = 500 # 500 MHz
        memory = 384 # 128MB
      }
    }
  }
}