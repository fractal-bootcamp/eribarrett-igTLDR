import dataLoader from '../services/dataLoader.js';
import { PostScorer } from '../services/postScorer.js';
import postPrioritizer from '../services/postPrioritizer.js';
import contentCategorizer, { ContentCategory } from '../services/contentCategorizer.js';
import fs from 'fs';
import path from 'path';
import { FileUtils, DateUtils, Paths } from '../services/utils.js';

console.log("========== SCRIPT STARTED ==========");
console.log("Current working directory:", process.cwd());

interface TopPostOutput {
  postId: string;
  username: string;
  mediaType: string;
  caption: string;
  hasEvent: boolean;
  eventKeywords?: string[];
  url: string;
  engagementCount: number;
  engagementRatio: number;
  createdAt: string;
  importance: {
    score: number;
    priority: string;
    reason: string;
  };
  contentCategories: {
    primary: string;
    secondary?: string;
    confidence: number;
    hashtags: string[];
  };
}

/**
 * Gets the top posts from today's feed data
 * @param count Number of top posts to return (default: 5)
 * @param outputPath Optional path to save results as JSON
 * @returns Array of top post objects
 */
async function getTopDailyPosts(count: number = 5, outputPath?: string): Promise<TopPostOutput[]> {
  try {
    console.log('Loading the latest feed data...');
    const rawPosts = dataLoader.loadLatestDirectFeed();
    console.log(`Loaded ${rawPosts.length} total posts from feed`);

    // Get unique usernames to check if they're close friends
    const usernames = [...new Set(rawPosts.map(post => post.user.username))];
    const closeFriendUsernames: string[] = [];

    // For each username, try to load close friends data
    for (const username of usernames) {
      const closeFriends = dataLoader.getCloseFriends(username);
      closeFriendUsernames.push(...closeFriends);
    }

    // Get today's date without time for filtering
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // Convert raw posts to our Post format
    const posts = rawPosts.map(rawPost =>
      dataLoader.convertToPost(rawPost, closeFriendUsernames)
    );

    // Filter to only include posts from today
    const todayPosts = posts.filter(post => {
      const postDate = new Date(post.createdAt);
      postDate.setHours(0, 0, 0, 0);
      return postDate.getTime() === today.getTime();
    });

    console.log(`Found ${todayPosts.length} posts from today`);

    if (todayPosts.length === 0) {
      console.log('No posts from today found. Using most recent posts instead...');
      // Sort all posts by date (newest first) and take the most recent ones
      posts.sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());
      todayPosts.push(...posts.slice(0, Math.min(count * 2, posts.length)));
    }

    // Score all today's posts
    const scorer = new PostScorer();
    const scoredPosts = todayPosts.map((post, index) => {
      const originalRaw = rawPosts.find(raw => raw.post_id === post.postId);
      const scoreResult = scorer.scorePost(post);
      const priorityResult = postPrioritizer.prioritize(post, scoreResult);

      return {
        post,
        score: scoreResult,
        priority: priorityResult,
        raw: originalRaw
      };
    });

    // Sort by score (highest first)
    scoredPosts.sort((a, b) => b.score.finalScore - a.score.finalScore);

    // Deduplicate posts by finding unique posts based on content similarity
    const deduplicated = [];
    const seenCaptions = new Set();
    const seenUsernames = new Set();
    const usersPostCount: Record<string, number> = {};

    // First pass: Get a count of posts per user to find diversity
    for (const post of scoredPosts) {
      const username = post.raw?.user.username || '';
      usersPostCount[username] = (usersPostCount[username] || 0) + 1;
    }

    // Get unique usernames and sort by post scores
    const uniqueUsernames = [...new Set(scoredPosts.map(post => post.raw?.user.username || ''))];
    const totalUniqueUsers = uniqueUsernames.length;

    // Determine how many posts per user we should allow
    const maxPostsPerUser = totalUniqueUsers >= count ? 1 : Math.ceil(count / totalUniqueUsers);

    // Second pass: Filter out duplicate posts and limit posts per user
    for (const post of scoredPosts) {
      const caption = post.post.caption || '';
      const captionStart = caption.substring(0, 50); // Use start of caption for similarity check
      const username = post.raw?.user.username || '';

      // Skip if we've already taken the max number of posts from this user
      if (seenUsernames.has(username) &&
        uniqueUsernames.length >= count &&
        maxPostsPerUser === 1) {
        continue;
      }

      // Count how many posts we've seen from this user
      const userPostsSeen = Array.from(seenUsernames).filter(u => u === username).length;
      if (userPostsSeen >= maxPostsPerUser) {
        continue;
      }

      // Generate a key combining username and caption start to check for duplicates
      const userCaptionKey = `${username}:${captionStart}`;

      // If we haven't seen this combo before, add it
      if (!seenCaptions.has(userCaptionKey)) {
        seenCaptions.add(userCaptionKey);
        seenUsernames.add(username);
        deduplicated.push(post);

        // If we have enough unique posts, break
        if (deduplicated.length >= count) {
          break;
        }
      }
    }

    // Log uniqueness stats
    console.log(`Found ${deduplicated.length} unique posts after deduplication`);
    console.log(`Total unique users: ${totalUniqueUsers}, max posts per user: ${maxPostsPerUser}`);

    // Take top N unique posts
    const topPosts = deduplicated.slice(0, count);

    // Format output
    const result = topPosts.map((item): TopPostOutput => {
      const { post, score, priority, raw } = item;

      // Categorize post content
      const category = contentCategorizer.categorizePost(
        post.caption || '',
        raw?.media_type || 'unknown',
        post.hasEventIndicators || false
      );

      return {
        postId: post.postId,
        username: raw?.user.username || '',
        mediaType: raw?.media_type || 'unknown',
        caption: post.caption || '',
        hasEvent: post.hasEventIndicators || false,
        eventKeywords: post.eventKeywords,
        url: `https://instagram.com/p/${raw?.shortcode || ''}`,
        engagementCount: post.engagementCount,
        engagementRatio: post.engagementCount / (post.followerCount || 1),
        createdAt: post.createdAt.toISOString(),
        importance: {
          score: score.finalScore,
          priority: priority.level,
          reason: priority.reason
        },
        contentCategories: {
          primary: category.primary,
          secondary: category.secondary,
          confidence: category.confidence,
          hashtags: category.hashtags
        }
      };
    });

    // Save to file if outputPath provided
    if (outputPath) {
      // Format the date for file naming
      const now = new Date();
      const formattedDate = DateUtils.formatDate(now);
      const timestamp = DateUtils.formatDateTime(now);
      
      // If no specific path is provided, use our organized directory structure
      let finalOutputPath;
      if (outputPath === 'default') {
        // Make sure the directory exists
        FileUtils.ensureDirectoryExists(Paths.DAILY_POSTS_DIR);
        const filename = `top_posts_${formattedDate}_${timestamp}.json`;
        finalOutputPath = path.join(Paths.DAILY_POSTS_DIR, filename);
        
        // Write the file
        fs.writeFileSync(
          finalOutputPath,
          JSON.stringify({
            date: now.toISOString(),
            count: result.length,
            posts: result
          }, null, 2)
        );
        
        // Update the latest.json reference
        FileUtils.updateLatestReference(Paths.DAILY_POSTS_DIR, filename, {
          post_count: result.length,
          timestamp: now.toISOString(),
          date: formattedDate
        });
        
        console.log(`Results saved to: ${finalOutputPath}`);
        console.log(`Updated latest reference at: ${path.join(Paths.DAILY_POSTS_DIR, 'latest.json')}`);
      } else {
        // User specified a custom path, ensure the directory exists
        const outputDir = path.dirname(outputPath);
        FileUtils.ensureDirectoryExists(outputDir);
        
        // Write the file
        fs.writeFileSync(
          outputPath,
          JSON.stringify({
            date: now.toISOString(),
            count: result.length,
            posts: result
          }, null, 2)
        );
        
        console.log(`Results saved to: ${outputPath}`);
      }
    }

    return result;
  } catch (error) {
    console.error('Error getting top daily posts:', error);
    return [];
  }
}

// When script is run directly
try {
  console.log("Script is running in main mode");
  console.log("Running top daily posts directly");
  const args = process.argv.slice(2);
  const count = args[0] ? parseInt(args[0]) : 5;
  const outputPath = args[1] || 'default'; // Use our default organized path

  getTopDailyPosts(count, outputPath).then(posts => {
    console.log(`\n=== Top ${posts.length} Posts from Today ===`);
    posts.forEach((post, i) => {
      console.log(`\n#${i + 1}: Importance Score: ${post.importance.score.toFixed(2)} (${post.importance.priority.toUpperCase()})`);
      console.log(`Username: @${post.username}`);
      console.log(`Media Type: ${post.mediaType}`);
      console.log(`Content: ${post.contentCategories.primary}${post.contentCategories.secondary ? ` / ${post.contentCategories.secondary}` : ''} (${(post.contentCategories.confidence * 100).toFixed(0)}% confidence)`);
      console.log(`Hashtags: ${post.contentCategories.hashtags.join(' ')}`);
      console.log(`Engagement: ${post.engagementCount} interactions (${(post.engagementRatio * 100).toFixed(2)}% ratio)`);
      console.log(`Caption: ${post.caption?.substring(0, 100)}${post.caption?.length > 100 ? '...' : ''}`);
      if (post.hasEvent) {
        console.log(`EVENT DETECTED! Keywords: ${post.eventKeywords?.join(', ')}`);
      }
      console.log(`URL: ${post.url}`);
    });
  }).catch(error => {
    console.error("Error getting top daily posts:", error);
  });
} catch (error) {
  console.error("Error in main execution:", error);
}

export default getTopDailyPosts;