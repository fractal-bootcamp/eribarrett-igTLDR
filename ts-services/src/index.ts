import express from 'express';
import path from 'path';
import { PostScorer } from './services/postScorer.js';
import dataLoader from './services/dataLoader.js';
import postPrioritizer, { PriorityLevel } from './services/postPrioritizer.js';
import contentCategorizer from './services/contentCategorizer.js';
import getTopDailyPosts from './scripts/topDailyPosts.js';
import { generatePostSummaries } from './services/openAiService.js';
import { FileUtils, Paths } from './services/utils.js';

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(express.json());

// Helper to create simplified post data
function simplifyPost(scoredPost: any, options: { truncateCaption?: boolean, summarize?: boolean } = {}) {
    const { post, score, raw, priority } = scoredPost;

    // Default options
    const opts = {
        truncateCaption: false,
        summarize: false,
        ...options
    };

    // Generate AI summary for caption if requested
    let captionSummary = null;
    if (opts.summarize && post.caption && post.caption.length > 100) {
        // Very simple summarization logic - could be replaced with a proper AI solution
        captionSummary = post.caption.substring(0, 100) + "...";
    }

    return {
        id: post.postId,
        username: raw.user.username,
        isCloseFriend: post.isCloseFriend,
        isVerified: post.isVerified,
        caption: opts.truncateCaption ? (post.caption?.substring(0, 200) || '') : post.caption,
        captionSummary,
        hasEvent: post.hasEventIndicators || false,
        eventKeywords: post.eventKeywords || [],
        score: score.finalScore,
        priority: priority?.level || 'unknown',
        priorityReason: priority?.reason || '',
        mediaType: raw.media_type,
        url: `https://instagram.com/p/${raw.shortcode}`,
        timestamp: post.createdAt
    };
}

// Full detailed data endpoint
app.get('/api/feed/scored', (req, res) => {
    try {
        // Load the latest feed data
        const rawPosts = dataLoader.loadLatestDirectFeed();

        // Get unique usernames to check if they're close friends
        const usernames = [...new Set(rawPosts.map(post => post.user.username))];
        const closeFriendUsernames: string[] = [];

        // For each username, try to load close friends data
        for (const username of usernames) {
            const closeFriends = dataLoader.getCloseFriends(username);
            closeFriendUsernames.push(...closeFriends);
        }

        // Convert raw posts to our Post format
        const posts = rawPosts.map(rawPost =>
            dataLoader.convertToPost(rawPost, closeFriendUsernames)
        );

        // Score all posts
        const scorer = new PostScorer();
        const scoredPosts = posts.map((post, index) => {
            const scoreResult = scorer.scorePost(post);
            const priorityResult = postPrioritizer.prioritize(post, scoreResult);

            return {
                post,
                score: scoreResult,
                raw: rawPosts[index], // Include original raw data
                priority: priorityResult
            };
        });

        // Sort by score (highest first)
        scoredPosts.sort((a, b) => b.score.finalScore - a.score.finalScore);

        res.json({
            count: scoredPosts.length,
            posts: scoredPosts
        });
    } catch (error: any) {
        console.error('Error in /api/feed/scored:', error);
        res.status(500).json({ error: error.message });
    }
});

// Simplified data endpoint
app.get('/api/feed/simple', (req, res) => {
    try {
        // Load the latest feed data
        const rawPosts = dataLoader.loadLatestDirectFeed();

        // Get unique usernames to check if they're close friends
        const usernames = [...new Set(rawPosts.map(post => post.user.username))];
        const closeFriendUsernames: string[] = [];

        // For each username, try to load close friends data
        for (const username of usernames) {
            const closeFriends = dataLoader.getCloseFriends(username);
            closeFriendUsernames.push(...closeFriends);
        }

        // Convert raw posts to our Post format
        const posts = rawPosts.map(rawPost =>
            dataLoader.convertToPost(rawPost, closeFriendUsernames)
        );

        // Score all posts
        const scorer = new PostScorer();
        const scoredPosts = posts.map((post, index) => {
            const scoreResult = scorer.scorePost(post);
            const priorityResult = postPrioritizer.prioritize(post, scoreResult);

            return {
                post,
                score: scoreResult,
                raw: rawPosts[index],
                priority: priorityResult
            };
        });

        // Sort by score (highest first)
        scoredPosts.sort((a, b) => b.score.finalScore - a.score.finalScore);

        // Get query parameters
        const truncate = req.query.truncate === 'true';
        const summarize = req.query.summarize === 'true';

        // Simplify the posts data
        const simplifiedPosts = scoredPosts.map(post =>
            simplifyPost(post, { truncateCaption: truncate, summarize })
        );

        res.json({
            count: simplifiedPosts.length,
            posts: simplifiedPosts
        });
    } catch (error: any) {
        console.error('Error in /api/feed/simple:', error);
        res.status(500).json({ error: error.message });
    }
});

// Add endpoint to get simplified event posts only
app.get('/api/feed/events/simple', (req, res) => {
    try {
        // Load the latest feed data
        const rawPosts = dataLoader.loadLatestDirectFeed();

        // Get unique usernames to check if they're close friends
        const usernames = [...new Set(rawPosts.map(post => post.user.username))];
        const closeFriendUsernames: string[] = [];

        // For each username, try to load close friends data
        for (const username of usernames) {
            const closeFriends = dataLoader.getCloseFriends(username);
            closeFriendUsernames.push(...closeFriends);
        }

        // Convert raw posts to our Post format
        const posts = rawPosts.map(rawPost =>
            dataLoader.convertToPost(rawPost, closeFriendUsernames)
        );

        // Score all posts
        const scorer = new PostScorer();
        const scoredPosts = posts.map((post, index) => {
            const scoreResult = scorer.scorePost(post);
            const priorityResult = postPrioritizer.prioritize(post, scoreResult);

            return {
                post,
                score: scoreResult,
                raw: rawPosts[index],
                priority: priorityResult
            };
        });

        // Filter to only include posts with event indicators
        const eventPosts = scoredPosts.filter(item => item.post.hasEventIndicators);

        // Sort by score (highest first)
        eventPosts.sort((a, b) => b.score.finalScore - a.score.finalScore);

        // Get query parameters
        const truncate = req.query.truncate === 'true';
        const summarize = req.query.summarize === 'true';

        // Simplify the posts data
        const simplifiedPosts = eventPosts.map(post =>
            simplifyPost(post, { truncateCaption: truncate, summarize })
        );

        res.json({
            count: simplifiedPosts.length,
            posts: simplifiedPosts
        });
    } catch (error: any) {
        console.error('Error in /api/feed/events/simple:', error);
        res.status(500).json({ error: error.message });
    }
});

// Original event endpoint
app.get('/api/feed/events', (req, res) => {
    try {
        // Load the latest feed data
        const rawPosts = dataLoader.loadLatestDirectFeed();

        // Get unique usernames to check if they're close friends
        const usernames = [...new Set(rawPosts.map(post => post.user.username))];
        const closeFriendUsernames: string[] = [];

        // For each username, try to load close friends data
        for (const username of usernames) {
            const closeFriends = dataLoader.getCloseFriends(username);
            closeFriendUsernames.push(...closeFriends);
        }

        // Convert raw posts to our Post format
        const posts = rawPosts.map(rawPost =>
            dataLoader.convertToPost(rawPost, closeFriendUsernames)
        );

        // Score all posts
        const scorer = new PostScorer();
        const scoredPosts = posts.map((post, index) => {
            const scoreResult = scorer.scorePost(post);
            const priorityResult = postPrioritizer.prioritize(post, scoreResult);

            return {
                post,
                score: scoreResult,
                raw: rawPosts[index],
                priority: priorityResult
            };
        });

        // Filter to only include posts with event indicators
        const eventPosts = scoredPosts.filter(item => item.post.hasEventIndicators);

        // Sort by score (highest first)
        eventPosts.sort((a, b) => b.score.finalScore - a.score.finalScore);

        res.json({
            count: eventPosts.length,
            posts: eventPosts
        });
    } catch (error: any) {
        console.error('Error in /api/feed/events:', error);
        res.status(500).json({ error: error.message });
    }
});

// Add endpoint to get posts by priority level
app.get('/api/feed/priority/:level', (req, res) => {
    try {
        const priorityLevel = req.params.level.toLowerCase();

        // Validate priority level
        if (!Object.values(PriorityLevel).includes(priorityLevel as PriorityLevel)) {
            return res.status(400).json({
                error: `Invalid priority level. Must be one of: ${Object.values(PriorityLevel).join(', ')}`
            });
        }

        // Load the latest feed data
        const rawPosts = dataLoader.loadLatestDirectFeed();

        // Get unique usernames to check if they're close friends
        const usernames = [...new Set(rawPosts.map(post => post.user.username))];
        const closeFriendUsernames: string[] = [];

        // For each username, try to load close friends data
        for (const username of usernames) {
            const closeFriends = dataLoader.getCloseFriends(username);
            closeFriendUsernames.push(...closeFriends);
        }

        // Convert raw posts to our Post format
        const posts = rawPosts.map(rawPost =>
            dataLoader.convertToPost(rawPost, closeFriendUsernames)
        );

        // Score all posts
        const scorer = new PostScorer();
        const scoredPosts = posts.map((post, index) => {
            const scoreResult = scorer.scorePost(post);
            const priorityResult = postPrioritizer.prioritize(post, scoreResult);

            return {
                post,
                score: scoreResult,
                raw: rawPosts[index],
                priority: priorityResult
            };
        });

        // Filter by priority level
        const filteredPosts = scoredPosts.filter(
            item => item.priority.level === priorityLevel
        );

        // Sort by score (highest first)
        filteredPosts.sort((a, b) => b.score.finalScore - a.score.finalScore);

        // Return simplified posts
        const simplifiedPosts = filteredPosts.map(item => simplifyPost(item, { truncateCaption: false }));

        res.json({
            count: simplifiedPosts.length,
            priority: priorityLevel,
            posts: simplifiedPosts
        });
    } catch (error: any) {
        console.error(`Error in /api/feed/priority/:level: ${error}`);
        res.status(500).json({ error: error.message });
    }
});

// Add endpoint to get top daily posts with content categorization
app.get('/api/feed/top-daily', async (req, res) => {
    try {
        const count = req.query.count ? parseInt(req.query.count as string) : 5;
        const topPosts = await getTopDailyPosts(count);

        res.json({
            date: new Date().toISOString(),
            count: topPosts.length,
            posts: topPosts
        });
    } catch (error: any) {
        console.error(`Error in /api/feed/top-daily: ${error}`);
        res.status(500).json({ error: error.message });
    }
});

// Add endpoint to categorize an individual post by content type
app.post('/api/categorize', (req, res) => {
    try {
        // Validate required fields
        const { caption, mediaType, hasEventIndicators } = req.body;
        if (!caption) {
            return res.status(400).json({ error: 'Caption is required' });
        }

        // Categorize the post
        const category = contentCategorizer.categorizePost(
            caption,
            mediaType || 'unknown',
            hasEventIndicators || false
        );

        res.json({
            categories: {
                primary: category.primary,
                secondary: category.secondary,
                confidence: category.confidence,
                hashtags: category.hashtags
            },
            original: {
                caption: caption,
                mediaType: mediaType || 'unknown',
                hasEventIndicators: hasEventIndicators || false
            }
        });
    } catch (error: any) {
        console.error(`Error in /api/categorize: ${error}`);
        res.status(500).json({ error: error.message });
    }
});

// Add endpoint to get summarized top daily posts
app.get('/api/feed/summaries', async (req, res) => {
    try {
        const count = req.query.count ? parseInt(req.query.count as string) : 5;
        const detail = req.query.detail === 'true'; // Option to include detailed post data
        const cached = req.query.cached === 'true'; // Option to use cached summaries
        
        // For cached requests, check for existing summaries first
        if (cached) {
            try {
                // Ensure summaries directory exists
                FileUtils.ensureDirectoryExists(Paths.SUMMARIES_DIR);
                
                // Try to get latest summary file using reference
                const latestSummaryFile = FileUtils.getLatestFileFromReference(Paths.SUMMARIES_DIR);
                
                if (latestSummaryFile) {
                    console.log(`Using cached summaries from: ${latestSummaryFile}`);
                    const cachedData = JSON.parse(fs.readFileSync(latestSummaryFile, 'utf-8'));
                    
                    // Check if we have enough summaries or need to generate more
                    if (cachedData.summaries && cachedData.summaries.length >= count) {
                        // We have enough cached summaries
                        const response = {
                            date: cachedData.generated_at,
                            count: Math.min(count, cachedData.summaries.length),
                            summaries: cachedData.summaries.slice(0, count),
                            cached: true
                        };
                        
                        // If detail requested and we don't have original posts, we'll ignore that option
                        return res.json(response);
                    }
                }
            } catch (cacheError) {
                console.warn('Error reading cached summaries, generating new ones:', cacheError);
                // Continue to generate new summaries below
            }
        }
        
        // Get top posts
        const topPosts = await getTopDailyPosts(count);
        
        // Generate summaries with OpenAI
        const summaries = await generatePostSummaries(topPosts);
        
        // If detail requested, include original post data
        const response: any = {
            date: new Date().toISOString(),
            count: summaries.length,
            summaries: summaries,
            cached: false
        };
        
        if (detail) {
            // Combine summaries with original posts for more context
            response.posts = summaries.map(summary => {
                const originalPost = topPosts.find(post => post.postId === summary.postId);
                return {
                    summary,
                    originalPost
                };
            });
        }
        
        res.json(response);
    } catch (error: any) {
        console.error(`Error in /api/feed/summaries: ${error}`);
        res.status(500).json({ error: error.message });
    }
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
    console.log(`📊 Scored feed API available at http://localhost:${PORT}/api/feed/scored`);
    console.log(`🌟 Simplified feed API available at http://localhost:${PORT}/api/feed/simple`);
    console.log(`🎭 Events feed API available at http://localhost:${PORT}/api/feed/events`);
    console.log(`🎪 Simplified events API available at http://localhost:${PORT}/api/feed/events/simple`);
    console.log(`⭐ Priority feed API available at http://localhost:${PORT}/api/feed/priority/[high|medium|low]`);
    console.log(`🔝 Top daily posts API available at http://localhost:${PORT}/api/feed/top-daily`);
    console.log(`🏷️  Content categorization API available at http://localhost:${PORT}/api/categorize`);
    console.log(`📝 AI-generated summaries API available at http://localhost:${PORT}/api/feed/summaries`);
});

export default app;