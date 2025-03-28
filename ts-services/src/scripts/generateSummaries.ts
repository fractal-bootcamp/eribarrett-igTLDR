import { generatePostSummaries } from '../services/openAiService.js';
import getTopDailyPosts from './topDailyPosts.js';
import fs from 'fs';
import path from 'path';
import { FileUtils, DateUtils, Paths } from '../services/utils.js';

/**
 * Generate summaries for the top daily posts
 */
async function generateSummariesForTopPosts(count: number = 5) {
  try {
    console.log(`Generating summaries for top ${count} posts...`);
    
    // Get the top posts
    const topPosts = await getTopDailyPosts(count);
    
    if (topPosts.length === 0) {
      console.log('No posts found to summarize.');
      return;
    }
    
    console.log(`Found ${topPosts.length} posts to summarize.`);
    
    // Generate summaries
    const summaries = await generatePostSummaries(topPosts);
    
    // Print the summaries
    console.log('\n===== GENERATED SUMMARIES =====');
    summaries.forEach((summary, index) => {
      console.log(`\n${index + 1}. * ${summary.emoji}`);
      console.log(`**@${summary.username}** ${summary.actionDescription}`);
      console.log(`**Primary Category: ${summary.primaryCategory}**`);
      if (summary.secondaryCategory) {
        console.log(`**Secondary Category: ${summary.secondaryCategory}**`);
      }
      
      // Print a shortened version of the original caption for reference
      const caption = summary.originalCaption || '';
      console.log(`\nOriginal Caption: ${caption.substring(0, 150)}${caption.length > 150 ? '...' : ''}`);
      
      // Print score and priority for reference
      console.log(`\nImportance: ${summary.originalScore.toFixed(2)} (${summary.originalPriority.toUpperCase()})`);
    });
    
    // Ensure summaries directory exists
    FileUtils.ensureDirectoryExists(Paths.SUMMARIES_DIR);
    
    // Create timestamped filename for the summaries
    const now = new Date();
    const formattedDate = DateUtils.formatDate(now);
    const timestamp = DateUtils.formatDateTime(now);
    const filename = `post_summaries_${formattedDate}_${timestamp}.json`;
    const outputPath = path.join(Paths.SUMMARIES_DIR, filename);
    
    // Save the summaries to a file
    fs.writeFileSync(
      outputPath,
      JSON.stringify({
        generated_at: now.toISOString(),
        count: summaries.length,
        summaries
      }, null, 2)
    );
    
    // Update latest.json reference
    FileUtils.updateLatestReference(Paths.SUMMARIES_DIR, filename, {
      summary_count: summaries.length,
      post_count: topPosts.length
    });
    
    console.log(`\nSaved ${summaries.length} summaries to ${outputPath}`);
    console.log(`Updated latest reference at: ${path.join(Paths.SUMMARIES_DIR, 'latest.json')}`);
    
    return summaries;
    
  } catch (error) {
    console.error('Error generating summaries:', error);
  }
}

// When script is run directly
if (import.meta.url === import.meta.main) {
  const args = process.argv.slice(2);
  const count = args[0] ? parseInt(args[0]) : 5;
  
  generateSummariesForTopPosts(count);
}

export default generateSummariesForTopPosts;