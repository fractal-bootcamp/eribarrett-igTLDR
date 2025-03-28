import OpenAI from 'openai';
import { readFileSync } from 'fs';
import { dirname, resolve } from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

// Load .env file
dotenv.config();

// Get the directory name
const __dirname = dirname(fileURLToPath(import.meta.url));

// Read the API key from environment variables
const apiKey = process.env.OPENAI_API_KEY;

if (!apiKey) {
  console.error('OPENAI_API_KEY is not set in the environment variables');
  process.exit(1);
}

// Initialize OpenAI client
const openai = new OpenAI({
  apiKey: apiKey,
});

/**
 * Interface for a post summary
 */
export interface PostSummary {
  postId: string;
  username: string;
  emoji: string;
  actionDescription: string;
  primaryCategory: string;
  secondaryCategory?: string;
  originalCaption: string;
  originalScore: number;
  originalPriority: string;
}

/**
 * Generate a human-readable summary for a post
 */
export async function generatePostSummary(post: any): Promise<PostSummary> {
  // Advanced emoji mapping with weights for intelligent fallback selection
  // Higher weights (0-10) indicate stronger relevance to the category
  interface EmojiMapping {
    emoji: string;
    weight: number;
    keywords: string[];
  }

  const categoryEmojiMap: Record<string, EmojiMapping[]> = {
    'Selfie': [
      { emoji: '🤳', weight: 10, keywords: ['selfie', 'mirror', 'phone'] },
      { emoji: '📱', weight: 7, keywords: ['phone', 'camera'] },
      { emoji: '😊', weight: 5, keywords: ['smile', 'face', 'happy'] }
    ],
    'Portrait': [
      { emoji: '👤', weight: 9, keywords: ['portrait', 'profile', 'headshot'] },
      { emoji: '📸', weight: 8, keywords: ['photo', 'picture', 'shoot'] },
      { emoji: '🖼️', weight: 6, keywords: ['frame', 'posed'] }
    ],
    'Food': [
      { emoji: '🍽️', weight: 7, keywords: ['meal', 'dining', 'restaurant'] },
      { emoji: '🍲', weight: 8, keywords: ['dish', 'cooking', 'homemade'] },
      { emoji: '👨‍🍳', weight: 6, keywords: ['chef', 'cooking', 'recipe'] },
      { emoji: '🍷', weight: 7, keywords: ['wine', 'drink', 'toast'] },
      { emoji: '🍕', weight: 8, keywords: ['pizza', 'takeout', 'delivery'] },
      { emoji: '🍣', weight: 8, keywords: ['sushi', 'japanese', 'seafood'] },
      { emoji: '🍔', weight: 8, keywords: ['burger', 'fastfood'] },
      { emoji: '🍰', weight: 8, keywords: ['cake', 'dessert', 'sweet'] },
      { emoji: '☕', weight: 7, keywords: ['coffee', 'cafe', 'morning'] }
    ],
    'Travel': [
      { emoji: '✈️', weight: 10, keywords: ['plane', 'flight', 'trip'] },
      { emoji: '🧳', weight: 8, keywords: ['luggage', 'packing', 'vacation'] },
      { emoji: '🗺️', weight: 7, keywords: ['map', 'navigation', 'explore'] },
      { emoji: '🏝️', weight: 9, keywords: ['island', 'beach', 'tropical'] },
      { emoji: '🚆', weight: 7, keywords: ['train', 'railway', 'station'] },
      { emoji: '🚗', weight: 6, keywords: ['car', 'roadtrip', 'drive'] }
    ],
    'Nature': [
      { emoji: '🌿', weight: 8, keywords: ['plant', 'leaves', 'green'] },
      { emoji: '🌲', weight: 9, keywords: ['tree', 'forest', 'woods'] },
      { emoji: '🌊', weight: 9, keywords: ['ocean', 'wave', 'sea'] },
      { emoji: '🏔️', weight: 10, keywords: ['mountain', 'peak', 'hiking'] },
      { emoji: '🌅', weight: 8, keywords: ['sunset', 'sunrise', 'horizon'] },
      { emoji: '🌸', weight: 7, keywords: ['flower', 'blossom', 'spring'] },
      { emoji: '🦋', weight: 6, keywords: ['butterfly', 'insect', 'garden'] }
    ],
    'Art': [
      { emoji: '🎨', weight: 10, keywords: ['painting', 'artist', 'palette'] },
      { emoji: '🖌️', weight: 8, keywords: ['brush', 'canvas', 'creation'] },
      { emoji: '✏️', weight: 7, keywords: ['drawing', 'sketch', 'illustration'] },
      { emoji: '🖼️', weight: 9, keywords: ['frame', 'gallery', 'exhibition'] },
      { emoji: '🎭', weight: 7, keywords: ['theater', 'performance', 'drama'] }
    ],
    'Event': [
      { emoji: '🎉', weight: 9, keywords: ['celebration', 'party', 'festive'] },
      { emoji: '🎊', weight: 8, keywords: ['confetti', 'celebration', 'surprise'] },
      { emoji: '📅', weight: 10, keywords: ['calendar', 'date', 'schedule'] },
      { emoji: '🎂', weight: 8, keywords: ['birthday', 'cake', 'anniversary'] },
      { emoji: '🎓', weight: 9, keywords: ['graduation', 'diploma', 'ceremony'] },
      { emoji: '💍', weight: 10, keywords: ['wedding', 'engagement', 'proposal'] },
      { emoji: '🏆', weight: 7, keywords: ['award', 'ceremony', 'competition'] }
    ],
    'Music': [
      { emoji: '🎵', weight: 9, keywords: ['notes', 'song', 'tune'] },
      { emoji: '🎸', weight: 10, keywords: ['guitar', 'band', 'concert'] },
      { emoji: '🎤', weight: 10, keywords: ['microphone', 'singer', 'karaoke'] },
      { emoji: '🎧', weight: 8, keywords: ['headphones', 'listening', 'playlist'] },
      { emoji: '🥁', weight: 7, keywords: ['drums', 'percussion', 'rhythm'] },
      { emoji: '🎹', weight: 7, keywords: ['piano', 'keyboard', 'keys'] },
      { emoji: '🎷', weight: 7, keywords: ['saxophone', 'jazz', 'brass'] }
    ],
    'Fashion': [
      { emoji: '👗', weight: 10, keywords: ['dress', 'outfit', 'style'] },
      { emoji: '👠', weight: 8, keywords: ['shoes', 'heels', 'footwear'] },
      { emoji: '👜', weight: 7, keywords: ['bag', 'purse', 'accessory'] },
      { emoji: '👔', weight: 8, keywords: ['formal', 'suit', 'business'] },
      { emoji: '🧥', weight: 7, keywords: ['coat', 'jacket', 'outerwear'] },
      { emoji: '👒', weight: 6, keywords: ['hat', 'headwear', 'accessory'] },
      { emoji: '👚', weight: 9, keywords: ['top', 'blouse', 'clothing'] }
    ],
    'Beauty': [
      { emoji: '💄', weight: 10, keywords: ['lipstick', 'makeup', 'cosmetics'] },
      { emoji: '💅', weight: 9, keywords: ['nails', 'manicure', 'polish'] },
      { emoji: '💇‍♀️', weight: 8, keywords: ['haircut', 'salon', 'style'] },
      { emoji: '🧖‍♀️', weight: 7, keywords: ['spa', 'treatment', 'relaxation'] },
      { emoji: '✨', weight: 6, keywords: ['glow', 'sparkle', 'shine'] }
    ],
    'Fitness': [
      { emoji: '💪', weight: 10, keywords: ['strength', 'muscles', 'workout'] },
      { emoji: '🏋️‍♀️', weight: 9, keywords: ['weights', 'gym', 'lifting'] },
      { emoji: '🧘‍♀️', weight: 8, keywords: ['yoga', 'meditation', 'flexibility'] },
      { emoji: '🏃‍♀️', weight: 9, keywords: ['running', 'jogging', 'cardio'] },
      { emoji: '🚴‍♀️', weight: 7, keywords: ['cycling', 'bike', 'spin'] },
      { emoji: '🏊‍♀️', weight: 7, keywords: ['swimming', 'pool', 'water'] }
    ],
    'Pet': [
      { emoji: '🐶', weight: 9, keywords: ['dog', 'puppy', 'canine'] },
      { emoji: '🐱', weight: 9, keywords: ['cat', 'kitten', 'feline'] },
      { emoji: '🐾', weight: 8, keywords: ['paws', 'animal', 'tracks'] },
      { emoji: '🦜', weight: 7, keywords: ['bird', 'parrot', 'feathers'] },
      { emoji: '🐠', weight: 6, keywords: ['fish', 'aquarium', 'underwater'] },
      { emoji: '🐢', weight: 6, keywords: ['turtle', 'reptile', 'slow'] },
      { emoji: '🐰', weight: 7, keywords: ['rabbit', 'bunny', 'fluffy'] }
    ],
    'Family': [
      { emoji: '👨‍👩‍👧‍👦', weight: 10, keywords: ['family', 'together', 'children'] },
      { emoji: '👶', weight: 9, keywords: ['baby', 'newborn', 'infant'] },
      { emoji: '🤱', weight: 8, keywords: ['mother', 'nursing', 'maternal'] },
      { emoji: '👨‍👧', weight: 7, keywords: ['father', 'daughter', 'dad'] },
      { emoji: '👩‍👦', weight: 7, keywords: ['mother', 'son', 'mom'] },
      { emoji: '👫', weight: 6, keywords: ['couple', 'together', 'partners'] },
      { emoji: '❤️', weight: 5, keywords: ['love', 'heart', 'romance'] }
    ],
    'Sports': [
      { emoji: '⚽', weight: 9, keywords: ['soccer', 'football', 'ball'] },
      { emoji: '🏀', weight: 9, keywords: ['basketball', 'court', 'hoop'] },
      { emoji: '🏈', weight: 9, keywords: ['football', 'nfl', 'touchdown'] },
      { emoji: '⚾', weight: 8, keywords: ['baseball', 'bat', 'catch'] },
      { emoji: '🎾', weight: 8, keywords: ['tennis', 'racket', 'court'] },
      { emoji: '🏄‍♀️', weight: 8, keywords: ['surfing', 'waves', 'beach'] },
      { emoji: '⛷️', weight: 8, keywords: ['skiing', 'snow', 'winter'] },
      { emoji: '🏅', weight: 7, keywords: ['medal', 'victory', 'champion'] }
    ],
    'Technology': [
      { emoji: '📱', weight: 10, keywords: ['phone', 'mobile', 'smart'] },
      { emoji: '💻', weight: 9, keywords: ['laptop', 'computer', 'tech'] },
      { emoji: '🖥️', weight: 8, keywords: ['desktop', 'monitor', 'screen'] },
      { emoji: '🎮', weight: 7, keywords: ['gaming', 'controller', 'console'] },
      { emoji: '📷', weight: 8, keywords: ['camera', 'photo', 'digital'] },
      { emoji: '🤖', weight: 6, keywords: ['robot', 'ai', 'automation'] },
      { emoji: '📡', weight: 5, keywords: ['satellite', 'signal', 'broadcast'] }
    ],
    'Announcement': [
      { emoji: '📢', weight: 10, keywords: ['announcement', 'news', 'attention'] },
      { emoji: '🔔', weight: 8, keywords: ['bell', 'alert', 'notification'] },
      { emoji: '📣', weight: 9, keywords: ['megaphone', 'loud', 'broadcast'] },
      { emoji: '🎯', weight: 7, keywords: ['target', 'goal', 'objective'] },
      { emoji: '🚨', weight: 6, keywords: ['alert', 'important', 'emergency'] }
    ],
    'Product': [
      { emoji: '🛍️', weight: 9, keywords: ['shopping', 'bags', 'purchase'] },
      { emoji: '🏷️', weight: 8, keywords: ['tag', 'price', 'label'] },
      { emoji: '💎', weight: 7, keywords: ['jewelry', 'gem', 'valuable'] },
      { emoji: '👕', weight: 8, keywords: ['clothing', 'shirt', 'apparel'] },
      { emoji: '📦', weight: 7, keywords: ['package', 'box', 'delivery'] },
      { emoji: '🛒', weight: 6, keywords: ['cart', 'shopping', 'checkout'] }
    ]
  };
  // Create a prompt for the OpenAI API
  const systemPrompt = `You are an assistant that generates compelling, attention-grabbing summaries of Instagram posts.
Format your response EXACTLY as follows (maintain this exact format with no deviations):

* [single emoji that best represents the content]
**@username** [compelling action description with essential details, max 15 words]
**Primary Category: Category**
**Secondary Category: Category** (omit if there's no secondary category)

Guidelines for emoji selection:
- Choose the most specific, contextually appropriate emoji that precisely matches the action/theme
- For events: 🎉 (parties), 🎤 (concerts), 🎭 (performances), 📅 (scheduled events)
- For locations: 🏔️ (mountains), 🏖️ (beaches), 🏙️ (cityscapes), 🏞️ (nature), 🏠 (homes)
- For food: Use specific food emojis (🍣 🍕 🍷) not generic ones (🍽️)
- For activities: 🏃‍♀️ (sports), 🎨 (art), 📚 (reading), 🎸 (music)
- For relationships: 👫 (couples), 👨‍👩‍👧‍👦 (family), 🐶 (pets)
- For emotions: 😂 (humor), 😢 (sadness), 🥰 (affection), 😮 (surprise)
- For milestones: 🎓 (graduation), 💍 (engagement), 🎂 (birthdays), 🏆 (achievements)
- Match the emoji precisely to the most distinctive element in the action description

Other guidelines:
- Action description MUST include event date, time, and location if present
- Use vivid, specific verbs in present tense (e.g., "flaunts" instead of "shows")
- Include the most striking/unusual/captivating detail that makes this post unique
- Prioritize concrete details over vague descriptions
- If post contains an invitation, announcement, or milestone, highlight it
- Be factual and detailed rather than generic
- DO NOT mention likes, comments, or other meta aspects
- DO NOT use hashtags
- DO NOT add any additional text, explanation, or notes`;

  const userPrompt = `Please summarize this Instagram post with attention to detail:
  
Username: ${post.username}
Caption: ${post.caption || '(No caption)'}
Media Type: ${post.mediaType}
Content Categories: Primary - ${post.contentCategories.primary}${post.contentCategories.secondary ? `, Secondary - ${post.contentCategories.secondary}` : ''}
Has Event: ${post.hasEvent ? 'Yes' : 'No'}
${post.hasEvent && post.eventKeywords ? `Event Keywords: ${post.eventKeywords.join(', ')}` : ''}

IMPORTANT: If this post mentions event details (date, time, location), you MUST include them in your summary.
Capture the most compelling aspect of this post while being specific and detailed.
Remember: Output ONLY the formatted summary in the exact format specified.`;

  try {
    // Call the OpenAI API
    const chatCompletion = await openai.chat.completions.create({
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt }
      ],
      model: 'gpt-4-turbo-preview',
      temperature: 0.6, // Slightly lower temperature for more factual responses
      max_tokens: 120, // Increased token limit to accommodate more detailed summaries
      presence_penalty: 0.1, // Slight penalty to avoid repetitive patterns
      frequency_penalty: 0.1 // Slight penalty to discourage overused phrases
    });

    // Extract the summary
    const summary = chatCompletion.choices[0]?.message?.content?.trim() || '';
    
    // Parse the summary to extract components
    const emojiMatch = summary.match(/\* ([\p{Emoji}])/u);
    const usernameActionMatch = summary.match(/\*\*@([^\*]+)\*\* ([^\n]+)/);
    const primaryCategoryMatch = summary.match(/\*\*Primary Category: ([^\*]+)\*\*/);
    const secondaryCategoryMatch = summary.match(/\*\*Secondary Category: ([^\*]+)\*\*/);
    
    // Select emoji from AI-generated content or fall back to smart category-based selection
    let emoji = emojiMatch?.[1] || '';
    
    // If no emoji was extracted from AI response, use weighted selection from our mapping
    if (!emoji) {
      const category = post.contentCategories.primary;
      if (category && categoryEmojiMap[category]) {
        // First try to match keywords from action description with our emoji mappings
        const actionDesc = usernameActionMatch?.[2] || '';
        const categoryEmojis = categoryEmojiMap[category];
        let bestEmoji = null;
        let highestScore = -1;
        
        // Find keywords in the action description and match against our emoji keywords
        for (const emojiMap of categoryEmojis) {
          let score = emojiMap.weight; // Start with base weight
          
          // Increase score if keywords are present in action description
          for (const keyword of emojiMap.keywords) {
            if (actionDesc.toLowerCase().includes(keyword.toLowerCase())) {
              score += 3; // Boost score when keyword is found
            }
          }
          
          // Also check post caption for keywords
          for (const keyword of emojiMap.keywords) {
            if (post.caption && post.caption.toLowerCase().includes(keyword.toLowerCase())) {
              score += 1; // Smaller boost for caption matches
            }
          }
          
          if (score > highestScore) {
            highestScore = score;
            bestEmoji = emojiMap.emoji;
          }
        }
        
        // Use the best matching emoji or highest weighted one if no matches
        emoji = bestEmoji || categoryEmojis[0].emoji;
      } else {
        // Generic fallback if no category matches
        emoji = '📱';
      }
    }
    
    return {
      postId: post.postId,
      username: post.username,
      emoji: emoji,
      actionDescription: usernameActionMatch?.[2] || 'shared a post',
      primaryCategory: primaryCategoryMatch?.[1] || post.contentCategories.primary,
      secondaryCategory: secondaryCategoryMatch?.[1] || post.contentCategories.secondary,
      originalCaption: post.caption || '',
      originalScore: post.importance.score,
      originalPriority: post.importance.priority
    };
  } catch (error) {
    console.error('Error generating summary with OpenAI:', error);
    
    // Return a fallback summary with intelligent emoji selection based on category
    const category = post.contentCategories.primary;
    let fallbackEmoji = '📱'; // Default generic emoji
    
    // Try to select a relevant emoji based on the post category
    if (category && categoryEmojiMap[category]) {
      // Get the highest weighted emoji for this category
      const categoryEmojis = categoryEmojiMap[category];
      categoryEmojis.sort((a, b) => b.weight - a.weight);
      fallbackEmoji = categoryEmojis[0].emoji;
    }
    
    return {
      postId: post.postId,
      username: post.username,
      emoji: fallbackEmoji,
      actionDescription: 'shared a post',
      primaryCategory: post.contentCategories.primary,
      secondaryCategory: post.contentCategories.secondary,
      originalCaption: post.caption || '',
      originalScore: post.importance.score,
      originalPriority: post.importance.priority
    };
  }
}

/**
 * Generate summaries for multiple posts
 */
export async function generatePostSummaries(posts: any[]): Promise<PostSummary[]> {
  const summaries: PostSummary[] = [];
  
  // Process posts sequentially to avoid rate limits
  for (const post of posts) {
    try {
      const summary = await generatePostSummary(post);
      summaries.push(summary);
    } catch (error) {
      console.error(`Error generating summary for post ${post.postId}:`, error);
    }
    
    // Add a small delay between requests to avoid rate limits
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  
  return summaries;
}

export default {
  generatePostSummary,
  generatePostSummaries
};