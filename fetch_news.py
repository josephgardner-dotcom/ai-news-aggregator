#!/usr/bin/env python3
"""
AI News Aggregator - RSS Feed Fetcher
Fetches AI news from configured RSS feeds and generates HTML output
"""

import feedparser
import json
from datetime import datetime, timedelta
from dateutil import parser as date_parser
import sys
from collections import defaultdict

def load_config(config_file='config.json'):
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Config file '{config_file}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in config file: {e}")
        sys.exit(1)

def fetch_feed(feed_url, feed_name):
    """Fetch and parse a single RSS feed"""
    try:
        feed = feedparser.parse(feed_url)
        if feed.bozo:
            print(f"Warning: Feed '{feed_name}' had parsing issues")
        return feed
    except Exception as e:
        print(f"Error fetching feed '{feed_name}': {e}")
        return None

def parse_date(date_string):
    """Parse various date formats into datetime object"""
    if not date_string:
        return datetime.now()

    try:
        # Try parsing with dateutil first (handles most formats)
        parsed = date_parser.parse(date_string)
        # Remove timezone info to make it naive for comparison
        if parsed.tzinfo is not None:
            parsed = parsed.replace(tzinfo=None)
        return parsed
    except:
        # Fallback to current time if parsing fails
        return datetime.now()

def get_articles(config):
    """Fetch articles from all configured feeds"""
    articles = []
    cutoff_date = datetime.now() - timedelta(days=config['days_to_show'])

    for feed_config in config['feeds']:
        feed_name = feed_config['name']
        feed_url = feed_config['url']
        category = feed_config['category']

        print(f"Fetching {feed_name}...")
        feed = fetch_feed(feed_url, feed_name)

        if not feed or not hasattr(feed, 'entries'):
            continue

        count = 0
        for entry in feed.entries:
            if count >= config['max_articles_per_feed']:
                break

            # Parse publication date
            pub_date = None
            if hasattr(entry, 'published'):
                pub_date = parse_date(entry.published)
            elif hasattr(entry, 'updated'):
                pub_date = parse_date(entry.updated)
            else:
                pub_date = datetime.now()

            # Only include recent articles
            if pub_date < cutoff_date:
                continue

            # Extract article details
            article = {
                'title': entry.get('title', 'No Title'),
                'link': entry.get('link', '#'),
                'published': pub_date,
                'published_str': pub_date.strftime('%Y-%m-%d'),
                'source': feed_name,
                'category': category,
                'summary': entry.get('summary', '')[:300] + '...' if len(entry.get('summary', '')) > 300 else entry.get('summary', '')
            }

            articles.append(article)
            count += 1

    # Sort by publication date (newest first)
    articles.sort(key=lambda x: x['published'], reverse=True)

    return articles

def group_by_category(articles):
    """Group articles by category"""
    categories = defaultdict(list)
    for article in articles:
        categories[article['category']].append(article)
    return dict(categories)

def generate_html(articles, config):
    """Generate HTML page from articles"""
    grouped_articles = group_by_category(articles)

    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI News Aggregator</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            line-height: 1.6;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            text-align: center;
        }

        h1 {
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .subtitle {
            color: #666;
            font-size: 1.1em;
        }

        .last-updated {
            color: #999;
            font-size: 0.9em;
            margin-top: 10px;
        }

        .category-section {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }

        .category-header {
            color: #667eea;
            font-size: 1.8em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }

        .article {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 15px;
            transition: transform 0.2s, box-shadow 0.2s;
            border-left: 4px solid #667eea;
        }

        .article:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }

        .article-title {
            font-size: 1.3em;
            margin-bottom: 8px;
        }

        .article-title a {
            color: #333;
            text-decoration: none;
            font-weight: 600;
        }

        .article-title a:hover {
            color: #667eea;
        }

        .article-meta {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
        }

        .article-source {
            color: #667eea;
            font-weight: 600;
        }

        .article-date {
            color: #999;
        }

        .article-summary {
            color: #555;
            margin-top: 10px;
        }

        footer {
            text-align: center;
            color: white;
            padding: 20px;
            margin-top: 30px;
        }

        @media (max-width: 768px) {
            h1 {
                font-size: 1.8em;
            }

            .category-header {
                font-size: 1.4em;
            }

            .article-title {
                font-size: 1.1em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 AI News Aggregator</h1>
            <div class="subtitle">Daily curated AI news from top sources</div>
            <div class="last-updated">Last updated: """ + datetime.now().strftime('%B %d, %Y at %H:%M UTC') + """</div>
        </header>
"""

    # Add articles grouped by category
    category_order = [
        'Company Announcements',
        'Enterprise AI',
        'AI Agents & Automation',
        'Research & Development',
        'AI Governance & Policy',
        'Industry News'
    ]
    for category in category_order:
        if category in grouped_articles:
            html += f"""
        <div class="category-section">
            <h2 class="category-header">{category}</h2>
"""
            for article in grouped_articles[category]:
                html += f"""
            <div class="article">
                <div class="article-title">
                    <a href="{article['link']}" target="_blank">{article['title']}</a>
                </div>
                <div class="article-meta">
                    <span class="article-source">{article['source']}</span>
                    <span class="article-date"> • {article['published_str']}</span>
                </div>
"""
                if article['summary']:
                    html += f"""
                <div class="article-summary">{article['summary']}</div>
"""
                html += """
            </div>
"""
            html += """
        </div>
"""

    html += """
        <footer>
            <p>Generated automatically • Updates daily</p>
        </footer>
    </div>
</body>
</html>"""

    return html

def main():
    """Main execution function"""
    print("AI News Aggregator - Starting fetch...")

    # Load configuration
    config = load_config()

    # Fetch articles
    articles = get_articles(config)
    print(f"\nFetched {len(articles)} total articles")

    # Generate HTML
    html = generate_html(articles, config)

    # Write to file
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("✓ Generated index.html successfully!")

if __name__ == '__main__':
    main()
