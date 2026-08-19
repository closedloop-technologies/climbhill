generator typescript_client {
  output_type "typescript"
  output_dir "../src"
  version "0.226.1"
  default_client_mode async
}

generator python_client {
  output_type "python/pydantic"
  output_dir "../climbhill"
  version "0.226.1"
  default_client_mode async
}
