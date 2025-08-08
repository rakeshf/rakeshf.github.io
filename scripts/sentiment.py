import feedparser
import json
import os
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

def get_google_news(stock_name):
    feeds = [
        f"https://news.google.com/rss/search?q={stock_name}&hl=en-IN&gl=IN&ceid=IN:en",
        f"https://www.bing.com/news/search?q={stock_name}+stock&format=rss",
        f"https://finance.yahoo.com/rss/headline?s={stock_name}.NS"
    ]
    news = []
    for feed_url in feeds:
        try:
            parsed = feedparser.parse(feed_url)
            news += [(entry.title, entry.link) for entry in parsed.entries[:5]]
        except Exception as e:
            print(f"❌ Error reading {feed_url}: {e}")
    return news[:10]

def analyze_sentiment(news_list):
    analyzer = SentimentIntensityAnalyzer()
    results = []
    for title, link in news_list:
        score = analyzer.polarity_scores(title)["compound"]
        sentiment = classify_sentiment(score)
        results.append({
            "title": title,
            "link": link,
            "score": round(score, 3),
            "sentiment": sentiment
        })
    return results

def classify_sentiment(score):
    if score >= 0.05:
        return "Positive 📈"
    elif score <= -0.05:
        return "Negative 📉"
    else:
        return "Neutral 😐"

def summarize(stock, date):
    news = get_google_news(stock)
    analyzed = analyze_sentiment(news)

    pos = sum(1 for a in analyzed if "Positive" in a["sentiment"])
    neg = sum(1 for a in analyzed if "Negative" in a["sentiment"])
    neu = sum(1 for a in analyzed if "Neutral" in a["sentiment"])

    avg_score = round(sum(a["score"] for a in analyzed) / len(analyzed), 3) if analyzed else 0.0
    overall = classify_sentiment(avg_score).replace("📈", "").replace("📉", "").replace("😐", "").strip()
    overall_emoji = classify_sentiment(avg_score).split()[-1]

    return {
        "stock": stock.upper(),
        "date": date,
        "positive": pos,
        "negative": neg,
        "neutral": neu,
        "average_score": avg_score,
        "overall": f"{overall.title()} {overall_emoji}",
        "articles": analyzed
    }

if __name__ == "__main__":
    today = datetime.now().strftime("%Y-%m-%d")
    output_file = f"../data/sentiment_{today}.json"

    try:
        with open("../sentiment.txt", "r") as f:
            stocks = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("❌ sentiment.txt file not found.")
        exit(1)

    print(f"📡 Fetching news and analyzing sentiment for {len(stocks)} stock(s)...\n")

    results = []
    for stock in stocks:
        print(f"🔍 {stock}")
        result = summarize(stock, today)
        results.append(result)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Sentiment analysis saved to: {output_file}")
