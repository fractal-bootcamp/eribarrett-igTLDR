/**
 * Test script to manually run and verify the top daily posts functionality
 */
import getTopDailyPosts from './scripts/topDailyPosts.js';
import fs from 'fs';
import path from 'path';

// Main function to test the top daily posts
async function testTopDailyPosts() {
  console.log('Starting top daily posts test...');
  
  try {
    // Get top 5 posts
    const topPosts = await getTopDailyPosts(5);
    
    console.log(`Got ${topPosts.length} top posts`);
    
    // Print out the results
    if (topPosts.length === 0) {
      console.log('No posts found!');
      return;
    }
    
    // Check for uniqueness
    const usernames = topPosts.map(post => post.username);
    const uniqueUsernames = new Set(usernames);
    
    console.log(`Usernames in top posts: ${usernames.join(', ')}`);
    console.log(`Number of unique usernames: ${uniqueUsernames.size} out of ${topPosts.length} posts`);
    
    // Save the results to a file for inspection
    const outputPath = path.resolve('./test-top-daily.json');
    fs.writeFileSync(
      outputPath,
      JSON.stringify({ 
        date: new Date().toISOString(),
        count: topPosts.length,
        posts: topPosts 
      }, null, 2)
    );
    
    console.log(`Saved results to ${outputPath} for inspection`);
    
    // Print brief summary
    topPosts.forEach((post, i) => {
      console.log(`\n[Post ${i+1}] @${post.username} - ${post.contentCategories.primary}${post.contentCategories.secondary ? `/${post.contentCategories.secondary}` : ''}`);
      console.log(`Caption start: ${post.caption.substring(0, 50)}...`);
    });
    
  } catch (error) {
    console.error('Error testing top daily posts:', error);
  }
}

// Run the test
testTopDailyPosts();