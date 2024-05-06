import psycopg2
from pgvector.psycopg2 import register_vector
import os
import csv
import json
import numpy as np

DATABASE_URL = os.environ.get('DATABASE_URL')

def connect_to_database():
    # Connect to the PostgreSQL database
    conn = psycopg2.connect(DATABASE_URL)

    return conn

def create_tables(conn, cur):
    cur.execute('CREATE EXTENSION IF NOT EXISTS vector')
    register_vector(conn)

    # Create VectorDB table for our embeddings
    cur.execute("""CREATE TABLE IF NOT EXISTS embeddings (id bigserial PRIMARY KEY,
                website VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(255), industries vector(1536),
                investment_rounds vector(1536))""")
    # Create our main table with infomation about VCs
    cur.execute('''
                CREATE TABLE IF NOT EXISTS venture_capital (
                    id SERIAL PRIMARY KEY,
                    website VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255),
                    contacts jsonb,
                    industries jsonb,
                    investment_rounds jsonb
                );
                ''')
    
def add_initial_data(conn, cur):
    with open('initial_data/embeddings.csv', 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                website = row[1]
                name = row[2]

                industries = np.array(row[3].replace('[', '').replace(']', '').split(',')).astype(float).tolist()
                investment_rounds = np.array(row[4].replace('[', '').replace(']', '').split(',')).astype(float).tolist()

                insert_query = '''
                INSERT INTO embeddings (website, name, industries, investment_rounds)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (website) DO UPDATE 
                SET name = EXCLUDED.name, 
                    industries = EXCLUDED.industries, 
                    investment_rounds = EXCLUDED.investment_rounds;
                '''
                cur.execute(insert_query, (website, name, industries, investment_rounds))
                conn.commit()
