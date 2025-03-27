import dataLoader from '../services/dataLoader.js';
import { PostScorer } from '../services/postScorer.js';
import postPrioritizer, { PriorityLevel } from '../services/postPrioritizer.js';
import chalk from 'chalk';

// Helper to create simplified post data for console output
function simplifyPost(scoredPost: any) {
    const { post, score, rawPost, priority } = scoredPost;
    return {
        id: post.postId,
        username: rawPost.user.username,
        isCloseFriend: post.isCloseFriend,
        isVerified: post.isVerified,
        caption: post.caption?.substring(0, 100) || '',
        hasEvent: post.hasEventIndicators || false,
        eventKeywords: post.eventKeywords || [],
        score: score.finalScore,
        priority: priority?.level || 'unknown',
        priorityReason: priority?.reason || '',
        mediaType: rawPost.media_type,
        url: `https://instagram.com/p/${rawPost.shortcode}`,
        timestamp: post.createdAt
    };
}

// Format priority level with color
function formatPriority(level: PriorityLevel): string {
    switch (level) {
        case PriorityLevel.HIGH:
            return chalk.red.bold('HIGH');
        case PriorityLevel.MEDIUM:
            return chalk.yellow.bold('MEDIUM');
        case PriorityLevel.LOW:
            return chalk.green('LOW');
        default:
            return level;
    }
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
        const scoredPosts = posts.map((post, index) => {
            const scoreResult = scorer.scorePost(post);
            const priorityResult = postPrioritizer.prioritize(post, scoreResult);
            
            return {
                post,
                score: scoreResult,
                rawPost: rawPosts[index],
                priority: priorityResult
            };
        });
        
        // Sort by priority first, then score
        scoredPosts.sort((a, b) => {
            // First sort by priority level
            const priorityOrder = { 
                [PriorityLevel.HIGH]: 0, 
                [PriorityLevel.MEDIUM]: 1, 
                [PriorityLevel.LOW]: 2 
            };
            
            const priorityDiff = priorityOrder[a.priority.level] - priorityOrder[b.priority.level];
            if (priorityDiff !== 0) return priorityDiff;
            
            // Then by score
            return b.score.finalScore - a.score.finalScore;
        });
        
        // Output posts by priority
        for (const level of [PriorityLevel.HIGH, PriorityLevel.MEDIUM, PriorityLevel.LOW]) {
            const postsInCategory = scoredPosts.filter(p => p.priority.level === level);
            console.log(`\n===== ${postsInCategory.length} ${level.toUpperCase()} PRIORITY POSTS =====`);
            
            postsInCategory.forEach((item, index) => {
                const simplified = simplifyPost(item);
                console.log(`\n#${index + 1} - Priority: ${formatPriority(item.priority.level)} (${item.priority.reason})`);
                console.log(`Score: ${simplified.score.toFixed(2)}`);
                console.log(`Username: ${simplified.username}`);
                console.log(`Close Friend: ${simplified.isCloseFriend ? 'Yes' : 'No'}`);
                console.log(`Has Event: ${simplified.hasEvent ? 'Yes' : 'No'}`);
                if (simplified.eventKeywords && simplified.eventKeywords.length > 0) {
                    console.log(`Event Keywords: ${simplified.eventKeywords.join(', ')}`);
                }
                console.log(`Caption: ${simplified.caption}${simplified.caption && simplified.caption.length === 100 ? '...' : ''}`);
                console.log(`URL: ${simplified.url}`);
            });
        }
        
    } catch (error) {
        console.error('Error running scorer:', error);
    }
}

main();