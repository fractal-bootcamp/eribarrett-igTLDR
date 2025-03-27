import express from 'express';
import path from 'path';
import { PostScorer } from './services/postScorer.js';
import dataLoader from './services/dataLoader.js';

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(express.json());

// Routes
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
        const scoredPosts = posts.map(post => ({
            post,
            score: scorer.scorePost(post),
            raw: rawPosts.find(p => p.id === post.postId) // Include original raw data
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

// Add endpoint to get the highest-scoring posts that contain event indicators
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
        const scoredPosts = posts.map(post => ({
            post,
            score: scorer.scorePost(post),
            raw: rawPosts.find(p => p.id === post.postId)
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
    console.log(`🎭 Events feed API available at http://localhost:${PORT}/api/feed/events`);
});

export default app;