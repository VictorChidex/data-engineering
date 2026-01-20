#!/usr/bin/env python
# coding: utf-8
"""
NYC Taxi Zone data ingestion script with Click CLI.
Fetches zone lookup CSV files and ingests them into PostgreSQL.
"""

import click
import pandas as pd
from sqlalchemy import create_engine


# Data type schema for zone lookup data
DTYPE_MAP = {
    "LocationID": "int64",
    "Borough": "string",
    "Zone": "string",
    "service_zone": "string"
}

# Default URL for NYC Taxi Zone Lookup data
DEFAULT_URL = "https://github.com/DataTalksClub/nyc-tlc-data/releases/download/misc/taxi_zone_lookup.csv"


@click.command()
@click.option('--pg_user', required=True, help='PostgreSQL user')
@click.option('--pg_pass', required=True, help='PostgreSQL password')
@click.option('--pg_host', default='localhost', help='PostgreSQL host')
@click.option('--pg_port', default=5432, type=int, help='PostgreSQL port')
@click.option('--pg_db', required=True, help='PostgreSQL database name')
@click.option('--target_table', default='taxi_zone_lookup', help='Target table name in database')
@click.option('--url', default=DEFAULT_URL, help='CSV URL for zone lookup data (uses default if not provided)')
def ingest(pg_user, pg_pass, pg_host, pg_port, pg_db, target_table, url):
    """
    Ingest NYC taxi zone lookup data from CSV to PostgreSQL.
    
    Automatically uses the default zone lookup URL unless overridden.
    
    Example (with defaults):
        python ingest_zone_data.py --pg_user root --pg_pass root \\
            --pg_db ny_taxi
    
    Example (with custom table name):
        python ingest_zone_data.py --pg_user root --pg_pass root \\
            --pg_db ny_taxi --target_table zones
    
    Example (with custom URL):
        python ingest_zone_data.py --pg_user root --pg_pass root \\
            --pg_db ny_taxi --url "https://custom-url.com/zones.csv"
    """
    click.echo(f"Starting zone data ingestion...")
    click.echo(f"Fetching data from: {url}")
    
    # Create database engine
    connection_string = f'postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}'
    engine = create_engine(connection_string)
    
    try:
        # Read CSV with proper dtypes
        df = pd.read_csv(url, dtype=DTYPE_MAP)
        click.echo(f"Loaded {len(df)} zone records")
        
        # Create table with schema
        df.head(n=0).to_sql(name=target_table, con=engine, if_exists='replace', index=False)
        click.echo(f"Created table '{target_table}'")
        
        # Ingest all data
        df.to_sql(name=target_table, con=engine, if_exists='append', index=False)
        click.echo(f"✅ Zone data ingestion complete! Total rows: {len(df):,}")
        
    except Exception as e:
        click.echo(f"❌ Error during ingestion: {str(e)}", err=True)
        raise


if __name__ == '__main__':
    ingest()