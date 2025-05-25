#!/usr/bin/env python3
"""
Matschia - Twitter Analysis Web Application
This Flask application provides a web interface for the Twitter analysis tool with a modern shadcn-like UI.
"""
import os
import json
import asyncio
import logging
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename

# Import modules for Twitter analysis
from twitter_wrapper import fetch_tweets_async
from twitter_analyzer import TwitterAnalyzer, TweetData
from tweet_poster import post_reply_async

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)
Bootstrap(app)

# Configure file paths
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = SCRIPT_DIR / "data.json"
ANALYSIS_PATH = SCRIPT_DIR / "analysis_results.json"
STORAGE_STATE_PATH = SCRIPT_DIR / "state.json"

# Global variables
twitter_analyzer = TwitterAnalyzer()

@app.route('/')
def index():
    """Render the home page with the scroll count form"""
    return render_template('index.html')

@app.route('/fetch_tweets', methods=['POST'])
def fetch_tweets():
    """Fetch tweets based on the number of scrolls"""
    scroll_count = request.form.get('scroll_count', 3)
    try:
        scroll_count = int(scroll_count)
        if scroll_count < 1 or scroll_count > 10:
            flash('Please enter a valid number between 1 and 10 for scroll count.', 'warning')
            scroll_count = 3  # Reset to default
    except ValueError:
        flash('Please enter a valid number for scroll count.', 'warning')
        scroll_count = 3  # Default to 3 scrolls if invalid input
    
    # Always fetch fresh tweets when requested
    try:
        # Start async task to fetch tweets
        asyncio.run(fetch_tweets_async(scroll_count))
        flash(f'Successfully fetched tweets with {scroll_count} scrolls!', 'success')
    except Exception as e:
        logger.error(f"Error fetching tweets: {str(e)}")
        flash(f'Error fetching tweets: {str(e)}', 'error')
        return render_template('error.html', error_code="Fetch Error", message=f"Failed to fetch tweets: {str(e)}")
    
    # Load fetched tweets
    try:
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            tweets = json.load(f)
        
        if not tweets:
            flash('No tweets were found. Please try again.', 'warning')
            return redirect(url_for('index'))
            
        # Store tweet count in session for later use
        session['tweet_count'] = len(tweets)
        return render_template('tweets.html', tweets=tweets)
    except Exception as e:
        logger.error(f"Error loading tweets: {str(e)}")
        flash(f'Error loading tweets: {str(e)}', 'error')
        return render_template('error.html', error_code="Data Error", message=f"Could not load tweet data: {str(e)}")

@app.route('/analyze_tweets')
def analyze_tweets():
    """Analyze tweets and generate a reply"""
    if not DATA_PATH.exists():
        flash('No tweets available for analysis. Please fetch tweets first.', 'warning')
        return redirect(url_for('index'))
        
    try:
        # Run the Twitter analyzer asynchronously
        results = asyncio.run(_analyze_tweets())
        
        # Check if there was an error in analysis
        if 'error' in results:
            flash(results['error'], 'error')
            return render_template('error.html', error_code="Analysis Error", message=results['error'])
            
        # Store results in session
        session['analysis_results'] = results
        
        return render_template('analysis.html', results=results)
    except Exception as e:
        logger.error(f"Error analyzing tweets: {str(e)}")
        flash(f'Error analyzing tweets: {str(e)}', 'error')
        return render_template('error.html', error_code="Analysis Error", message=f"Failed to analyze tweets: {str(e)}")

async def _analyze_tweets():
    """Helper function to run the analysis asynchronously"""
    # Load tweet data
    tweet_data = TweetData()
    tweets = tweet_data.get_tweets()
    
    # Classify tech tweets
    tech_tweets = await twitter_analyzer.classify_tech_tweets(tweets)
    
    # If no tech tweets found, return error
    if not tech_tweets:
        return {"error": "No technology-related tweets found."}
    
    # Score engagement potential
    scored_tweets = await twitter_analyzer.score_engagement_potential(tech_tweets)
    
    # Find best tweet
    best_tweet = await twitter_analyzer.find_best_tweet(scored_tweets)
    
    # Generate reply
    tweet_reply = await twitter_analyzer.generate_reply(best_tweet)
    
    # Create results dictionary
    results = {
        "best_tweet": {
            "url": best_tweet['url'],
            "post": best_tweet['post'],
            "stats": best_tweet['stats'],
            "engagement_score": best_tweet['engagement_score'].engagement_potential,
            "tech_categories": best_tweet['tech_analysis'].tech_categories
        },
        "generated_reply": {
            "text": tweet_reply.reply_text,
            "tone": tweet_reply.tone,
            "style": tweet_reply.humor_style if hasattr(tweet_reply, 'humor_style') else "",
            "reasoning": tweet_reply.reasoning
        },
        "analysis_summary": {
            "total_tweets": len(tweets),
            "tech_tweets_found": len(tech_tweets),
            "best_score": best_tweet['engagement_score'].engagement_potential
        }
    }
    
    # Save results to file
    with open(ANALYSIS_PATH, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    return results

@app.route('/confirm_reply', methods=['POST'])
def confirm_reply():
    """Confirm and post reply to Twitter"""
    if 'analysis_results' not in session:
        flash('No analysis results found. Please analyze tweets first.', 'error')
        return redirect(url_for('index'))
    
    # Get analysis results from session
    results = session['analysis_results']
    
    # Post reply
    if request.form.get('confirm') == 'yes':
        try:
            tweet_url = results['best_tweet']['url']
            # Get the edited reply if available, otherwise use the original
            reply_text = request.form.get('edited_reply', results['generated_reply']['text'])
            
            # Update the reply text in session for display on confirmation
            results['generated_reply']['text'] = reply_text
            session['analysis_results'] = results
            
            # Post the reply asynchronously
            success = asyncio.run(post_reply_async(tweet_url, reply_text))
            
            if success:
                flash('Reply posted successfully!', 'success')
                return render_template('confirm.html', success=True, results=results)
            else:
                flash('Failed to post reply.', 'error')
                return render_template('confirm.html', success=False, results=results)
        except Exception as e:
            logger.error(f"Error posting reply: {str(e)}")
            flash(f'Error posting reply: {str(e)}', 'error')
            return render_template('confirm.html', success=False, results=results)
    else:
        # User clicked "No, Cancel" - go back to home page
        flash('Reply cancelled. Starting over.', 'info')
        return redirect(url_for('restart'))

@app.route('/restart')
def restart():
    """Clear session and restart the process"""
    session.clear()
    # Optionally delete data.json and analysis_results.json
    return redirect(url_for('index'))

# Custom error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code=404, message="Page not found"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_code=500, message="Internal server error"), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
