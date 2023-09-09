from cassandra.cluster import Cluster


cluster = Cluster(["localhost"])


def create_keyspace(keyspace_name):
    try:
        session = cluster.connect("text_to_video")
        # CQL query to create the keyspace
        create_keyspace_query = f"CREATE KEYSPACE IF NOT EXISTS {keyspace_name} WITH replication = {{'class': " \
                                f"'SimpleStrategy', 'replication_factor': 1}}"
        session.execute(create_keyspace_query)
        session.shutdown()
        return f"Keyspace '{keyspace_name}' created successfully"
    except Exception as e:
        return str(e)


def create_table(keyspace_name, table):
    try:
        session = cluster.connect("text_to_video")
        if table == 'users':
            create_table_query = f"CREATE TABLE {keyspace_name}.{table} (name TEXT, email TEXT PRIMARY " \
                                 f"KEY, password TEXT, gender TEXT, age INT, location TEXT);"
        if table == 'video_data':
            create_table_query = (f'CREATE TABLE {keyspace_name}.{table} (video_id UUID PRIMARY KEY, user_email text, '
                                  f'video_title text, video_description text, video_url text, prompt text, '
                                  f'prompt_sent_timestamp timestamp, video_stored_timestamp timestamp);')
        if table == 'video_logs':
            create_table_query = (
                f'CREATE TABLE {keyspace_name}.{table} (user_email text, video_id UUID, prompt text, action text,'
                f'prompt_submitted_time timestamp, PRIMARY KEY (user_email, video_id, prompt_submitted_time));')
        session.execute(create_table_query)

        session.shutdown()
        return f"Table '{keyspace_name}.{table}' created successfully"
    except Exception as e:
        return str(e)


