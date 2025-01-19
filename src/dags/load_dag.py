import logging
import pendulum
import requests
import enum
import datetime as dt
from contextlib import contextmanager
import psycopg
import json

from airflow.decorators import dag, task
from airflow.hooks.base import BaseHook
from airflow.operators.python import get_current_context
from airflow.operators.bash import BashOperator


log = logging.getLogger(__name__)
ApiParam = enum.Enum(value='ApiParam', names=['sort_field', 'sort_direction', 'limit', 'offset'])
LoadParam = enum.Enum(value='ApiParam', names=['target_schema', 'target_table', 'api_params', 'pre_hook'])

class DAGConfig:
    API_CONN = "HTTP_DELIVERY_SYSTEM_API"
    PG_CONN = "PG_WAREHOUSE_CONNECTION"

    TARGET_SCHEMA = "stg"

    BATCH_SIZE = 50

DC = DAGConfig()

# Контекст DAG_RUN появляется только во время запуска, поэтому если не обернуть список параметров, то DAG не будет работать 
def get_api_params(context: dict):
    execution_date=context["logical_date"]
    return {
        "couriers": {
            LoadParam.target_schema: DC.TARGET_SCHEMA,
            LoadParam.target_table: "api_couriers",
            LoadParam.api_params: {
                ApiParam.sort_field.name: "id",
                ApiParam.sort_direction.name: "asc",
                ApiParam.limit.name: DC.BATCH_SIZE,
            }
        }, 
        "deliveries": {
            LoadParam.target_schema: DC.TARGET_SCHEMA,
            LoadParam.target_table: "api_deliveries",
            LoadParam.api_params: {
                ApiParam.sort_field.name: "_id",
                ApiParam.sort_direction.name: "asc",
                ApiParam.limit.name: DC.BATCH_SIZE,
                'from': execution_date.strftime('%Y-%m-%d 00:00:00'),
                'to': (execution_date+dt.timedelta(days=1)).strftime('%Y-%m-%d 00:00:00')
            }
        },
    }

@contextmanager
def PgConnection(id: str):
    conn = BaseHook.get_connection(id)
    kwargs = {
        'host': conn.host,
        'dbname': conn.schema,
        'user': conn.login,
        'password': conn.password,
        'port': conn.port
    }
    if 'sslmode' in conn.extra_dejson: kwargs['sslmode'] = conn.extra_dejson['sslmode']
    conn = psycopg.connect(**kwargs)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_api_str(log: logging.Logger, methods: dict) -> None:
    api_conn = BaseHook.get_connection(DC.API_CONN)
    for method, info in methods.items():
        with PgConnection(DC.PG_CONN) as conn:
            with conn.cursor() as cur:
                if info.get(LoadParam.pre_hook) != None:
                    cur.execute(info[LoadParam.pre_hook])
                offset_count = 0
                while True:
                    params = info[LoadParam.api_params]
                    params['offset']=DC.BATCH_SIZE*offset_count    
                    url = f"{api_conn.schema}://{api_conn.host}/{method}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
                    log.info(f'GET: {url}')
                    response = requests.get(url, headers=api_conn.extra_dejson)
                    if response.json() != []:
                        for object in response.json():
                            cur.execute(f"""
                            INSERT INTO {info[LoadParam.target_schema]}.{info[LoadParam.target_table]} (object_value, update_ts)
                            VALUES ('{json.dumps(object)}', transaction_timestamp())
                            """)
                    else: 
                        break
                    offset_count+=1
        #log.info(url)

@dag(
    schedule_interval=None, #'0/15 * * * *',
    start_date=pendulum.datetime(2022, 5, 5, tz="UTC"),
    catchup=False,
    tags=['sprint5', 'stg', 'load'],
    is_paused_upon_creation=False
)
def sprint5_load_stg_dag():
    @task()
    def api_str(task_id="get_api_str", **context):
        get_api_str(log, get_api_params(context))

    dbt_run = BashOperator(
        task_id='dbt_run',
        bash_command=f"""source {dbt_path}/.venv/bin/activate && cd {dbt_path} && dbt run --models mart --vars '{{"execution_date": "{execution_date}" }}' """,
    )

    load_api = api_str()
    load_api>>dbt_run



load_stg_dag = sprint5_load_stg_dag()