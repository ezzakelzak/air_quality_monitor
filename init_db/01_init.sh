#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE ecologie_data;
    GRANT ALL PRIVILEGES ON DATABASE ecologie_data TO $POSTGRES_USER;
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "ecologie_data" <<-EOSQL
    CREATE TABLE IF NOT EXISTS raw_measurements (
        city VARCHAR(50),
        latitude FLOAT,
        longitude FLOAT,
        timestamp TIMESTAMPTZ,
        pm10 FLOAT,
        pm2_5 FLOAT,
        no2 FLOAT,
        o3 FLOAT,
        so2 FLOAT,
        aqi FLOAT
    );
    
    -- Admin is superuser, no need for extra grants
EOSQL
