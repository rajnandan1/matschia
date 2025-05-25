#!/usr/bin/env python3
"""
Tweet Scraper - Twitter/X Data Collection Tool
This script uses Playwright to collect tweets from Twitter/X timeline.
It fetches tweets, their stats, and comments, then saves them to data.json.
"""
import asyncio
import os
import json
import time
from pathlib import Path
from playwright.async_api import async_playwright

# Use the same directory for state file as in the JS version
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
STORAGE_STATE_PATH = SCRIPT_DIR / "state.json"

print(f"Storage state will be saved to: {STORAGE_STATE_PATH}")

async def main():
    print("🚀 Launching Playwright Chromium...")
    
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
            
            # Set up context options for desktop browser dimensions (14-inch MacBook Pro)
            context_options = {
                "viewport": {"width": 1512, "height": 982},  # 14-inch MacBook Pro dimensions
                "device_scale_factor": 2,  # Retina display
            }
            
            # Load session state if it exists
            if STORAGE_STATE_PATH.exists():
                context_options["storage_state"] = str(STORAGE_STATE_PATH)
                print(f"✅ Attempting to load session state from {STORAGE_STATE_PATH}")
            else:
                print(f"ℹ️ No existing session state file found at {STORAGE_STATE_PATH}. Starting fresh.")
            
            context = await browser.new_context(**context_options)
            page = await context.new_page()
            
            await page.goto("https://x.com/home?lang=en")
            print(f"✅ Page loaded: {await page.title()}")
            
            # Check if login is required (usually needed on first run)
            is_logged_in = await page.evaluate('''() => {
                // Check for elements that would indicate being logged in
                return document.querySelector('div[aria-label="Timeline: Your Home Timeline"]') !== null;
            }''')
            
            if not is_logged_in:
                print("🔑 Waiting for you to log in manually...")
                print("Please log in to Twitter/X in the browser window.")
                print("The script will continue once you're logged in.")
                
                # Wait for the timeline to appear (indication of successful login)
                await page.wait_for_selector('div[aria-label="Timeline: Your Home Timeline"]', timeout=120000)
                
                print("✅ Login detected!")
                
                # Save session state immediately after login
                await context.storage_state(path=str(STORAGE_STATE_PATH))
                print(f"✅ Session state saved to {STORAGE_STATE_PATH} after login")
            
            # Wait until timeline is loaded
            await page.wait_for_selector('div[aria-label="Timeline: Your Home Timeline"]')
            print("✅ Timeline loaded")
            
            # Get the reference to first child only
            timeline = await page.query_selector('div[aria-label="Timeline: Your Home Timeline"] > div')
            
            # Scroll to the bottom of the page
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for a bit to allow new posts to load
            await page.wait_for_timeout(2000)
            
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            await page.wait_for_timeout(4000)
            
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
            
            print(f"✅ User names and post URLs extracted: {posts_urls}")
            
            my_posts = []
            
            # Go to each URL and get the post
            for url in posts_urls:
                await page.goto(url)
                await page.wait_for_selector('[data-testid="tweet"]')
                
                # Check if post text exists
                post_exists = await page.evaluate('''() => {
                    return document.querySelector('[data-testid="tweet"] [data-testid="tweetText"]') !== null;
                }''')
                
                if not post_exists:
                    print(f"❌ Post not found for URL: {url}")
                    continue
                
                # Extract post text
                post = await page.evaluate('''() => {
                    return document.querySelector('[data-testid="tweet"] [data-testid="tweetText"]').innerText;
                }''')
                
                # Scroll down to load more content
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                await page.wait_for_timeout(2000)
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
            
            print(f"✅ Posts extracted: {json.dumps(my_posts, indent=2)}")
            
            # Save collected data to data.json
            with open("data.json", "w", encoding="utf-8") as f:
                json.dump(my_posts, f, indent=2)
            print("✅ Data saved to data.json")
            
            print("🔒 Closing browser...")
            await browser.close()
            print("✅ Browser closed successfully")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            # Ensure browser is closed even if there's an error
            try:
                if 'browser' in locals() and browser:
                    await browser.close()
                    print("✅ Browser closed after error")
            except:
                pass

if __name__ == "__main__":
    asyncio.run(main())
