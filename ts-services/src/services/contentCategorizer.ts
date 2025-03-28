/**
 * Service for categorizing Instagram posts by content type
 */

// Content category types
export enum ContentCategory {
  EVENT = 'Event',
  SELFIE = 'Selfie',
  PORTRAIT = 'Portrait',
  GROUP_PHOTO = 'Group Photo',
  FOOD = 'Food',
  TRAVEL = 'Travel',
  NATURE = 'Nature',
  ANIMAL = 'Animal',
  ART = 'Art',
  FASHION = 'Fashion',
  FITNESS = 'Fitness',
  MUSIC = 'Music',
  MEME = 'Meme',
  QUOTE = 'Quote',
  PRODUCT = 'Product',
  TECHNOLOGY = 'Technology',
  SPORTS = 'Sports',
  POLITICAL = 'Political',
  NEWS = 'News',
  ADVERTISEMENT = 'Advertisement',
  ANNOUNCEMENT = 'Announcement',
  REVIEW = 'Review',
  EXHIBITION = 'Exhibition',
  WORKSHOP = 'Workshop',
  EDUCATIONAL = 'Educational',
  LIFESTYLE = 'Lifestyle',
  BEAUTY = 'Beauty',
  OTHER = 'Other'
}

// Post categorization result
export interface CategoryResult {
  primary: ContentCategory;
  secondary?: ContentCategory;
  confidence: number;
  hashtags: string[];
}

/**
 * Content categorization service
 */
export class ContentCategorizer {
  // Keyword patterns for different categories
  private categoryPatterns: Record<ContentCategory, RegExp[]> = {
    [ContentCategory.EVENT]: [
      /\b(?:event|concert|festival|show|performance|conference|meetup|gathering|party|celebration)\b/i,
      /\b(?:tomorrow|tonight|today at|join us|upcoming|this weekend)\b/i,
      /\bon\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)/i,
      /\b(?:\d{1,2}(?::\d{2})?(?:\s*[ap]m)?|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2})\b/i,
    ],
    [ContentCategory.SELFIE]: [
      /\b(?:selfie|me|myself|self[- ]portrait)\b/i,
      /\b(?:#selfie|#me|#myself|#selftime|#selfportrait|#myface)\b/i,
    ],
    [ContentCategory.PORTRAIT]: [
      /\b(?:portrait|headshot|profile)\b/i,
      /\b(?:#portrait|#portraitphotography|#model)\b/i,
    ],
    [ContentCategory.GROUP_PHOTO]: [
      /\b(?:group|squad|team|crew|friends|family|together|us|we)\b/i,
      /\b(?:#squadgoals|#friendsforever|#family|#crew)\b/i,
    ],
    [ContentCategory.FOOD]: [
      /\b(?:food|meal|dinner|lunch|breakfast|dish|restaurant|recipe|delicious|tasty|yummy|chef|cooking|baking|cuisine)\b/i,
      /\b(?:#foodporn|#foodie|#instafood|#yummy|#delicious|#homemade|#recipe)\b/i,
    ],
    [ContentCategory.TRAVEL]: [
      /\b(?:travel|trip|journey|adventure|explore|destination|wanderlust|vacation|holiday|tourism|tourist|sightseeing)\b/i,
      /\b(?:#travel|#wanderlust|#adventure|#explore|#travelgram|#vacation|#trip)\b/i,
    ],
    [ContentCategory.NATURE]: [
      /\b(?:nature|landscape|outdoor|mountain|beach|ocean|sea|lake|river|forest|tree|hiking|sunset|sunrise|sky)\b/i,
      /\b(?:#nature|#naturephotography|#landscape|#outdoors|#naturelovers|#sunset)\b/i,
    ],
    [ContentCategory.ANIMAL]: [
      /\b(?:animal|pet|dog|cat|bird|wildlife|zoo|fish|puppy|kitten)\b/i,
      /\b(?:#animal|#pet|#dog|#cat|#puppy|#kitten|#wildlife|#dogsofinstagram|#catsofinstagram)\b/i,
    ],
    [ContentCategory.ART]: [
      /\b(?:art|artist|painting|drawing|sculpture|creative|sketch|illustration|design|artistic|gallery)\b/i,
      /\b(?:#art|#artist|#artwork|#creative|#illustration|#painting|#drawing)\b/i,
    ],
    [ContentCategory.FASHION]: [
      /\b(?:fashion|style|outfit|clothes|clothing|dress|shoes|accessory|accessories|model|designer|brand)\b/i,
      /\b(?:#fashion|#style|#outfit|#ootd|#outfitoftheday|#clothes|#stylish)\b/i,
    ],
    [ContentCategory.FITNESS]: [
      /\b(?:fitness|workout|gym|exercise|training|fit|health|healthy|run|running|yoga|body|muscle|strength)\b/i,
      /\b(?:#fitness|#workout|#gym|#fit|#fitfam|#training|#healthylifestyle)\b/i,
    ],
    [ContentCategory.MUSIC]: [
      /\b(?:music|song|singer|band|concert|album|release|track|artist|sing|singing|lyrics|guitar|piano|drum|musician)\b/i,
      /\b(?:#music|#musician|#singer|#band|#newmusic|#song|#livemusic|#concert)\b/i,
    ],
    [ContentCategory.MEME]: [
      /\b(?:meme|joke|humor|funny|lol|lmao|rofl|comedy|hilarious)\b/i,
      /\b(?:#meme|#memes|#funny|#humor|#lol|#joke|#comedy)\b/i,
    ],
    [ContentCategory.QUOTE]: [
      /\b(?:quote|quotes|wisdom|words|saying|inspiration|motivational|motivation)\b/i,
      /\b(?:#quote|#quotes|#qotd|#quoteoftheday|#words|#wisdom|#inspiration)\b/i,
      /[""].*[""]/, // Quoted text
    ],
    [ContentCategory.PRODUCT]: [
      /\b(?:product|buy|purchase|sale|discount|offer|shop|shopping|store|price|quality|brand|limited)\b/i,
      /\b(?:#product|#shopping|#sale|#discount|#offer|#shop|#buy|#newproduct)\b/i,
    ],
    [ContentCategory.TECHNOLOGY]: [
      /\b(?:technology|tech|software|hardware|app|gadget|device|computer|phone|mobile|digital|code|coding|program|innovation)\b/i,
      /\b(?:#technology|#tech|#software|#coding|#programming|#developer|#innovation)\b/i,
    ],
    [ContentCategory.SPORTS]: [
      /\b(?:sport|sports|game|match|team|player|football|soccer|basketball|baseball|tennis|golf|championship|tournament|league|competition)\b/i,
      /\b(?:#sports|#sport|#football|#soccer|#basketball|#baseball|#tennis|#game|#match)\b/i,
    ],
    [ContentCategory.POLITICAL]: [
      /\b(?:politic|political|government|election|vote|policy|politician|president|minister|campaign|protest|democracy)\b/i,
      /\b(?:#politics|#political|#election|#vote|#democracy|#government|#campaign)\b/i,
    ],
    [ContentCategory.NEWS]: [
      /\b(?:news|breaking|announcement|report|update|latest|headlines|current events)\b/i,
      /\b(?:#news|#breakingnews|#update|#currentevents|#headlines|#today)\b/i,
    ],
    [ContentCategory.ADVERTISEMENT]: [
      /\b(?:ad|ads|advert|advertisement|sponsor|sponsored|promotion|promotional|collab|collaboration|partner|partnership)\b/i,
      /\b(?:#ad|#sponsored|#promotion|#collab|#partnership|#sponsored|#paidpartnership)\b/i,
    ],
    [ContentCategory.ANNOUNCEMENT]: [
      /\b(?:announcement|announcing|reveal|introducing|launch|new|coming soon|sneak peek|preview)\b/i,
      /\b(?:#announcement|#newarrival|#comingsoon|#sneakpeek|#launch|#introducing)\b/i,
    ],
    [ContentCategory.REVIEW]: [
      /\b(?:review|rating|recommend|experience|tried|opinion|thoughts|verdict)\b/i,
      /\b(?:#review|#productreview|#bookreview|#moviereview|#recommendation|#honest)\b/i,
    ],
    [ContentCategory.EXHIBITION]: [
      /\b(?:exhibition|exhibit|gallery|museum|showcase|display|art show|installation)\b/i,
      /\b(?:#exhibition|#exhibit|#gallery|#museum|#artshow|#installation)\b/i,
    ],
    [ContentCategory.WORKSHOP]: [
      /\b(?:workshop|class|session|training|learn|teach|tutorial|lesson|seminar|webinar)\b/i,
      /\b(?:#workshop|#class|#learning|#teaching|#tutorial|#seminar|#webinar)\b/i,
    ],
    [ContentCategory.EDUCATIONAL]: [
      /\b(?:education|educational|learn|learning|knowledge|study|student|school|university|college|course|degree|academic)\b/i,
      /\b(?:#education|#learning|#knowledge|#study|#student|#school|#university)\b/i,
    ],
    [ContentCategory.LIFESTYLE]: [
      /\b(?:lifestyle|life|living|daily|everyday|routine|habits|home|house|apartment|decor|interior)\b/i,
      /\b(?:#lifestyle|#life|#dailylife|#everyday|#home|#decor|#interior)\b/i,
    ],
    [ContentCategory.BEAUTY]: [
      /\b(?:beauty|makeup|skincare|cosmetic|cosmetics|hair|face|skin|lipstick|mascara|eyeshadow|foundation|nail|nails)\b/i,
      /\b(?:#beauty|#makeup|#skincare|#cosmetics|#hair|#skin|#mua)\b/i,
    ],
    [ContentCategory.OTHER]: [
      /.+/i, // Match anything (fallback)
    ],
  };

  /**
   * Extract hashtags from a post caption
   */
  private extractHashtags(caption: string): string[] {
    if (!caption) return [];
    
    const hashtagRegex = /#[\w\u0590-\u05ff]+/g;
    const matches = caption.match(hashtagRegex);
    return matches || [];
  }

  /**
   * Categorize a post based on its caption and metadata
   */
  public categorizePost(
    caption: string, 
    mediaType: string,
    hasEventIndicators: boolean
  ): CategoryResult {
    if (!caption) {
      return {
        primary: ContentCategory.OTHER,
        confidence: 0.3,
        hashtags: []
      };
    }

    // Extract hashtags
    const hashtags = this.extractHashtags(caption);
    
    // Start with event detection from post score analysis
    if (hasEventIndicators) {
      // Check if it's a specific type of event
      if (this.matchCategory(caption, ContentCategory.EXHIBITION)) {
        return {
          primary: ContentCategory.EXHIBITION,
          secondary: ContentCategory.EVENT,
          confidence: 0.9,
          hashtags
        };
      } else if (this.matchCategory(caption, ContentCategory.WORKSHOP)) {
        return {
          primary: ContentCategory.WORKSHOP,
          secondary: ContentCategory.EVENT,
          confidence: 0.9,
          hashtags
        };
      } else if (this.matchCategory(caption, ContentCategory.MUSIC)) {
        return {
          primary: ContentCategory.MUSIC,
          secondary: ContentCategory.EVENT,
          confidence: 0.85,
          hashtags
        };
      }
      
      return {
        primary: ContentCategory.EVENT,
        confidence: 0.85,
        hashtags
      };
    }
    
    // Calculate category scores
    const scores: Record<ContentCategory, number> = {} as Record<ContentCategory, number>;
    
    for (const category of Object.values(ContentCategory)) {
      if (category === ContentCategory.OTHER) continue; // Skip OTHER as it's a fallback
      
      scores[category] = this.calculateCategoryScore(caption, category, hashtags);
    }
    
    // Find top two categories
    const sortedCategories = Object.entries(scores)
      .sort((a, b) => b[1] - a[1])
      .filter(([_, score]) => score > 0);
    
    if (sortedCategories.length === 0) {
      return {
        primary: ContentCategory.OTHER,
        confidence: 0.3,
        hashtags
      };
    }
    
    const [primaryCategory, primaryScore] = sortedCategories[0];
    
    if (sortedCategories.length > 1) {
      const [secondaryCategory, secondaryScore] = sortedCategories[1];
      
      // Only include secondary if it's reasonably strong
      if (secondaryScore > 0.3) {
        return {
          primary: primaryCategory as ContentCategory,
          secondary: secondaryCategory as ContentCategory,
          confidence: primaryScore,
          hashtags
        };
      }
    }
    
    return {
      primary: primaryCategory as ContentCategory,
      confidence: primaryScore,
      hashtags
    };
  }

  /**
   * Calculate a score for how strongly a caption matches a category
   */
  private calculateCategoryScore(caption: string, category: ContentCategory, hashtags: string[]): number {
    let score = 0;
    const patterns = this.categoryPatterns[category];
    
    // Check for category patterns in caption
    for (const pattern of patterns) {
      const matches = caption.match(pattern);
      if (matches) {
        score += 0.2 * matches.length;
      }
    }
    
    // Check hashtags against common category hashtags
    const hashtagText = hashtags.join(' ');
    for (const pattern of patterns) {
      const matches = hashtagText.match(pattern);
      if (matches) {
        score += 0.3 * matches.length;
      }
    }
    
    // Add specific logic for certain categories
    if (category === ContentCategory.SELFIE && /\b(?:i|me|my|mine|myself)\b/i.test(caption)) {
      score += 0.3;
    }
    
    // Cap the score at 1.0
    return Math.min(score, 1.0);
  }

  /**
   * Check if a caption strongly matches a specific category
   */
  private matchCategory(caption: string, category: ContentCategory): boolean {
    const patterns = this.categoryPatterns[category];
    let matches = 0;
    
    for (const pattern of patterns) {
      if (pattern.test(caption)) {
        matches++;
      }
    }
    
    return matches >= 2; // Require at least 2 pattern matches for a strong match
  }
}

export default new ContentCategorizer();