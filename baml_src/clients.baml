client<llm> ClimbHillOpenAI {
  provider openai-responses
  options {
    model "gpt-5.1-2025-11-13"
    api_key env.OPENAI_API_KEY
  }
}

retry_policy BoundedRetry {
  max_retries 2
  strategy {
    type exponential_backoff
    delay_ms 300
    multiplier 2
    max_delay_ms 2000
  }
}
