import dataLoader from '../services/dataLoader.js';
import { PostScorer } from '../services/postScorer.js';

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
        const scoredPosts = posts.map(post => ({
            post,
            score: scorer.scorePost(post)
        }));
        
        // Sort by score (highest first)
        scoredPosts.sort((a, b) => b.score.finalScore - a.score.finalScore);
        
        // Output top 10 highest scored posts
        console.log('\n===== TOP 10 HIGHEST SCORED POSTS =====');
        scoredPosts.slice(0, 10).forEach((item, index) => {
            const { post, score } = item;
            console.log(`\n#${index + 1} - Score: ${score.finalScore}`);
            console.log(`Username: ${rawPosts.find(p => p.id === post.postId)?.user.username}`);
            console.log(`Close Friend: ${post.isCloseFriend ? 'Yes' : 'No'}`);
            console.log(`Verified: ${post.isVerified ? 'Yes' : 'No'}`);
            console.log(`Caption: ${post.caption?.substring(0, 100)}${post.caption && post.caption.length > 100 ? '...' : ''}`);
            console.log(`Event Indicators: ${post.hasEventIndicators ? 'Yes' : 'No'}`);
            if (post.eventKeywords && post.eventKeywords.length > 0) {
                console.log(`Event Keywords: ${post.eventKeywords.join(', ')}`);
            }
            console.log(`Component Scores: ${JSON.stringify(score.componentScores)}`);
        });
        
    } catch (error) {
        console.error('Error running scorer:', error);
    }
}

main();