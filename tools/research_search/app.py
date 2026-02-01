"""
Research Literature Search Tool
A Flask application to search arXiv, IEEE, and Zenodo simultaneously.

Copyright (c) 2026 Christopher Riner
Licensed under the MIT License. See LICENSE file for details.

Wavelength-Division Ternary Optical Computer
https://github.com/jackwayne234/-wavelength-ternary-optical-computer
"""

from flask import Flask, render_template, request, jsonify
import requests
import feedparser
import time
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)


def search_arxiv(query, max_results=10):
    """Search arXiv for papers matching the query."""
    try:
        # arXiv API endpoint
        url = "http://export.arxiv.org/api/query"
        params = {
            'search_query': f'all:{query}',
            'start': 0,
            'max_results': max_results,
            'sortBy': 'relevance',
            'sortOrder': 'descending'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            feed = feedparser.parse(response.text)
            results = []
            
            for entry in feed.entries:
                results.append({
                    'title': entry.get('title', 'No title'),
                    'authors': [author.get('name', 'Unknown') for author in entry.get('authors', [])],
                    'summary': entry.get('summary', 'No abstract')[:300] + '...',
                    'url': entry.get('link', '#'),
                    'published': entry.get('published', 'Unknown date'),
                    'source': 'arXiv',
                    'id': entry.get('id', '').split('/')[-1]
                })
            
            return results
        else:
            return [{'error': f'arXiv API error: {response.status_code}'}]
    except Exception as e:
        return [{'error': f'arXiv search failed: {str(e)}'}]


def search_ieee(query, max_results=10):
    """Search IEEE Xplore for papers matching the query."""
    try:
        # Note: IEEE Xplore requires an API key for full access
        # This is a basic implementation that may have limited results without a key
        # For production use, sign up for a free API key at: https://developer.ieee.org/
        
        api_key = None  # Add your API key here if you have one
        
        url = "https://ieeexploreapi.ieee.org/api/v1/search/articles"
        params = {
            'querytext': query,
            'max_results': max_results,
            'format': 'json'
        }
        
        if api_key:
            params['apikey'] = api_key
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = []
            
            for article in data.get('articles', []):
                results.append({
                    'title': article.get('title', 'No title'),
                    'authors': article.get('authors', []),
                    'summary': article.get('abstract', 'No abstract')[:300] + '...',
                    'url': article.get('html_url', article.get('pdf_url', '#')),
                    'published': article.get('publication_year', 'Unknown'),
                    'source': 'IEEE',
                    'id': article.get('article_number', 'unknown')
                })
            
            return results
        else:
            # If no API key or error, return informative message
            return [{
                'title': 'IEEE Xplore Search',
                'summary': 'IEEE Xplore requires an API key for full search functionality. Some results may be limited. Visit https://developer.ieee.org/ to get a free API key.',
                'url': f'https://ieeexplore.ieee.org/search/searchresult.jsp?queryText={query}',
                'source': 'IEEE',
                'authors': [],
                'published': 'N/A'
            }]
    except Exception as e:
        return [{'error': f'IEEE search failed: {str(e)}'}]


def search_zenodo(query, max_results=10):
    """Search Zenodo for records matching the query."""
    try:
        url = "https://zenodo.org/api/records"
        params = {
            'q': query,
            'size': max_results,
            'sort': 'bestmatch',
            'order': 'desc'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = []
            
            for hit in data.get('hits', {}).get('hits', []):
                metadata = hit.get('metadata', {})
                results.append({
                    'title': metadata.get('title', 'No title'),
                    'authors': [creator.get('name', 'Unknown') for creator in metadata.get('creators', [])],
                    'summary': metadata.get('description', 'No description')[:300] + '...',
                    'url': hit.get('links', {}).get('html', '#'),
                    'published': metadata.get('publication_date', 'Unknown'),
                    'source': 'Zenodo',
                    'id': hit.get('id', 'unknown'),
                    'doi': metadata.get('doi', None)
                })
            
            return results
        else:
            return [{'error': f'Zenodo API error: {response.status_code}'}]
    except Exception as e:
        return [{'error': f'Zenodo search failed: {str(e)}'}]


@app.route('/')
def index():
    """Render the main search page."""
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search():
    """Handle search requests."""
    query = request.form.get('query', '').strip()
    
    if not query:
        return jsonify({'error': 'Please enter a search query'})
    
    # Search all three sources in parallel
    with ThreadPoolExecutor(max_workers=3) as executor:
        arxiv_future = executor.submit(search_arxiv, query)
        ieee_future = executor.submit(search_ieee, query)
        zenodo_future = executor.submit(search_zenodo, query)
        
        # Add small delay to be nice to APIs
        time.sleep(0.5)
        
        arxiv_results = arxiv_future.result()
        ieee_results = ieee_future.result()
        zenodo_results = zenodo_future.result()
    
    return jsonify({
        'query': query,
        'arxiv': arxiv_results,
        'ieee': ieee_results,
        'zenodo': zenodo_results,
        'total': len(arxiv_results) + len(ieee_results) + len(zenodo_results)
    })


@app.route('/health')
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({'status': 'healthy', 'service': 'research-search-tool'})


if __name__ == '__main__':
    # For local development
    app.run(debug=True, host='0.0.0.0', port=5000)
