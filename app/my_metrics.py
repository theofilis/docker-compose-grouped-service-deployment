import prometheus_client

heads_count = prometheus_client.Counter(
    "heads_count",
    "Number of heads"
)
