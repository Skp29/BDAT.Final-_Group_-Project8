import requests
import time
from pymongo import MongoClient
from flask import Flask, render_template, jsonify  
from apscheduler.schedulers.background import BackgroundScheduler
import logging



app = Flask(__name__)
password = "sumit123"
# Attempt to connect to MongoDB Atlas
client = MongoClient(f"mongodb+srv://sumit:{password}@cluster0.4jrsqhs.mongodb.net/test?retryWrites=true&w=majority")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Check if the connection was successful
if client.server_info():
    print("Connected to MongoDB Atlas successfully.")

# Specify the database and collection
db = client['news_db']
collection = db['headlines']
api_key     = "91524285b94e4b29a0f15ef0e93d51db"


# ... rest of your Flask app ...

@app.route('/api/news')
def api_news():
    news_articles = collection.find({})

    # Filter out unwanted articles
    def is_valid_article(article):
        if article.get('author') is None and article.get('content') == "[Removed]":
            return False
        if article.get('description') == "[Removed]" and article.get('title') == "[Removed]":
            return False
        return True

    # Convert ObjectId to string and filter articles
    def transform_and_filter(article):
        if is_valid_article(article):
            article['_id'] = str(article['_id'])
            return article
        return None

    news_articles = [transform_and_filter(article) for article in news_articles]
    news_articles = [article for article in news_articles if article is not None]
    return jsonify(news_articles)


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/piechart')
def piechart():
    return render_template('piechart.html')


@app.route('/scatterplot')
def scatterplot():
    return render_template('scatterplot.html')

@app.route('/comparisonchart')
def comparisonchart():
    return render_template('comparisonchart.html')

@app.route('/fetch')
def fetch():
    try:  
        logging.info("Starting to fetch news...")
        url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            news_data = response.json()['articles']
            collection.insert_many(news_data)
            return f"Fetched and stored {len(news_data)} articles"
        else:
            return "Failed to fetch data from News API"

    except Exception as e:
        print("Failed to connect to MongoDB Atlas:", str(e))
        exit()
    return 'Hello, World!'



@app.route('/')
def home():
    # Fetch data from MongoDB
    news_articles = collection.find({})
    # Render data in a HTML table
    return render_template('show.html', articles=news_articles)


scheduler = BackgroundScheduler()
scheduler.add_job(func=fetch, trigger="interval", hours=24)
# scheduler.add_job(func=fetch, trigger="interval", seconds=10)

scheduler.start()

if __name__ == '__main__':
    try:
        app.run(debug=True)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()  # Not to leave behind threads
