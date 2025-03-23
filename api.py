from fastapi import FastAPI, HTTPException, Response  # Handling API creation and Response
from bs4 import BeautifulSoup # For Parsing the news content
import requests # Makes HTTP requests 
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer # Text Sentiment Analyzer
from deep_translator import GoogleTranslator # Translates the English text to Hindi
from gtts import gTTS  # Provides the text to Speech Functionality
import os # Handles File Operations 
import json # Provides Data Serialization
import logging # Debuuging the code

# Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI() # Instance of FastAPI application


# Initialize VaderSentiment Analyzer
try:
    analyzer = SentimentIntensityAnalyzer()
except Exception as e:
    logger.error(f"Initialization error: {e}")
    raise


# Checking whether the news is relevant to the user input (company name)
def is_relevant_article(company, title, description):

    """Check if the article is relevant to the company."""

    # Converting to Lowercase
    company_lower = company.lower() # User input
    title_lower = title.lower()
    description_lower = description.lower()

    # Checks for the company name in company appears in title and description
    return company_lower in title_lower or company_lower in description_lower


# Fetech news from Google News RSS
def fetch_news(company, base_query, page, page_size, seen_titles, report):

    """Fetch news articles from Google News RSS for the user query."""

    # RSS url with query and pagination
    url = f"https://news.google.com/rss/search?q={base_query}&hl=en-US&gl=US&ceid=US:en&start={page * page_size}"
    response = requests.get(url, timeout=10) # Send HTTP request with 10 second timeout
    response.raise_for_status() # HHTP Status (500 - Server error,etc.,)

    # Parses the content using the beautiful soup
    soup = BeautifulSoup(response.content, 'xml')
    items = soup.find_all('item')

    for item in items:

        # Provides the news title, desc, source and publication date
        title = item.find('title').text if item.find('title') else "No title"
        description = item.find('description').text if item.find('description') else "No summary available"
        source = item.find('source').text if item.find('source') else "Unknown"
        pub_date = item.find('pubDate').text if item.find('pubDate') else "Unknown"

        
        description_soup = BeautifulSoup(description, 'html.parser')
        description = description_soup.get_text()

        # Checking for relevant article
        if is_relevant_article(company, title, description) and title not in seen_titles:
            seen_titles.add(title) # To avoid duplicates
            text = f"{title} {description}"
            sentiment = analyzer.polarity_scores(text) # Analyzes the sentiment using title and description of the news
            sentiment_label = "Positive" if sentiment['compound'] > 0.05 else "Negative" if sentiment['compound'] < -0.05 else "Neutral" # Sentiment classification based on score
            # appends the data to the report
            report.append({
                'title': title,
                'summary': description,
                'source': source,
                'date': pub_date,
                'sentiment': sentiment_label,
                'score': sentiment['compound']
            })

        # If ten articles generated, it stops
        if len(report) >= 10:
            break

    return len(items) > 0  # Return True if there are more items to fetch


# API endpoint 
@app.get("/analyze/{company}")
async def analyze_company(company: str):
    try:
        logger.info(f"Scraping news for company: {company}")
        
        page_size = 10  # Number of articles per request
        report = []
        seen_titles = set()  # Unique articles
        max_pages_per_query = 5  # Limit pagination per query
        attempted_queries = []  # Track all attempted queries

        # # Define search queries for expanded search
        queries = [
            company,
            f"{company} stock",
            f"{company} news"
        ]
        # Iterate through queries until 10 articles 
        for query in queries:
            if len(report) >= 10:
                break
            
            logger.info(f"Trying query: {query}")
            attempted_queries.append(query)
            page = 0
            # Fetch news for up to max_pages_per_query
            while len(report) < 10 and page < max_pages_per_query:
                has_more_items = fetch_news(company, query, page, page_size, seen_titles, report)
                if not has_more_items:
                    break
                page += 1

        # Log if less than 10 unique articles found
        if len(report) < 10:
            logger.warning(f"Only {len(report)} unique relevant articles found for {company} after expanded search. "
                           f"Attempted queries: {', '.join(attempted_queries)}")

        # Overall Analysis
        total_articles = len(report)
        positive = len([r for r in report if r['sentiment'] == "Positive"])
        negative = len([r for r in report if r['sentiment'] == "Negative"])
        neutral = total_articles - positive - negative
        avg_score = sum(r['score'] for r in report) / total_articles if total_articles > 0 else 0

        #Overall Summary
        summary = (f"{company} news: {total_articles} articles analyzed. "
                   f"{positive} Positive ({positive/total_articles*100:.1f}%), "
                   f"{negative} Negative ({negative/total_articles*100:.1f}%), "
                   f"{neutral} Neutral ({neutral/total_articles*100:.1f}%). "
                   f"Average sentiment score: {avg_score:.2f}")

        # Hindi Translation
        hindi_summary = GoogleTranslator(source='en', target='hi').translate(summary)

        # English and Hindi Audio files
        en_audio_file = "english_output.mp3"
        hi_audio_file = "hindi_output.mp3"
        
        # Audio generation using gTTs
        try:
            tts_en = gTTS(text=summary, lang='en', slow=False)
            tts_en.save(en_audio_file)
            tts_hi = gTTS(text=hindi_summary, lang='hi', slow=False)
            tts_hi.save(hi_audio_file)
        except Exception as e:
            logger.error(f"Error generating audio: {e}")
            raise HTTPException(status_code=500, detail=f"Audio generation failed: {e}")

        # Reading audio files
        try:
            with open(en_audio_file, "rb") as f:
                en_audio_bytes = f.read()
            with open(hi_audio_file, "rb") as f:
                hi_audio_bytes = f.read()
        except Exception as e:
            logger.error(f"Error reading audio files: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to read audio files: {e}")

        # Cleaning audio files
        try:
            os.remove(en_audio_file)
            os.remove(hi_audio_file)
        except Exception as e:
            logger.warning(f"Error cleaning up audio files: {e}")

        # JSON output (excluding audio)
        json_output = {
            "company": company,
            "total_articles": total_articles,
            "articles": report,
            "summary": {
                "text": summary,
                "hindi_text": hindi_summary,
                "positive": {"count": positive, "percentage": positive/total_articles*100 if total_articles > 0 else 0},
                "negative": {"count": negative, "percentage": negative/total_articles*100 if total_articles > 0 else 0},
                "neutral": {"count": neutral, "percentage": neutral/total_articles*100 if total_articles > 0 else 0},
                "average_sentiment_score": avg_score
            }
        }

        # Combine JSON and audio 
        response_data = {
            "data": json.dumps(json_output),  # JSON as a string
            "audio_english": en_audio_bytes.hex(),  # Audio as hex string
            "audio_hindi": hi_audio_bytes.hex()     # Audio as hex string
        }
        # Return the response as JSON
        return Response(content=json.dumps(response_data), media_type="application/json")

    # HTTP exceptions
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

if __name__ == "__main__":
    # Import uvicorn to run the server
    import uvicorn
    # Start the server on all interfaces at port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)