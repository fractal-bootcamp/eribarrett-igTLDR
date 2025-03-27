export interface Post {
    postId: string;
    userId: string;
    isCloseFriend: boolean;
    isVerified: boolean;
    caption?: string;
    engagementCount: number;
    followerCount: number;
    createdAt: Date;
    hasEventIndicators?: boolean;
    eventKeywords?: string[];
}

export interface ComponentScores {
    userSignal: number;
    contentSignal: number;
    keywordRelevance: number;
    engagementRatio: number;
    recency: number;
}

export interface ScoreResult {
    componentScores: ComponentScores;
    finalScore: number;
}

export class PostScorer {
    private weights: Record<string, number> = {
        userSignal: 0.3,
        contentSignal: 0.25,
        keywordRelevance: 0.2,
        engagementRatio: 0.15,
        recency: 0.1
    };

    private eventPatterns: RegExp[] = [
        /\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b/,  // Date patterns
        /\b\d{1,2}:\d{2}\s*(?:AM|PM)?\b/,      // Time patterns
        /\b\d{1,3}\s+[A-Za-z\s,]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)\b/,  // Address patterns
        /\b(?:RSVP|register|sign up|tickets|event|meeting|conference|workshop)\b/  // Event keywords
    ];

    private engagementThresholds: Record<string, number> = {
        high: 0.05,    // 5% of followers
        medium: 0.02,  // 2% of followers
        low: 0.01      // 1% of followers
    };

    private calculateUserSignalWeight(post: Post): number {
        if (post.isCloseFriend) {
            return 1.0;
        } else if (post.isVerified) {
            return 0.3;
        }
        return 0.7;
    }

    private calculateContentSignalWeight(post: Post): number {
        if (!post.caption) {
            const engagementRatio = post.engagementCount / post.followerCount;
            if (engagementRatio >= this.engagementThresholds.high) {
                return 0.4;
            }
            return 0.2;
        }

        if (post.hasEventIndicators) {
            return 1.0;
        }
        return 0.6;
    }

    private calculateKeywordRelevanceWeight(post: Post): number {
        if (post.hasEventIndicators) {
            return 1.0;
        } else if (post.eventKeywords && post.eventKeywords.length > 0) {
            return 0.8;
        }
        return 0.2;
    }

    private calculateEngagementRatioWeight(post: Post): number {
        const engagementRatio = post.engagementCount / post.followerCount;

        if (engagementRatio >= this.engagementThresholds.high) {
            return 0.8;
        } else if (engagementRatio >= this.engagementThresholds.medium) {
            return 0.5;
        }
        return 0.2;
    }

    private calculateRecencyWeight(post: Post): number {
        const now = new Date();
        const daysOld = Math.floor((now.getTime() - post.createdAt.getTime()) / (1000 * 60 * 60 * 24));

        if (daysOld === 0) {
            return 1.0;
        } else if (daysOld <= 7) {
            return 0.8;
        } else if (daysOld <= 30) {
            return 0.5;
        }
        return 0.2;
    }

    private detectEventIndicators(text: string): [boolean, string[]] {
        if (!text) {
            return [false, []];
        }

        const foundKeywords: string[] = [];
        let hasIndicators = false;

        for (const pattern of this.eventPatterns) {
            const matches = text.match(pattern);
            if (matches) {
                hasIndicators = true;
                foundKeywords.push(...matches);
            }
        }

        return [hasIndicators, foundKeywords];
    }

    private calculateFinalScore(post: Post): number {
        const userWeight = this.calculateUserSignalWeight(post);
        const contentWeight = this.calculateContentSignalWeight(post);
        const keywordWeight = this.calculateKeywordRelevanceWeight(post);
        const engagementWeight = this.calculateEngagementRatioWeight(post);
        const recencyWeight = this.calculateRecencyWeight(post);

        const finalScore = (
            userWeight * this.weights.userSignal +
            contentWeight * this.weights.contentSignal +
            keywordWeight * this.weights.keywordRelevance +
            engagementWeight * this.weights.engagementRatio +
            recencyWeight * this.weights.recency
        );

        return Number(finalScore.toFixed(3));
    }

    public scorePost(post: Post): ScoreResult {
        // Detect event indicators in caption if present
        if (post.caption) {
            const [hasIndicators, keywords] = this.detectEventIndicators(post.caption);
            post.hasEventIndicators = hasIndicators;
            post.eventKeywords = keywords;
        }

        // Calculate component scores
        const componentScores: ComponentScores = {
            userSignal: this.calculateUserSignalWeight(post),
            contentSignal: this.calculateContentSignalWeight(post),
            keywordRelevance: this.calculateKeywordRelevanceWeight(post),
            engagementRatio: this.calculateEngagementRatioWeight(post),
            recency: this.calculateRecencyWeight(post)
        };

        // Calculate final score
        const finalScore = this.calculateFinalScore(post);

        return {
            componentScores,
            finalScore
        };
    }
}