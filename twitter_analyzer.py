import json
import os
import asyncio
import random
from typing import Dict, List, Any
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from agents import Agent, Runner, trace
from agents.tool import WebSearchTool

# Load environment variables
load_dotenv()

class TweetAnalysis(BaseModel):
    is_technology_related: bool = Field(description="Whether the tweet is technology-related")
    confidence_score: float = Field(description="Confidence score between 0 and 1")
    reasoning: str = Field(description="Reasoning for the classification")
    tech_categories: List[str] = Field(description="List of technology categories the tweet belongs to")

class EngagementScore(BaseModel):
    engagement_potential: float = Field(description="Engagement potential score between 0 and 10")
    reasoning: str = Field(description="Reasoning for the engagement score")
    factors: List[str] = Field(description="Factors that contribute to engagement potential")

class TweetReply(BaseModel):
    reply_text: str = Field(description="The natural, human-like reply text")
    tone: str = Field(description="Whether the reply agrees or disagrees with the tweet")
    reasoning: str = Field(description="Reasoning behind the reply")
    humor_style: str = Field(description="The conversational style used in the reply")
    style: str = Field(description="The conversational style used in the reply")

class TweetData:
    def __init__(self, data_file: str = "data.json"):
        with open(data_file, 'r', encoding='utf-8') as f:
            self.tweets = json.load(f)
    
    def get_tweets(self) -> List[Dict[str, Any]]:
        return self.tweets

class TwitterAnalyzer:
    def __init__(self):
        # Web Search Tool for fetching tech news
        self.web_search_tool = WebSearchTool(
            search_context_size="medium"  # Options: "low", "medium", "high"
        )
        
        # Tech Classification Agent
        self.tech_classifier = Agent(
            name="Tech Tweet Classifier",
            instructions="""You are an expert at identifying technology-related tweets. 
            Analyze tweets to determine if they are technology-related.
            
            Consider these as technology-related:
            - AI/ML, software development, programming, hardware
            - Startups, VC funding, entrepreneurship in tech, founder stories
            - Tech companies, coding, apps, websites, digital products
            - Developer tools, frameworks, APIs, cloud services
            - Tech industry news, startup acquisitions, product launches, technical discussions
            - Startup metrics, growth strategies, and scaling tech businesses
            
            Rate confidence from 0-1 and categorize the specific tech areas.
            Be strict - only classify as tech if it's clearly technology focused.""",
            output_type=TweetAnalysis,
            model="gpt-4o"
        )
        
        # Engagement Scoring Agent
        self.engagement_scorer = Agent(
            name="Engagement Potential Scorer",
            instructions="""You are an expert at predicting tweet engagement potential.
            
            Analyze technology tweets and score their engagement potential (0-10).
            
            High engagement factors:
            - Controversial or debatable topics about tech and startups
            - Popular tech personalities, founders, or startup companies mentioned
            - Current trending technologies (AI, React, etc.) and startup trends
            - Questions or discussions that invite responses from tech/startup community
            - Strong opinions or hot takes on tech products, startup funding, or growth
            - Relatable developer problems/experiences or founder stories
            - Industry drama, startup acquisitions, or important tech announcements
            
            Low engagement factors:
            - Generic statements
            - Old news
            - Very niche technical details
            - No clear discussion points
            
            Consider the existing stats, comments, and content quality.""",
            output_type=EngagementScore,
            model="gpt-4o"
        )
        
        # Post Generator Agent
        self.post_generator = Agent(
            name="Tech Thought Leadership Post Generator",
            instructions="""You are a knowledgeable tech person who writes insightful standalone Twitter posts in the style of tech/startup Twitter influencers like @paulg, @naval, @chris__cox, @dhh, @karpathy, @tobi, @gaganbiyani.
            
            Your personality:
            - Write short, insightful statements about tech, startups, and entrepreneurship
            - Use concise, punchy sentences with bold, opinionated takes on startup building and tech trends
            - Be straightforward and confident in your assertions about business and technology
            - Focus on practical wisdom and real-world observations from startup ecosystems
            - Regularly offer contrarian and thought-provoking takes that challenge conventional wisdom
            - Sound like a seasoned founder/investor with deep industry knowledge and startup expertise
            - Take specific stances on recent tech news, trends, and controversial topics
            - Don't be afraid to be polarizing - the best tweets make people either strongly agree or disagree
            
            Style guidelines:
            - Create highly engaging original content based on analyzed tech topics and recent tech news
            - Aim for virality by making specific predictions or bold claims about technology's future
            - DO NOT use emojis
            - DO NOT use hashtags
            - Express strong opinions with confidence and assertiveness
            - Use short sentences for impact with occasional mic-drop statements
            - DO NOT use excessive punctuation
            - Focus on specific insights rather than general platitudes
            - Sound authentic, authoritative, and unapologetically opinionated
            - Reference specific technologies, companies, or trends rather than vague concepts
            
            Always be respectful while sharing provocative opinions on tech and startup trends.""",
            output_type=TweetReply,
            model="gpt-4o"
        )
        
        # Reply Generator Agent
        self.reply_generator = Agent(
            name="Human Tech Reply Generator",
            instructions="""You are a knowledgeable tech person who writes natural, human-like Twitter replies in the style of tech/startup Twitter influencers like @paulg, @naval, @chris__cox, @dhh, @karpathy, @tobi, @gaganbiyani, @shl, @girdley, @csallen, @eladgil, @packyM, @mubashariqbal, @bentossell, @nikitabier, @suhail, @hnshah.
            
            Your personality:
            - Write short, insightful statements about tech, startups, and entrepreneurship
            - Use concise, punchy sentences with clear opinions on startup building and tech trends
            - Be straightforward and confident in your assertions about business and technology
            - Focus on practical wisdom and real-world observations from startup ecosystems
            - Occasionally use counterintuitive takes that make people think about founding, scaling, or funding
            - Sound like a seasoned founder/investor with deep industry knowledge and startup expertise
            
            Style guidelines:
            - DO NOT end tweets with questions
            - DO NOT use emojis
            - DO NOT use hashtags
            - Keep opinions clear and direct
            - Use short sentences for impact
            - DO NOT use excessive punctuation
            - Write as if you're talking to a colleague
            - Focus on genuine insights or questions
            - Be conversational and authentic
            
            Always be respectful and aim to continue the conversation naturally.""",
            output_type=TweetReply,
            model="gpt-4o"
        )

    async def classify_tech_tweets(self, tweets: List[Dict]) -> List[Dict]:
        """Classify tweets as technology-related or not"""
        tech_tweets = []
        
        for tweet in tweets:
            # Prepare tweet content for analysis
            tweet_content = f"""
            Tweet: {tweet['post']}
            Stats: {tweet['stats']}
            Sample Comments: {' | '.join(tweet['comments'][:5])}
            """
            
            try:
                # Run tech classification agent with tracing
                with trace(workflow_name="Tech_Classification"):
                    result = await Runner.run(self.tech_classifier, tweet_content)
                    
                # Get the structured output as a TweetAnalysis model
                analysis = result.final_output
                
                if analysis.is_technology_related and analysis.confidence_score >= 0.7:
                    tweet_with_analysis = tweet.copy()
                    tweet_with_analysis['tech_analysis'] = analysis
                    tech_tweets.append(tweet_with_analysis)
                    print(f"✅ Tech tweet found: {tweet['post'][:100]}...")
                    print(f"   Categories: {analysis.tech_categories}")
                    print(f"   Confidence: {analysis.confidence_score:.2f}")
                else:
                    print(f"❌ Not tech-related: {tweet['post'][:100]}...")
                    
            except Exception as e:
                print(f"Error classifying tweet: {e}")
                print(f"Error details: {str(e)}")
                continue
        
        return tech_tweets

    async def score_engagement_potential(self, tech_tweets: List[Dict]) -> List[Dict]:
        """Score engagement potential for tech tweets"""
        scored_tweets = []
        
        for tweet in tech_tweets:
            tweet_content = f"""
            Tweet: {tweet['post']}
            Stats: {tweet['stats']}
            Comments: {' | '.join(tweet['comments'][:10])}
            Tech Categories: {tweet['tech_analysis'].tech_categories}
            Tech Reasoning: {tweet['tech_analysis'].reasoning}
            """
            
            try:
                # Run engagement scoring agent with tracing
                with trace(workflow_name="Engagement_Scoring"):
                    result = await Runner.run(self.engagement_scorer, tweet_content)
                
                # Get the structured output as an EngagementScore model
                engagement = result.final_output
                
                tweet['engagement_score'] = engagement
                scored_tweets.append(tweet)
                
                print(f"📊 Engagement score: {engagement.engagement_potential:.1f}/10")
                print(f"   Factors: {engagement.factors}")
                
            except Exception as e:
                print(f"Error scoring engagement: {e}")
                print(f"Error details: {str(e)}")
                continue
        
        return scored_tweets

    async def find_best_tweet(self, scored_tweets: List[Dict]) -> Dict:
        """Find the tweet with highest engagement potential"""
        if not scored_tweets:
            raise ValueError("No tech tweets found to analyze")
        
        best_tweet = max(scored_tweets, key=lambda t: t['engagement_score'].engagement_potential)
        
        print(f"\n🏆 BEST TWEET FOR ENGAGEMENT:")
        print(f"Tweet: {best_tweet['post']}")
        print(f"Score: {best_tweet['engagement_score'].engagement_potential:.1f}/10")
        print(f"URL: {best_tweet['url']}")
        print(f"Stats: {best_tweet['stats']}")
        
        return best_tweet

    async def generate_reply(self, best_tweet: Dict) -> TweetReply:
        """Generate a natural, human-like reply to the best tweet"""
        tweet_context = f"""
        Original Tweet: {best_tweet['post']}
        Tweet Stats: {best_tweet['stats']}
        Tech Categories: {best_tweet['tech_analysis'].tech_categories}
        Engagement Factors: {best_tweet['engagement_score'].factors}
        Sample Comments: {' | '.join(best_tweet['comments'][:5])}
        
        Generate a natural, conversational reply that a tech-savvy person would write.
        The reply should sound authentic and continue the conversation naturally.
        """
        
        with trace(workflow_name="Reply_Generation"):
            result = await Runner.run(self.reply_generator, tweet_context)
        
        return result.final_output

    async def get_recent_tech_news(self) -> List[Dict]:
        """Get recent tech news and trending topics in the tech world using web search"""
        print("🔍 Searching the web for latest tech news...")
        
        # Topics to search for
        search_topics = [
            "latest AI technology news",
            "tech startup funding news today",
            "recent tech layoffs",
            "latest tech regulation news",
            "controversial tech trends",
            "big tech company announcements",
            "open source technology news",
            "cybersecurity breaches recent"
        ]
        
        # Select a few random topics to search for
        selected_topics = random.sample(search_topics, min(3, len(search_topics)))
        recent_tech_news = []
        
        # Create a tech analyzer Agent to categorize web search results
        tech_news_analyzer = Agent(
            name="Tech News Analyzer",
            instructions="""Analyze this tech news headline and provide structured information about it.
            Extract the main topic, categorize it by tech domain, assess its sentiment (positive/negative/neutral),
            and rate the potential controversy level (low/medium/high).
            """,
            model="gpt-4o"
        )
        
        # Search for each topic and process results
        for topic in selected_topics:
            try:
                print(f"  Searching for: {topic}")
                
                # Prepare the search context
                search_context = f"""
                Find the most recent and significant tech news about {topic}.
                Focus on headlines from reputable tech news sources published in the last week.
                Look for specific announcements, product launches, funding rounds, or industry trends.
                """
                
                # Use the WebSearchTool via an agent to search the web
                with trace(workflow_name=f"Web_Search_{topic}"):
                    search_agent = Agent(
                        name="Web Search Agent",
                        instructions=search_context,
                        tools=[self.web_search_tool]
                    )
                    search_result = await Runner.run(search_agent, f"Find the latest news on {topic}")
                
                # Extract headlines from the search results
                raw_results = search_result.final_output
                
                # Process each headline to categorize it
                headlines = self._extract_headlines_from_search(raw_results)
                
                for headline in headlines[:2]:  # Process top 2 headlines per topic
                    analysis_prompt = f"Analyze this tech news headline: '{headline}'"
                    
                    with trace(workflow_name="News_Analysis"):
                        analysis_result = await Runner.run(tech_news_analyzer, analysis_prompt)
                    
                    # Extract structured information
                    analysis = analysis_result.final_output
                    
                    # Create a news item with the analyzed data
                    news_item = {
                        "title": headline,
                        "topic": self._extract_field(analysis, "topic", "Technology"),
                        "sentiment": self._extract_field(analysis, "sentiment", "neutral"),
                        "controversy_level": self._extract_field(analysis, "controversy_level", "medium")
                    }
                    
                    recent_tech_news.append(news_item)
                    print(f"  ✅ Found: {headline}")
                
            except Exception as e:
                print(f"  ❌ Error searching for {topic}: {e}")
                continue
        
        # If web search failed or returned no results, use fallback simulated news
        if not recent_tech_news:
            print("  ⚠️ Web search returned no results, using fallback news data")
            recent_tech_news = self._get_fallback_tech_news()
        
        return recent_tech_news
    
    def _extract_headlines_from_search(self, search_result: str) -> List[str]:
        """Extract headlines from search results text"""
        headlines = []
        
        # Try to extract headlines from the search results
        lines = search_result.strip().split('\n')
        for line in lines:
            line = line.strip()
            # Look for lines that could be headlines (not too short, not too long)
            if 30 <= len(line) <= 150 and not line.startswith("http") and not line.startswith("www."):
                # Remove common prefixes and quotes
                clean_line = line.strip('"\'')
                if clean_line:
                    headlines.append(clean_line)
        
        # If we failed to extract headlines, try to find sentences that sound like headlines
        if not headlines:
            import re
            # Look for sentences that might be news headlines
            headline_patterns = [
                r'[A-Z][^.!?]*launches[^.!?]*',
                r'[A-Z][^.!?]*announces[^.!?]*',
                r'[A-Z][^.!?]*reveals[^.!?]*',
                r'[A-Z][^.!?]*releases[^.!?]*',
                r'[A-Z][^.!?]*introduces[^.!?]*',
                r'[A-Z][^.!?]*acquires[^.!?]*',
                r'[A-Z][^.!?]*plans to[^.!?]*',
            ]
            
            for pattern in headline_patterns:
                matches = re.findall(pattern, search_result)
                headlines.extend(matches)
        
        # Ensure headlines are unique
        unique_headlines = list(set(headlines))
        
        # If still no headlines, create generic ones from the search topic
        if not unique_headlines:
            unique_headlines = ["Recent developments in " + topic for topic in [
                "artificial intelligence", 
                "tech startups", 
                "cybersecurity"
            ]]
        
        return unique_headlines
    
    def _extract_field(self, analysis: str, field_name: str, default_value: str) -> str:
        """Extract a specific field from the analysis text"""
        try:
            # Try to find the field in the analysis text
            import re
            pattern = rf"{field_name}\s*[:=]\s*([a-zA-Z0-9 /-]+)"
            match = re.search(pattern, analysis.lower())
            if match:
                return match.group(1).strip()
            return default_value
        except:
            return default_value
    
    def _get_fallback_tech_news(self) -> List[Dict]:
        """Provide fallback tech news when web search fails"""
        fallback_news = [
            {
                "title": "OpenAI releases GPT-5 with enhanced multimodal capabilities",
                "topic": "AI",
                "sentiment": "positive",
                "controversy_level": "medium"
            },
            {
                "title": "Tech layoffs continue as major companies cut costs amid economic uncertainty",
                "topic": "Tech Industry",
                "sentiment": "negative",
                "controversy_level": "high"
            },
            {
                "title": "Apple unveils new AR headset with mixed reality features",
                "topic": "Hardware",
                "sentiment": "positive",
                "controversy_level": "medium"
            },
            {
                "title": "Startups raising at lower valuations as venture funding tightens",
                "topic": "Startups",
                "sentiment": "negative",
                "controversy_level": "medium"
            }
        ]
        
        # Randomly select a subset of news items to focus on
        selected_news = random.sample(fallback_news, min(4, len(fallback_news)))
        
        return selected_news
        
    async def generate_new_post(self, tech_tweets: List[Dict]) -> TweetReply:
        """Generate an engaging standalone post based on analyzed tech tweets and recent news"""
        # Extract tech categories and topics from all analyzed tweets
        categories = []
        topics = []
        for tweet in tech_tweets:
            if 'tech_analysis' in tweet and hasattr(tweet['tech_analysis'], 'tech_categories'):
                categories.extend(tweet['tech_analysis'].tech_categories)
        
        # Get unique categories
        unique_categories = list(set(categories))
        
        # Get recent tech news using web search
        recent_news = await self.get_recent_tech_news()
        
        # Select high controversy topics for more opinionated content
        controversial_topics = [news for news in recent_news if news["controversy_level"] in ["medium", "high"]]
        
        # Create context for post generation with both categories and recent news
        post_context = f"""
        Generate an engaging, opinionated standalone tweet about technology based on these insights:
        
        Trending Tech Categories: {', '.join(unique_categories[:7])}
        
        Recent Tech News:
        {', '.join([f"{news['title']} ({news['sentiment']} sentiment)" for news in recent_news])}
        
        Controversial Topics to Consider:
        {', '.join([f"{news['title']} ({news['topic']})" for news in controversial_topics])}
        
        Instructions:
        1. Create a thought-provoking, insightful post that would resonate with the tech community.
        2. Take a SPECIFIC, OPINIONATED stance on one of the recent news topics or tech categories.
        3. Make a bold prediction or contrarian observation that challenges conventional wisdom.
        4. Be specific rather than general - reference actual technologies, trends, or companies.
        5. The post should be original and provocative enough to generate strong reactions.
        6. Focus on ONE specific topic rather than making general statements about the tech industry.
        """
        
        with trace(workflow_name="Post_Generation"):
            result = await Runner.run(self.post_generator, post_context)
        
        return result.final_output

async def main():
    print("🤖 Starting Twitter Analysis with OpenAI Agents...")
    print("=" * 60)
    
    # Initialize analyzer and load tweets
    analyzer = TwitterAnalyzer()
    tweet_data = TweetData()
    tweets = tweet_data.get_tweets()
    
    print(f"📁 Loaded {len(tweets)} tweets from data.json")
    print("\n🔍 Step 1: Classifying technology-related tweets...")
    
    # Use an overall trace for the entire workflow
    with trace(workflow_name="Tweet_Analysis"):
        # Step 1: Classify tech tweets
        tech_tweets = await analyzer.classify_tech_tweets(tweets)
        print(f"\n✅ Found {len(tech_tweets)} technology-related tweets")
        
        if not tech_tweets:
            print("No technology tweets found. Exiting.")
            return
        
        # Step 2: Score engagement potential
        print(f"\n📊 Step 2: Scoring engagement potential...")
        scored_tweets = await analyzer.score_engagement_potential(tech_tweets)
        
        # Step 3: Find best tweet
        print(f"\n🎯 Step 3: Finding best tweet for engagement...")
        best_tweet = await analyzer.find_best_tweet(scored_tweets)
        
        # Step 4: Generate human-like reply
        print(f"\n✍️  Step 4: Generating human-like reply...")
        tweet_reply = await analyzer.generate_reply(best_tweet)
        
        # Step 5: Generate standalone post
        print(f"\n📝 Step 5: Generating standalone post...")
        tweet_post = await analyzer.generate_new_post(scored_tweets)
    
    # Display results
    print("\n" + "=" * 60)
    print("🎉 FINAL RESULTS")
    print("=" * 60)
    
    print(f"\n📝 ORIGINAL TWEET:")
    print(f"   {best_tweet['post']}")
    print(f"   URL: {best_tweet['url']}")
    print(f"   Stats: {best_tweet['stats']}")
    
    print(f"\n🎯 ENGAGEMENT ANALYSIS:")
    print(f"   Score: {best_tweet['engagement_score'].engagement_potential:.1f}/10")
    print(f"   Reasoning: {best_tweet['engagement_score'].reasoning}")
    
    print(f"\n💬 GENERATED REPLY:")
    print(f"   {tweet_reply.reply_text}")
    print(f"   Tone: {tweet_reply.tone}")
    print(f"   Style: {tweet_reply.humor_style}")
    print(f"   Reasoning: {tweet_reply.reasoning}")
    
    print(f"\n📢 GENERATED POST:")
    print(f"   {tweet_post.reply_text}")
    print(f"   Tone: {tweet_post.tone}")
    print(f"   Style: {tweet_post.humor_style}")
    print(f"   Reasoning: {tweet_post.reasoning}")
    
    # Save results
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
            "style": tweet_reply.humor_style,
            "reasoning": tweet_reply.reasoning
        },
        "generated_post": {
            "text": tweet_post.reply_text,
            "tone": tweet_post.tone,
            "style": tweet_post.humor_style,
            "reasoning": tweet_post.reasoning
        },
        "analysis_summary": {
            "total_tweets": len(tweets),
            "tech_tweets_found": len(tech_tweets),
            "best_score": best_tweet['engagement_score'].engagement_potential
        }
    }
    
    with open("analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Results saved to analysis_results.json")
    print("\n🚀 Analysis complete! Ready to engage!")

if __name__ == "__main__":
    asyncio.run(main())
