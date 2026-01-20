# data-engineering
Data Engineering Bootcamp

run python ingest_data.py \
  --pg-user=root \
  --pg-pass=root \
  --pg-host=localhost \
  --pg-port=5432 \
  --pg-db=ny_taxi \
  --target-table=yellow_taxi_trips_2 \
  --year=2021 \
  --month=1 \
  --chunksize=100000





docker network create pg-network


sudo docker build -t taxi_ingest:v001 .

# Run PostgreSQL on the network
sudo docker run -it --rm \
  --network=pg-network \
  --name pgdatabase \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="ny_taxi" \
  -v ny_taxi_postgres_data:/var/lib/postgresql \
  -p 5432:5432 \
  postgres:18


sudo docker run -it --rm \
    --network=pipeline_pg-network \
    taxi_ingest:v001 \
        --pg-user=root \
        --pg-pass=root \
        --pg-host=pgdatabase \
        --pg-port=5432 \
        --pg-db=ny_taxi \
        --target-table=yellow_taxi_trips_2021_1 \
        --year=2021 \
        --month=1 \
        --chunksize=100000


uv run pgcli -h localhost -p 5432 -u root -d ny_taxi

# In another terminal, run pgAdmin on the same network


sudo docker run -it --rm \
  --network=pg-network \
  --name pgdatabase \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="ny_taxi" \
  -v ny_taxi_postgres_data:/var/lib/postgresql \
  -p 5432:5432 \
  postgres:18

sudo docker run -it \
  -e PGADMIN_DEFAULT_EMAIL="admin@admin.com" \
  -e PGADMIN_DEFAULT_PASSWORD="root" \
  -v pgadmin_data:/var/lib/pgadmin \
  -p 8085:80 \
  --network=pg-network \
  --name pgadmin \
  dpage/pgadmin4

  