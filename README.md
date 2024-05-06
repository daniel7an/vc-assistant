# Venture Capital AI Assistant

## Overview
The Venture Capital AI Assistant is a web-based application which allows users to input website URs of VCs and generates JSON representation, as well as performs similarity searches to find similar VCs.

## Architecture
- Scraping: VC website URLs are scraped using the [Jina AI Reader API](https://jina.ai/reader/), which is great tool also for generating LLM friendly output.
- Data Processing: The scraped data is processed using the OpenAI API to generate structured JSON representations of VCs, including attributes such as name, contacts, industries, and investment rounds.
- Database: The VC data is stored in PostgreSQL tables, with one table storing the main VC information and another table storing vector embeddings. 
- Web Interface: The Flask web application provides a user-friendly interface for interacting with the AI assistant.

## Similarity
The attributes *industries* and *investment_rounds* are used to implement similarity search. This approach eliminates the need for other features like name and contacts, focusing on relevant attributes for similarity calculations. Using [Pgvector](https://github.com/pgvector/pgvector-python), we compute similarity using __Euclidean distance__ and __cosine similarity__ metrics.
Here is a great [tutorial](https://severalnines.com/blog/vector-similarity-search-with-postgresqls-pgvector-a-deep-dive/) which helped me to implement similarity search with Pgvector.

## Hosting
Both the web application and the PostgreSQL database are hosted on Render cloud platform. Due to limitations of the free tier account, the application may experience slowdowns and sleep mode after 15 minutes of inactivity. Users are advised to be patient when accessing the web app, as it may take up to 1 minute to resume functionality after sleep.
