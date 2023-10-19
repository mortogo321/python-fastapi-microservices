from os import environ as env

from redis_om import get_redis_connection

database = get_redis_connection(
    host=env["REDIS_HOST"],
    port=env["REDIS_PORT"],
    password=env["REDIS_PASSWORD"],
)
