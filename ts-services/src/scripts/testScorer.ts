import { PostScorer } from '../services/postScorer.js';

/**
 * This script tests the PostScorer with sample data
 */
function main() {
    console.log('Testing PostScorer with sample data...');

    const samplePosts = [
        {
            postId: "1",
            userId: "user1",
            isCloseFriend: true,
            isVerified: false,
            caption: "Join us tomorrow at 2 PM at 123 Main Street for our workshop!",
            engagementCount: 1000,
            followerCount: 10000,
            createdAt: new Date(),
            hasEventIndicators: true,
            eventKeywords: ["workshop", "tomorrow", "2 PM"]
        },
        {
            postId: "2",
            userId: "user2",
            isCloseFriend: false,
            isVerified: true,
            caption: "Just posted a new photo!",
            engagementCount: 5000,
            followerCount: 100000,
            createdAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000), // 3 days ago
            hasEventIndicators: false,
            eventKeywords: []
        },
        {
            postId: "3",
            userId: "user3",
            isCloseFriend: false,
            isVerified: false,
            caption: "RSVP for our event on 04/15/2025 at 7:30 PM",
            engagementCount: 200,
            followerCount: 5000,
            createdAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000), // 1 day ago
            hasEventIndicators: true,
            eventKeywords: ["event", "RSVP", "04/15/2025", "7:30 PM"]
        }
    ];

    const scorer = new PostScorer();

    // Score each post and display results
    samplePosts.forEach((post, index) => {
        const result = scorer.scorePost(post);

        console.log(`\nPost #${index + 1}:`);
        console.log(`Caption: ${post.caption}`);
        console.log(`Close Friend: ${post.isCloseFriend ? 'Yes' : 'No'}`);
        console.log(`Verified: ${post.isVerified ? 'Yes' : 'No'}`);
        console.log(`Event Indicators: ${post.hasEventIndicators ? 'Yes' : 'No'}`);

        if (post.eventKeywords && post.eventKeywords.length > 0) {
            console.log(`Event Keywords: ${post.eventKeywords.join(', ')}`);
        }

        console.log('Component Scores:');
        Object.entries(result.componentScores).forEach(([component, score]) => {
            console.log(`  ${component}: ${score}`);
        });

        console.log(`Final Score: ${result.finalScore}`);
    });
}

main();