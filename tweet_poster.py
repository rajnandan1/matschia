#!/usr/bin/env python3
"""
Tweet Reply Module
This module handles posting replies to Twitter/X tweets using Playwright
"""
import os
import logging
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Use the same directory for state file
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
STORAGE_STATE_PATH = SCRIPT_DIR / "state.json"
SCREENSHOT_PATH = SCRIPT_DIR / "reply_screenshot.png"

async def post_reply_async(tweet_url, reply_text):
    """Post a reply to a specified tweet URL with the given text"""
    logger.info(f"Preparing to reply to tweet: {tweet_url}")
    logger.info(f"Reply text: {reply_text}")
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-infobars",
                    "--disable-extensions",
                    "--start-maximized",
                ],
                headless=False,  # Ensure the browser is visible
            )
            
            # Set up context options
            context_options = {
                "viewport": {"width": 1512, "height": 982},
                "device_scale_factor": 2,
            }
            
            # Load session state if it exists
            if STORAGE_STATE_PATH.exists():
                context_options["storage_state"] = str(STORAGE_STATE_PATH)
                logger.info(f"Loading session state from {STORAGE_STATE_PATH}")
            else:
                logger.error(f"No session state file found at {STORAGE_STATE_PATH}")
                await browser.close()
                return False
            
            context = await browser.new_context(**context_options)
            page = await context.new_page()
            
            # Go to the tweet
            logger.info(f"Navigating to tweet: {tweet_url}")
            await page.goto(tweet_url)
            
            # Wait for the tweet to load
            logger.info("Waiting for tweet to load...")
            await page.wait_for_selector('[data-testid="tweet"]')
            
            # Click on the reply button
            logger.info("Clicking reply button...")
            reply_button = await page.query_selector('[data-testid="reply"]')
            if not reply_button:
                logger.error("Couldn't find reply button")
                await browser.close()
                return False
            
            await reply_button.click()
            
            # Wait for reply text field to appear
            logger.info("Waiting for reply text field...")
            await page.wait_for_selector('[data-testid="tweetTextarea_0"]')
            
            # Type the reply
            logger.info(f"Typing reply: {reply_text}")
            await page.fill('[data-testid="tweetTextarea_0"]', reply_text)
            
            # Wait a moment before clicking reply
            await page.wait_for_timeout(1000)
            
            # Click the reply button to submit
            logger.info("Submitting reply...")
            reply_submit_button = await page.query_selector('[data-testid="tweetButton"]')
            if not reply_submit_button:
                logger.error("Couldn't find reply submit button")
                await browser.close()
                return False
                
            await reply_submit_button.click()
            
            # Wait for reply to be posted
            logger.info("Waiting for reply to be posted...")
            try:
                # Wait for some confirmation element or timeout
                await page.wait_for_timeout(5000)
                
                # Check if we're back on the tweet page (indicating success)
                is_back_on_tweet = await page.evaluate('''() => {
                    return document.querySelector('[data-testid="cellInnerDiv"] article') !== null;
                }''')
                
                if is_back_on_tweet:
                    logger.info("Reply successfully posted!")
                else:
                    logger.warning("Unable to confirm if reply was posted.")
            except Exception as e:
                logger.error(f"Error waiting for reply confirmation: {str(e)}")
            
            # Save a screenshot
            await page.screenshot(path=str(SCREENSHOT_PATH))
            logger.info(f"Screenshot saved to {SCREENSHOT_PATH}")
            
            # Wait a moment before closing
            logger.info("Waiting 3 seconds before closing browser...")
            await page.wait_for_timeout(3000)
            
            # Close the browser
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
            return False

if __name__ == "__main__":
    # If run directly, test with a sample URL and reply
    asyncio.run(post_reply_async(
        "https://x.com/example/status/123456789",
        "This is a test reply from the Twitter Reply Bot."
    ))
