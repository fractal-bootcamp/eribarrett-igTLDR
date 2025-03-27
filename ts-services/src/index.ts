import express from 'express';
import path from 'path';
import { PostScorer } from './services/postScorer.js';
import dataLoader from './services/dataLoader.js';

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(express.json());

// Helper to create simplified post data
function simplifyPost(scoredPost: any) {
    const { post, score, raw } = scoredPost;
    return {
        id: post.postId,
        username: raw.user.username,
        isCloseFriend: post.isCloseFriend,
        isVerified: post.isVerified,
        caption: post.caption?.substring(0, 200) || '',
        hasEvent: post.hasEventIndicators || false,
        eventKeywords: post.eventKeywords || [],
        score: score.finalScore,
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
        const scoredPosts = posts.map((post, index) => ({
            post,
            score: scorer.scorePost(post),
            raw: rawPosts[index] // Include original raw data
        }));
        
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
        const scoredPosts = posts.map((post, index) => ({
            post,
            score: scorer.scorePost(post),
            raw: rawPosts[index]
        }));
        
        // Sort by score (highest first)
        scoredPosts.sort((a, b) => b.score.finalScore - a.score.finalScore);
        
        // Simplify the posts data
        const simplifiedPosts = scoredPosts.map(simplifyPost);
        
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
        const scoredPosts = posts.map((post, index) => ({
            post,
            score: scorer.scorePost(post),
            raw: rawPosts[index]
        }));
        
        // Filter to only include posts with event indicators
        const eventPosts = scoredPosts.filter(item => item.post.hasEventIndicators);
        
        // Sort by score (highest first)
        eventPosts.sort((a, b) => b.score.finalScore - a.score.finalScore);
        
        // Simplify the posts data
        const simplifiedPosts = eventPosts.map(simplifyPost);
        
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
        const scoredPosts = posts.map((post, index) => ({
            post,
            score: scorer.scorePost(post),
            raw: rawPosts[index]
        }));
        
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

// Start server
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
    console.log(`📊 Scored feed API available at http://localhost:${PORT}/api/feed/scored`);
    console.log(`🌟 Simplified feed API available at http://localhost:${PORT}/api/feed/simple`);
    console.log(`🎭 Events feed API available at http://localhost:${PORT}/api/feed/events`);
    console.log(`🎪 Simplified events API available at http://localhost:${PORT}/api/feed/events/simple`);
});

export default app;