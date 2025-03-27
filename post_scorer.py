from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import re
from dataclasses import dataclass

@dataclass
class Post:
    post_id: str
    user_id: str
    is_close_friend: bool
    is_verified: bool
    caption: Optional[str]
    engagement_count: int
    follower_count: int
    created_at: datetime
    has_event_indicators: bool = False
    event_keywords: List[str] = None

class PostScorer:
    def __init__(self):
        # Component weights for final score calculation
        self.weights = {
            'user_signal': 0.3,
            'content_signal': 0.25,
            'keyword_relevance': 0.2,
            'engagement_ratio': 0.15,
            'recency': 0.1
        }
        
        # Event indicator patterns
        self.event_patterns = [
            r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',  # Date patterns
            r'\b\d{1,2}:\d{2}\s*(?:AM|PM)?\b',      # Time patterns
            r'\b\d{1,3}\s+[A-Za-z\s,]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)\b',  # Address patterns
            r'\b(?:RSVP|register|sign up|tickets|event|meeting|conference|workshop)\b'  # Event keywords
        ]
        
        # Engagement thresholds
        self.engagement_thresholds = {
            'high': 0.05,    # 5% of followers
            'medium': 0.02,  # 2% of followers
            'low': 0.01      # 1% of followers
        }

    def calculate_user_signal_weight(self, post: Post) -> float:
        """Calculate weight based on user relationship and verification status."""
        if post.is_close_friend:
            return 1.0
        elif post.is_verified:
            return 0.3
        else:
            return 0.7

    def calculate_content_signal_weight(self, post: Post) -> float:
        """Calculate weight based on caption presence and quality."""
        if not post.caption:
            # If no caption, weight depends on engagement
            engagement_ratio = post.engagement_count / post.follower_count
            if engagement_ratio >= self.engagement_thresholds['high']:
                return 0.4
            return 0.2
        
        if post.has_event_indicators:
            return 1.0
        return 0.6

    def calculate_keyword_relevance_weight(self, post: Post) -> float:
        """Calculate weight based on presence of event-related keywords."""
        if post.has_event_indicators:
            return 1.0
        elif post.event_keywords and len(post.event_keywords) > 0:
            return 0.8
        return 0.2

    def calculate_engagement_ratio_weight(self, post: Post) -> float:
        """Calculate weight based on engagement ratio."""
        engagement_ratio = post.engagement_count / post.follower_count
        
        if engagement_ratio >= self.engagement_thresholds['high']:
            return 0.8
        elif engagement_ratio >= self.engagement_thresholds['medium']:
            return 0.5
        return 0.2

    def calculate_recency_weight(self, post: Post) -> float:
        """Calculate weight based on post recency."""
        now = datetime.now()
        days_old = (now - post.created_at).days
        
        if days_old == 0:
            return 1.0
        elif days_old <= 7:
            return 0.8
        elif days_old <= 30:
            return 0.5
        return 0.2

    def detect_event_indicators(self, text: str) -> Tuple[bool, List[str]]:
        """Detect event indicators in text and return found keywords."""
        if not text:
            return False, []
        
        found_keywords = []
        has_indicators = False
        
        for pattern in self.event_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                has_indicators = True
                found_keywords.extend(matches)
        
        return has_indicators, found_keywords

    def calculate_final_score(self, post: Post) -> float:
        """Calculate the final weighted score for a post."""
        # Calculate individual component weights
        user_weight = self.calculate_user_signal_weight(post)
        content_weight = self.calculate_content_signal_weight(post)
        keyword_weight = self.calculate_keyword_relevance_weight(post)
        engagement_weight = self.calculate_engagement_ratio_weight(post)
        recency_weight = self.calculate_recency_weight(post)
        
        # Calculate final weighted score
        final_score = (
            user_weight * self.weights['user_signal'] +
            content_weight * self.weights['content_signal'] +
            keyword_weight * self.weights['keyword_relevance'] +
            engagement_weight * self.weights['engagement_ratio'] +
            recency_weight * self.weights['recency']
        )
        
        return round(final_score, 3)

    def score_post(self, post: Post) -> Dict[str, float]:
        """Score a post and return detailed component scores."""
        # Detect event indicators in caption if present
        if post.caption:
            has_indicators, keywords = self.detect_event_indicators(post.caption)
            post.has_event_indicators = has_indicators
            post.event_keywords = keywords
        
        # Calculate component scores
        component_scores = {
            'user_signal': self.calculate_user_signal_weight(post),
            'content_signal': self.calculate_content_signal_weight(post),
            'keyword_relevance': self.calculate_keyword_relevance_weight(post),
            'engagement_ratio': self.calculate_engagement_ratio_weight(post),
            'recency': self.calculate_recency_weight(post)
        }
        
        # Calculate final score
        final_score = self.calculate_final_score(post)
        
        return {
            'component_scores': component_scores,
            'final_score': final_score
        }

# Example usage
if __name__ == "__main__":
    # Create a sample post
    sample_post = Post(
        post_id="123",
        user_id="user1",
        is_close_friend=True,
        is_verified=False,
        caption="Join us tomorrow at 2 PM at 123 Main Street for our workshop!",
        engagement_count=1000,
        follower_count=10000,
        created_at=datetime.now()
    )
    
    # Initialize scorer and calculate scores
    scorer = PostScorer()
    scores = scorer.score_post(sample_post)
    
    # Print results
    print("Component Scores:")
    for component, score in scores['component_scores'].items():
        print(f"{component}: {score}")
    print(f"\nFinal Score: {scores['final_score']}") 