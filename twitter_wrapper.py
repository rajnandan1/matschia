#!/usr/bin/env python3
"""
Twitter Wrapper Module
This module handles Twitter interactions using Playwright
"""
import os
import json
import asyncio
import logging
from pathlib import Path
from playwright.async_api import async_playwright

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Use the same directory for state file
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
STORAGE_STATE_PATH = SCRIPT_DIR / "state.json"
DATA_PATH = SCRIPT_DIR / "data.json"

async def fetch_tweets_async(scroll_count=3):
    """Fetch tweets from Twitter using Playwright with configurable scroll count"""
    logger.info(f"Starting tweet fetch with {scroll_count} scrolls")
    logger.info(f"Storage state will be loaded from: {STORAGE_STATE_PATH}")
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",  # May help in some environments
                    "--disable-web-security",  # Not recommended for production use
                    "--disable-infobars",  # Prevent infobars
                    "--disable-extensions",  # Disable extensions
                    "--start-maximized",  # Start maximized
                ],
                headless=False,  # Ensure the browser is visible
            )
            
            # Set up context options for desktop browser dimensions
            context_options = {
                "viewport": {"width": 1512, "height": 982},
                "device_scale_factor": 2,
            }
            
            # Load session state if it exists
            if STORAGE_STATE_PATH.exists():
                context_options["storage_state"] = str(STORAGE_STATE_PATH)
                logger.info(f"Loading session state from {STORAGE_STATE_PATH}")
            else:
                logger.info(f"No existing session state found at {STORAGE_STATE_PATH}")
            
            context = await browser.new_context(**context_options)
            page = await context.new_page()
            
            await page.goto("https://x.com/home?lang=en")
            logger.info(f"Page loaded: {await page.title()}")
            
            # Check if login is required (usually needed on first run)
            is_logged_in = await page.evaluate('''() => {
                // Check for elements that would indicate being logged in
                return document.querySelector('div[aria-label="Timeline: Your Home Timeline"]') !== null;
            }''')
            
            if not is_logged_in:
                logger.info("Waiting for user to log in manually...")
                print("Please log in to Twitter/X in the browser window.")
                print("The script will continue once you're logged in.")
                
                # Wait for the timeline to appear (indication of successful login)
                await page.wait_for_selector('div[aria-label="Timeline: Your Home Timeline"]', timeout=120000)
                
                logger.info("Login detected!")
                
                # Save session state immediately after login
                await context.storage_state(path=str(STORAGE_STATE_PATH))
                logger.info(f"Session state saved to {STORAGE_STATE_PATH} after login")
            
            # Wait until timeline is loaded
            await page.wait_for_selector('div[aria-label="Timeline: Your Home Timeline"]')
            logger.info("Timeline loaded")
            
            # Get the reference to first child only
            timeline = await page.query_selector('div[aria-label="Timeline: Your Home Timeline"] > div')
            
            # Scroll based on scroll_count parameter
            logger.info(f"Scrolling {scroll_count} times to load tweets...")
            for i in range(scroll_count):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                logger.info(f"Scroll {i+1}/{scroll_count} completed")
                # Wait for content to load after each scroll
                await page.wait_for_timeout(2000)
            
            # Extract post URLs
            posts_urls = await timeline.evaluate('''() => {
                let postsURLs = [];
                document.querySelectorAll('[data-testid="User-Name"]').forEach((el) => {
                    const statusLinks = el.querySelectorAll('a[href*="/status/"]');
                    statusLinks.forEach((link) => {
                        postsURLs.push(link.href);
                    });
                });
                return postsURLs;
            }''')
            
            logger.info(f"Extracted {len(posts_urls)} post URLs")
            
            my_posts = []
            
            # Go to each URL and get the post
            for idx, url in enumerate(posts_urls):
                logger.info(f"Processing tweet {idx+1}/{len(posts_urls)}: {url}")
                await page.goto(url)
                await page.wait_for_selector('[data-testid="tweet"]')
                
                # Check if post text exists
                post_exists = await page.evaluate('''() => {
                    return document.querySelector('[data-testid="tweet"] [data-testid="tweetText"]') !== null;
                }''')
                
                if not post_exists:
                    logger.warning(f"Post not found for URL: {url}")
                    continue
                
                # Extract post text
                post = await page.evaluate('''() => {
                    return document.querySelector('[data-testid="tweet"] [data-testid="tweetText"]').innerText;
                }''')
                
                # Scroll down to load more content
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                await page.wait_for_timeout(2000)
                
                # Get stats
                stats = await page.evaluate('''() => {
                    return document.querySelector('[data-testid="tweet"] div[aria-label*="like"]').getAttribute("aria-label");
                }''')
                
                # Get comments
                comments = await page.evaluate('''() => {
                    let els = document.querySelectorAll('article[data-testid="tweet"] div[data-testid="tweetText"]');
                    let comments = [];
                    els.forEach((el) => {
                        comments.push(el.innerText);
                    });
                    return comments;
                }''')
                
                my_posts.append({
                    "url": url,
                    "post": post,
                    "stats": stats,
                    "comments": comments,
                })
            
            logger.info(f"Extracted {len(my_posts)} posts")
            
            # Save collected data to data.json
            with open(DATA_PATH, "w", encoding="utf-8") as f:
                json.dump(my_posts, f, indent=2)
            logger.info(f"Data saved to {DATA_PATH}")
            
            logger.info("Closing browser...")
            await browser.close()
            logger.info("Browser closed successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            # Ensure browser is closed even if there's an error
            try:
                if 'browser' in locals() and browser:
                    await browser.close()
                    logger.info("Browser closed after error")
            except:
                pass
            raise e

if __name__ == "__main__":
    # If run directly, fetch 3 scrolls worth of tweets
    asyncio.run(fetch_tweets_async(3))
