import requests
import openai
from openai import OpenAI
import json
from flask import Flask
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os

# importing custom methods
from db import connect_to_database, create_tables, add_initial_data
from similarity import embed_data, nearest_neighbours, cosine_similarity

app = Flask(__name__)
CORS(app)

# Connect to the PostgreSQL database
conn = connect_to_database()
print('Database connection established')

# Create a cursor object to execute SQL queries
cur = conn.cursor()

# Create the tables in the database
create_tables(conn, cur)
print('Tables created successfully')

# Adding initial 10 VCs data embeddings to database for implementing similarity search
add_initial_data(conn, cur)
print('Initial data adedded successfully')

conn.commit()
cur.close()
conn.close()

openai_api_key = os.environ.get('OPENAI_API_KEY')

# Creating OpenAI client
client = OpenAI(api_key=openai_api_key)

# API for scraping websites
jina_api = 'https://r.jina.ai/'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data', methods=['POST'])
def get_data():
    data = request.get_json()
    user_input = data.get('data')
    jina_response = requests.get(jina_api + user_input)

    # Check if the request from scraper was successful (status code 200)
    if jina_response.status_code == 200:
        scraped_data = jina_response.text

        a = 0 # variable, for additional output generation, in case of errors.

        while True:
            try:
                # Connect to the PostgreSQL database
                conn = connect_to_database()
                
                completion = client.completions.create(model='gpt-3.5-turbo-instruct', prompt=f'Use scraped website data below to generate json file with the VC information (4 attributes): name, contacts (it is important to fill email, phone number, address), industries (list: represents industries where company invests), investment_rounds (list). Text: {scraped_data}', max_tokens=400)
                output = json.loads(completion.choices[0].text)
                keys = list(output.keys())
                
                name = output[keys[0]]
                contacts = json.dumps(output[keys[1]])
                industries = json.dumps(output[keys[2]])
                investment_rounds = json.dumps(output[keys[3]])

                print('Check1')
                insert_vc = '''
                INSERT INTO venture_capital (website, name, contacts, industries, investment_rounds)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (website) DO UPDATE 
                SET name = EXCLUDED.name, 
                    contacts = EXCLUDED.contacts, 
                    industries = EXCLUDED.industries, 
                    investment_rounds = EXCLUDED.investment_rounds;
                '''
                cur.execute(insert_vc, (user_input.strip(), name, contacts, industries, investment_rounds))
                conn.commit()
                print('Check2')
                
                # Embed industries and investment_rounds, for similarity search
                industry_vector = embed_data(json.dumps(industries))
                investment_rounds_vector = embed_data(json.dumps(investment_rounds))
                # Adding embedded vectors to our VectorDB table
                insert_vector = '''
                INSERT INTO embeddings (website, name, industries, investment_rounds)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (website) DO UPDATE 
                SET name = EXCLUDED.name, 
                    industries = EXCLUDED.industries, 
                    investment_rounds = EXCLUDED.investment_rounds;
                '''
                cur.execute(insert_vector, (user_input.strip(), name, industry_vector, investment_rounds_vector))
                conn.commit()

                # Calculate similarities between VCs and return 3 most similar ones.
                neighbors = nearest_neighbours(conn, cur, name)
                cos_similarity = cosine_similarity(conn, cur, name)

                cosine = [cos[2] for cos in cos_similarity[1:]]
                euclidean = [neighbor[2] for neighbor in neighbors[1:]]
                print('Check4')

                # Return answer to user
                return jsonify({"response":True, "message": json.dumps(output) + f"\n SIMILAR VCs ----->  Nearest Neighbors: {euclidean}, Cosine Similarity: {cosine}"})

            except (json.decoder.JSONDecodeError, AttributeError)  as e:
                # These errors may occur because the OpenAI API model sometimes fails to generate proper JSON format text.
                # We provide more attempts to fix these mistakes.
                print(e)
                print(a)
                a += 1
                if a >= 5:
                    return jsonify({"response":False, "message": 'Error: Unable to generate JSON representation. Please try again.'})
            except openai.BadRequestError as e:
                print(e)
                # These error occurs due to limitations in the GPT-3.5 model's capabilities.
                return jsonify({"response":False, "message": 'Error: Website content is too complex to process'})
            except Exception as e:
                # For any other errors, we assume that they are in most cases related with the response LLM gives to us
                # and we give more chances to it to genrate correct output.
                print(e)
                print(a)
                a += 1
                if a>=5:
                    return jsonify({"response":False, "message": str(e)})
            finally:
                cur.close()
                conn.close()

    else:
        # In this case if Jina API fails to scrape the website, most likely the url
        # provided from the user was incorrect.
        return jsonify({"response":False, "message": 'Website url is incorrect.'})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)


