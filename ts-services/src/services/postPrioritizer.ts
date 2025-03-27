import { Post, ScoreResult } from './postScorer.js';

/**
 * Priority levels for categorizing posts
 */
export enum PriorityLevel {
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low'
}

/**
 * Output from the post prioritizer
 */
export interface PriorityResult {
  level: PriorityLevel;
  reason: string;
  score: number;
}

/**
 * Decision tree-based post prioritizer
 */
export class PostPrioritizer {
  // Threshold values for different aspects of the decision tree
  private thresholds = {
    // Final score thresholds
    score: {
      high: 0.75,
      medium: 0.5
    },
    // Individual component thresholds
    closeFriend: true,
    hasEvent: true,
    recentDays: 2,
    engagementRatio: 0.03  // 3% of followers
  };

  /**
   * Categorize a post into High, Medium, or Low priority
   * based on its score and key attributes
   */
  public prioritize(post: Post, scoreResult: ScoreResult): PriorityResult {
    // First check for automatic high priority conditions
    if (post.isCloseFriend) {
      return {
        level: PriorityLevel.HIGH,
        reason: 'From close friend',
        score: scoreResult.finalScore
      };
    }
    
    if (post.hasEventIndicators) {
      return {
        level: PriorityLevel.HIGH,
        reason: 'Contains event details',
        score: scoreResult.finalScore
      };
    }
    
    // Check if the post is very recent (within last 2 days)
    const now = new Date();
    const postDate = post.createdAt;
    const daysDiff = Math.floor((now.getTime() - postDate.getTime()) / (1000 * 60 * 60 * 24));
    const isVeryRecent = daysDiff <= this.thresholds.recentDays;
    
    // Check high engagement
    const engagementRatio = post.engagementCount / post.followerCount;
    const hasHighEngagement = engagementRatio >= this.thresholds.engagementRatio;
    
    // Check final score thresholds
    if (scoreResult.finalScore >= this.thresholds.score.high) {
      return {
        level: PriorityLevel.HIGH,
        reason: 'High overall score',
        score: scoreResult.finalScore
      };
    } else if (scoreResult.finalScore >= this.thresholds.score.medium) {
      if (isVeryRecent || hasHighEngagement) {
        return {
          level: PriorityLevel.HIGH,
          reason: isVeryRecent ? 'Recent post with good score' : 'High engagement post',
          score: scoreResult.finalScore
        };
      }
      
      return {
        level: PriorityLevel.MEDIUM,
        reason: 'Medium overall score',
        score: scoreResult.finalScore
      };
    } else {
      // For low scores, still check if it's very recent or has high engagement
      if (isVeryRecent && hasHighEngagement) {
        return {
          level: PriorityLevel.MEDIUM,
          reason: 'Recent post with high engagement',
          score: scoreResult.finalScore
        };
      }
      
      if (isVeryRecent || hasHighEngagement) {
        return {
          level: PriorityLevel.MEDIUM,
          reason: isVeryRecent ? 'Very recent post' : 'Post with high engagement',
          score: scoreResult.finalScore
        };
      }
      
      return {
        level: PriorityLevel.LOW,
        reason: 'Low overall score',
        score: scoreResult.finalScore
      };
    }
  }

  /**
   * Set custom threshold values
   */
  public setThresholds(newThresholds: Partial<typeof this.thresholds>): void {
    this.thresholds = {
      ...this.thresholds,
      ...newThresholds
    };
  }

  /**
   * Get current threshold values
   */
  public getThresholds(): typeof this.thresholds {
    return { ...this.thresholds };
  }
}

/**
 * The decision tree logic can be described as:
 * 
 * 1. Is the post from a close friend?
 *    -> Yes: HIGH PRIORITY
 *    -> No: Continue
 * 
 * 2. Does the post contain event indicators?
 *    -> Yes: HIGH PRIORITY
 *    -> No: Continue
 * 
 * 3. Is the post score >= 0.75?
 *    -> Yes: HIGH PRIORITY
 *    -> No: Continue
 * 
 * 4. Is the post score >= 0.5?
 *    -> Yes: 
 *        4a. Is the post very recent (≤ 2 days) OR has high engagement (≥ 3%)?
 *            -> Yes: HIGH PRIORITY
 *            -> No: MEDIUM PRIORITY
 *    -> No: Continue
 * 
 * 5. Is the post very recent AND has high engagement?
 *    -> Yes: MEDIUM PRIORITY
 *    -> No: Continue
 * 
 * 6. Is the post very recent OR has high engagement?
 *    -> Yes: MEDIUM PRIORITY
 *    -> No: LOW PRIORITY
 */

export default new PostPrioritizer();