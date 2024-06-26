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

# Creating Flask app instance
app = Flask(__name__)
CORS(app)

# Connect to the PostgreSQL database
conn = connect_to_database()
# Create a cursor object to execute SQL queries
cur = conn.cursor()

# Create the tables in the database
create_tables(conn, cur)

# Adding initial 10 VCs data embeddings to database for implementing similarity search
add_initial_data(conn, cur)

# in the end, we need to commit changes and close connections to databse
conn.commit()
cur.close()
conn.close()

# Getting OPENAI API KEY
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
    try:
        data = request.get_json()
        user_input = data.get('data')
        # For very big websites, our scraper can be unable to scrape, just and shut down. 
        # We handle it with exception.
        jina_response = requests.get(jina_api + user_input)
    except:
        return jsonify({"response":False, "message": 'Unable to scrape the website. Maybe it is very complex'})
    
    # Check if the request from scraper was successful (status code 200)
    if jina_response.status_code == 200:
        scraped_data = jina_response.text

        a = 0 # variable, for additional output generation, in case of errors in GPT output.

        while True:
            try:
                # Connect to the PostgreSQL database
                conn = connect_to_database()
                cur = conn.cursor()

                # Getting relevant information with LLM
                completion = client.completions.create(model='gpt-3.5-turbo-instruct', prompt=f'Use scraped website data below to generate json file with the VC information (4 attributes): name, contacts (it is important to fill email, phone number, address), industries (list: represents industries where company invests), investment_rounds (list). Text: {scraped_data}', max_tokens=400)
                output = json.loads(completion.choices[0].text)
                keys = list(output.keys())
                
                # extracting our attributes
                name = output[keys[0]]
                contacts = json.dumps(output[keys[1]])
                industries = json.dumps(output[keys[2]])
                investment_rounds = json.dumps(output[keys[3]])

                # Adding data into our main table
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

                # Return answer to user
                return jsonify({"response":True, "message": json.dumps(output) + f"\n SIMILAR VCs ----->  Nearest Neighbors: {euclidean}, Cosine Similarity: {cosine}"})

            except (json.decoder.JSONDecodeError, AttributeError)  as e:
                # These errors may occur because the OpenAI API model sometimes fails to generate proper JSON format text.
                # We provide more attempts to fix these mistakes.
                print(e)
                a += 1
                if a >= 5:
                    return jsonify({"response":False, "message": 'Error: Unable to generate proper JSON representation. Please provide website link again :)'})
            except openai.BadRequestError as e:
                # These error occurs due to limitations in the GPT-3.5 model's capabilities.
                # Most likely scraped data from the website has a big size.
                print(e)
                return jsonify({"response":False, "message": 'Error: Website content is too complex to process'})
            except Exception as e:
                # For any other errors, we assume that they are in most cases related with the response LLM gives to us
                # and we give more chances to it to generate correct output.
                print(e)
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