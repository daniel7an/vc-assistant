from langchain_openai.embeddings import OpenAIEmbeddings
import json
import string

embeddings = OpenAIEmbeddings()

def embed_data(data):
    industry_list = json.loads(data)

    # Lowercasing
    industry_list = [industry.lower() for industry in industry_list]

    # Removing punctuation
    industry_list = [''.join(char for char in industry if char not in string.punctuation) for industry in industry_list]

    industry_text = ' '.join(industry_list)

    vector = embeddings.embed_query(industry_text)

    return vector

def nearest_neighbours(conn, cur, target_name):

    cur.execute('SELECT industries, investment_rounds FROM embeddings WHERE name = %s LIMIT 1', (target_name,))
    row = cur.fetchone()
    conn.commit()
    
    cur.execute('SELECT * FROM embeddings ORDER BY industries <-> %s, investment_rounds <-> %s LIMIT 4',
                (row[0], row[1]))
    print('cur.execute: SUCCESS')
    neighbors = cur.fetchall()
    print('cur.fetchall: SUCCESS')
    conn.commit()
    return neighbors


def cosine_similarity(conn, cur, target_name):
    cur.execute('SELECT industries, investment_rounds FROM embeddings WHERE name = %s LIMIT 1', (target_name,))
    row = cur.fetchone()
    conn.commit()
    
    cur.execute('SELECT * FROM embeddings ORDER BY industries <=> %s, investment_rounds <=> %s LIMIT 4',
                (row[0], row[1]))
    print('cur.execute: SUCCESS')
    vectors = cur.fetchall()
    print('cur.fetchall: SUCCESS')
    conn.commit()
    return vectors

