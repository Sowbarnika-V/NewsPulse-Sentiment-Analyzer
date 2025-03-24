# News Sentiment Analysis API

This project is a FastAPI-based application that fetches news articles related to a specified company, performs sentiment analysis on the articles, and provides a summary in both English and Hindi, along with audio outputs for the summaries. It uses various APIs and libraries to scrape news, analyze sentiment, translate text, and generate speech.

## Features
- **News Fetching**: Scrapes news articles from Google News RSS based on a company name.
- **Sentiment Analysis**: Uses VADER Sentiment Analyzer to classify news as Positive, Negative, or Neutral.
- **Multilingual Support**: Translates the summary into Hindi using Google Translate.
- **Text-to-Speech**: Generates audio files in English and Hindi using gTTS.
- **API Endpoint**: Provides a RESTful API to access the analysis results, including JSON data and audio outputs.

## Prerequisites
- Python 3.8 or higher
- A NewsAPI key (optional, though the current implementation uses Google News RSS instead)
- Internet connection for fetching news and translation services
