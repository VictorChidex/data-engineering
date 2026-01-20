#!/usr/bin/env python
# coding: utf-8
"""
Green taxi data ingestion script with Click CLI.
Fetches green taxi parquet files from CloudFront and ingests them into PostgreSQL.
"""

import click
import pandas as pd
from sqlalchemy import create_engine
from tqdm.auto import tqdm
import pyarrow.parquet as pq
import requests
from io import BytesIO


# Data type schema for green taxi data
DTYPE_MAP = {
    "VendorID": "Int64",
    "passenger_count": "Int64",
    "trip_distance": "float64",
    "RatecodeID": "Int64",
    "store_and_fwd_flag": "string",
    "PULocationID": "Int64",
    "DOLocationID": "Int64",
    "payment_type": "Int64",
    "fare_amount": "float64",
    "extra": "float64",
    "mta_tax": "float64",
    "tip_amount": "float64",
    "tolls_amount": "float64",
    "improvement_surcharge": "float64",
    "total_amount": "float64",
    "congestion_surcharge": "float64"
}

PARSE_DATES = [
    "lpep_pickup_datetime",
    "lpep_dropoff_datetime"
]


def chunked_parquet_reader(url, batch_size=10000):
    """
    Read parquet file from URL in chunks and apply dtype conversions.
    
    Args:
        url: URL to parquet file
        batch_size: Number of records per batch
        
    Yields:
        DataFrame chunks with proper dtypes applied
    """
    response = requests.get(url)
    response.raise_for_status()
    parquet_file = pq.ParquetFile(BytesIO(response.content))

    for batch in parquet_file.iter_batches(batch_size=batch_size):
        df_chunk = batch.to_pandas()
        
        # Convert datetime columns
        for col in PARSE_DATES:
            if col in df_chunk.columns:
                df_chunk[col] = pd.to_datetime(df_chunk[col])
        
        # Convert numeric columns to specified dtypes
        for col, dtype in DTYPE_MAP.items():
            if col in df_chunk.columns:
                df_chunk[col] = df_chunk[col].astype(dtype)
        
        yield df_chunk


@click.command()
@click.option('--pg_user', required=True, help='PostgreSQL user')
@click.option('--pg_pass', required=True, help='PostgreSQL password')
@click.option('--pg_host', required=True, default='localhost', help='PostgreSQL host')
@click.option('--pg_port', required=True, type=int, default=5432, help='PostgreSQL port')
@click.option('--pg_db', required=True, help='PostgreSQL database name')
@click.option('--year', required=True, type=int, help='Year of the data (YYYY)')
@click.option('--month', required=True, type=int, help='Month of the data (MM)')
@click.option('--target_table', required=True, help='Target table name in database')
@click.option('--chunksize', default=10000, type=int, help='Chunk size for ingestion')
def ingest(pg_user, pg_pass, pg_host, pg_port, pg_db, year, month, target_table, chunksize):
    """
    Ingest green taxi data from CloudFront to PostgreSQL.
    
    Example:
        uv python ingest_green_data.py --pg_user root --pg_pass root \\
            --pg_host localhost --pg_port 5432 --pg_db ny_taxi \\
            --year 2025 --month 11 --target_table green_taxi_data --chunksize 10000
    """
    click.echo(f"Starting ingestion for {year:04d}-{month:02d}...")
    
    # Construct CloudFront URL
    url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_{year:04d}-{month:02d}.parquet"
    click.echo(f"Fetching data from: {url}")
    
    # Create database engine
    connection_string = f'postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}'
    engine = create_engine(connection_string)
    
    try:
        # Get chunked reader iterator
        df_iter = chunked_parquet_reader(url, batch_size=chunksize)
        
        # Process first chunk to create table schema
        first_chunk = next(df_iter)
        click.echo(f"Creating table '{target_table}' with schema from first chunk...")
        first_chunk.head(n=0).to_sql(name=target_table, con=engine, if_exists='replace')
        
        # Ingest first chunk
        first_chunk.to_sql(name=target_table, con=engine, if_exists='append', index=False)
        click.echo(f"Ingested first chunk: {len(first_chunk)} rows")
        
        # Ingest remaining chunks with progress bar
        total_rows = len(first_chunk)
        for df_chunk in tqdm(df_iter, desc="Ingesting chunks"):
            df_chunk.to_sql(name=target_table, con=engine, if_exists='append', index=False)
            total_rows += len(df_chunk)
        
        click.echo(f"✅ Ingestion complete! Total rows: {total_rows:,}")
        
    except Exception as e:
        click.echo(f"❌ Error during ingestion: {str(e)}", err=True)
        raise


if __name__ == '__main__':
    ingest()