import os
import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "masteroz",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "email_on_failure": False,
    "email_on_retry": False,
}

dag = DAG(
    dag_id="nlp_trendscope_pipeline",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["nlp", "dvc", "production"],
    default_args=default_args,
)

with dag:
    def scrape():
        logging.info("Starting scraping...")
        os.system("python scrapper.py")

    scrape_data = PythonOperator(
        task_id="scrape_data",
        python_callable=scrape,
    )

    def preprocess():
        logging.info("Starting preprocessing...")
        os.system("python preprocessor.py")

    preprocess_data = PythonOperator(
        task_id="preprocess_data",
        python_callable=preprocess,
    )

    def generate():
        logging.info("Generating features...")
        os.system("python representation.py")

    generate_features = PythonOperator(
        task_id="generate_features",
        python_callable=generate,
    )

    def compute_stats():
        logging.info("Computing linguistic statistics...")
        os.system("python report.py")

    compute_statistics = PythonOperator(
        task_id="compute_statistics",
        python_callable=compute_stats,
    )

    def push_data():
        logging.info("Pushing data to DVC remote...")
        os.system("dvc add data/")
        os.system("dvc push")
        os.system("git add . && git commit -m 'Airflow pipeline update' && git push")

    dvc_push = PythonOperator(
        task_id="dvc_push",
        python_callable=push_data,
    )

    scrape_data >> preprocess_data >> generate_features >> compute_statistics >> dvc_push