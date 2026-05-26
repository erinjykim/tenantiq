# import os
# from prometheus_client import Histogram, Counter, Gauge, multiprocess, CollectorRegistry

# # set this BEFORE importing anything else from prometheus_client
# os.environ["PROMETHEUS_MULTIPROC_DIR"] = "/tmp/prometheus_multiproc"
# os.makedirs("/tmp/prometheus_multiproc", exist_ok=True)

# from prometheus_client import Histogram, Counter, Gauge

# agent_latency = Histogram(
#     'tenantiq_agent_latency_seconds',
#     'Time spent in each agent step',
#     ['agent'],
#     buckets=[0.5, 1, 2, 5, 10, 20, 30, 60]
# )

# tokens_used = Counter(
#     'tenantiq_tokens_used_total',
#     'Total tokens consumed',
#     ['agent', 'token_type']
# )

# cost_per_request = Gauge(
#     'tenantiq_cost_per_request_usd',
#     'Estimated cost of the last request in USD',
#     multiprocess_mode='liveall'
# )

# retrieval_similarity = Histogram(
#     'tenantiq_retrieval_similarity_score',
#     'Cosine similarity scores of retrieved chunks',
#     buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
# )

# query_category = Counter(
#     'tenantiq_query_category_total',
#     'Number of queries by legal category',
#     ['category']
# )

# request_total = Counter(
#     'tenantiq_requests_total',
#     'Total number of requests processed'
# )

# request_errors = Counter(
#     'tenantiq_request_errors_total',
#     'Total number of failed requests'
# )

import os
from prometheus_client import Histogram, Counter, Gauge

agent_latency = Histogram(
    'tenantiq_agent_latency_seconds',
    'Time spent in each agent step',
    ['agent'],
    buckets=[0.5, 1, 2, 5, 10, 20, 30, 60]
)

tokens_used = Counter(
    'tenantiq_tokens_used_total',
    'Total tokens consumed',
    ['agent', 'token_type']
)

cost_per_request = Gauge(
    'tenantiq_cost_per_request_usd',
    'Estimated cost of the last request in USD'
)

retrieval_similarity = Histogram(
    'tenantiq_retrieval_similarity_score',
    'Cosine similarity scores of retrieved chunks',
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

query_category = Counter(
    'tenantiq_query_category_total',
    'Number of queries by legal category',
    ['category']
)

request_total = Counter(
    'tenantiq_requests_total',
    'Total number of requests processed'
)

request_errors = Counter(
    'tenantiq_request_errors_total',
    'Total number of failed requests'
)