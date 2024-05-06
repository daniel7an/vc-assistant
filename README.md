# Venture Capital AI Assistant

## Overview
The Venture Capital AI Assistant is a web-based application that leverages artificial intelligence and natural language processing to facilitate the exploration and discovery of venture capital (VC) data. The application allows users to input website URLs containing VC-related information and generates informative summaries, as well as performs similarity searches to find similar VCs based on specific attributes.

## Architecture
- Scraping: VC website URLs are scraped using the [Jina AI Reader API](https://jina.ai/reader/), which is great tool to generate LLM friendly text.
- Data Processing: The scraped data is processed using the OpenAI API to generate structured JSON representations of VCs, including attributes such as name, contacts, industries, and investment rounds.
- Database: The VC data is stored in PostgreSQL tables, with one table storing the main VC information and another table storing vector embeddings.
- Similarity Search: Vector embeddings are used to compute similarities between VCs. 
- Web Interface: The Flask web application provides a user-friendly interface for interacting with the AI assistant.
