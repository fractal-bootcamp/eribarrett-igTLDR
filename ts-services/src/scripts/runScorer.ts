import dataLoader from '../services/dataLoader.js';
import { PostScorer } from '../services/postScorer.js';

// Helper to create simplified post data for console output
function simplifyPost(scoredPost: any) {
    const { post, score, rawPost } = scoredPost;
    return {
        id: post.postId,
        username: rawPost.user.username,
        isCloseFriend: post.isCloseFriend,
        isVerified: post.isVerified,
        caption: post.caption?.substring(0, 100) || '',
        hasEvent: post.hasEventIndicators || false,
        eventKeywords: post.eventKeywords || [],
        score: score.finalScore,
        mediaType: rawPost.media_type,
        url: `https://instagram.com/p/${rawPost.shortcode}`,
        timestamp: post.createdAt
    };
}

/**
 * This script loads the latest feed data collected by the Python backend,
 * scores all posts, and outputs the results sorted by score.
 */
async function main() {
    try {
        console.log('Loading the latest feed data from Python backend...');
        const rawPosts = dataLoader.loadLatestDirectFeed();
        console.log(`Loaded ${rawPosts.length} posts from feed`);
        
        // Get unique usernames to check if they're close friends
        const usernames = [...new Set(rawPosts.map(post => post.user.username))];
        const closeFriendUsernames: string[] = [];
        
        // For each username, try to load close friends data
        for (const username of usernames) {
            const closeFriends = dataLoader.getCloseFriends(username);
            closeFriendUsernames.push(...closeFriends);
        }
        
        console.log(`Found ${closeFriendUsernames.length} close friend usernames`);
        
        // Convert raw posts to our Post format
        const posts = rawPosts.map(rawPost => 
            dataLoader.convertToPost(rawPost, closeFriendUsernames)
        );
        
        // Score all posts
        const scorer = new PostScorer();
        const scoredPosts = posts.map((post, index) => ({
            post,
            score: scorer.scorePost(post),
            rawPost: rawPosts[index]
        }));
        
        // Sort by score (highest first)
        scoredPosts.sort((a, b) => b.score.finalScore - a.score.finalScore);
        
        // Output top 10 highest scored posts
        console.log('\n===== TOP 10 HIGHEST SCORED POSTS =====');
        scoredPosts.slice(0, 10).forEach((item, index) => {
            const simplified = simplifyPost(item);
            console.log(`\n#${index + 1} - Score: ${simplified.score}`);
            console.log(`Username: ${simplified.username}`);
            console.log(`Close Friend: ${simplified.isCloseFriend ? 'Yes' : 'No'}`);
            console.log(`Verified: ${simplified.isVerified ? 'Yes' : 'No'}`);
            console.log(`Caption: ${simplified.caption}${simplified.caption && simplified.caption.length === 100 ? '...' : ''}`);
            console.log(`Has Event: ${simplified.hasEvent ? 'Yes' : 'No'}`);
            if (simplified.eventKeywords && simplified.eventKeywords.length > 0) {
                console.log(`Event Keywords: ${simplified.eventKeywords.join(', ')}`);
            }
            console.log(`URL: ${simplified.url}`);
        });
        
        // Output event posts
        const eventPosts = scoredPosts.filter(item => item.post.hasEventIndicators);
        console.log(`\n\n===== ${eventPosts.length} POSTS WITH EVENTS =====`);
        eventPosts.forEach((item, index) => {
            const simplified = simplifyPost(item);
            console.log(`\n#${index + 1} - Score: ${simplified.score}`);
            console.log(`Username: ${simplified.username}`);
            console.log(`Caption: ${simplified.caption}${simplified.caption && simplified.caption.length === 100 ? '...' : ''}`);
            console.log(`Event Keywords: ${simplified.eventKeywords.join(', ')}`);
            console.log(`URL: ${simplified.url}`);
        });
        
    } catch (error) {
        console.error('Error running scorer:', error);
    }
}

main();