import psycopg2
from pgvector.psycopg2 import register_vector

# def connect_to_database():
#     # Connect to the PostgreSQL database
#     conn = psycopg2.connect(
#         dbname="vc-data",
#         user="postgres",
#         password="Magavuz77*",
#         host="localhost",
#         port="5432"
#     )

    # return conn

def connect_to_database():
    # Connect to the PostgreSQL database
    conn = psycopg2.connect(
        dbname="vcdata",
        user="vcdata_user",
        password="04mIVJWnpVCaYx3EziK0toZvq8sW5FZc",
        host="dpg-corloui0si5c739ihihg-a.oregon-postgres.render.com",
        port="5432"
    )

    return conn

def create_tables(conn, cur):
    cur.execute('CREATE EXTENSION IF NOT EXISTS vector')
    register_vector(conn)

    # Create VectorDB table for our embeddings
    cur.execute("""CREATE TABLE IF NOT EXISTS embeddings (id bigserial PRIMARY KEY,
                website VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(255), industries vector(1536),
                investment_rounds vector(1536))""")
    # Create our main table with infomation abou VCs
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
