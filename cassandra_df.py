import pandas as pd
import os
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster, Session, ResultSet, DCAwareRoundRobinPolicy
from cassandra.policies import RetryPolicy, FallthroughRetryPolicy

cassandra_df_data = [
    ['Environment', 'contact_points', 'username', 'password', 'datacenter_name'],
    ['LOCAL', ["127.0.0.1"], None, None, "datacenter1"],
]


# Define a custom retry policy with exponential backoff
class ExponentialBackoffRetryPolicy(RetryPolicy):
    def on_read_timeout(self, query, consistency, required_responses,
                        received_responses, data_retrieved, retry_num):
        if retry_num < 5:  # Limit the number of retries
            return (True, 0.5 * (2 ** retry_num))  # Exponential backoff
        else:
            return (False, 0.0)  # Give up after max retries


cassandra_df = pd.DataFrame(cassandra_df_data[1:], columns=cassandra_df_data[0])
env_details = cassandra_df[cassandra_df['Environment'] == 'LOCAL']

contact_points = env_details["contact_points"].values[0]
datacenter_name = env_details["datacenter_name"].values[0]
auth_provider = PlainTextAuthProvider(username=env_details["username"].values[0],
                                      password=env_details["password"].values[0])
cluster = Cluster(contact_points=contact_points,
                  auth_provider=auth_provider,
                  load_balancing_policy=DCAwareRoundRobinPolicy(local_dc=datacenter_name),
                  protocol_version=4)
cluster.default_retry_policy = FallthroughRetryPolicy()
session = cluster.connect()  # Create a session to interact with the cluster
