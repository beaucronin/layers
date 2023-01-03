data_dir = "/Users/beau/nomad"

bind_addr = "0.0.0.0"

server {
  enabled = true
  bootstrap_expect = 1
}

client {
  enabled = true
}

ui {
  enabled = true
}