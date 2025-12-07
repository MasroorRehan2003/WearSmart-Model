"""
Adaptive Learning Module
Simulates AI model learning from user feedback for demonstration purposes
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Tuple
import random

class AdaptiveLearningModel:
    """Simulates an adaptive AI model that improves based on user feedback"""
    
    def __init__(self, learning_log_path: str = "adaptive_learning_log.json"):
        self.learning_log_path = learning_log_path
        self.learning_data = self._load_learning_data()
        
    def _load_learning_data(self) -> Dict:
        """Load existing learning data or create new structure"""
        if os.path.exists(self.learning_log_path):
            try:
                with open(self.learning_log_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "total_feedback": 0,
            "positive_feedback": 0,
            "negative_feedback": 0,
            "learning_improvements": [],
            "user_preferences": {},
            "model_confidence": 0.75,
            "last_updated": None
        }
    
    def _save_learning_data(self):
        """Save learning data to file"""
        self.learning_data["last_updated"] = datetime.now().isoformat()
        with open(self.learning_log_path, 'w') as f:
            json.dump(self.learning_data, f, indent=2)
    
    def process_user_feedback(self, feedback_data: Dict) -> str:
        """Process user feedback and simulate model learning"""
        try:
            # Extract feedback information
            liked = feedback_data.get("liked", "no").lower() == "yes"
            gender = feedback_data.get("gender", "unknown")
            season = feedback_data.get("season", "unknown")
            occasion = feedback_data.get("occasion", "unknown")
            top_label = feedback_data.get("top_label", "")
            bottom_label = feedback_data.get("bottom_label", "")
            outer_label = feedback_data.get("outer_label", "")
            
            # Update counters
            self.learning_data["total_feedback"] += 1
            if liked:
                self.learning_data["positive_feedback"] += 1
            else:
                self.learning_data["negative_feedback"] += 1
            
            # Simulate learning improvements
            improvement = self._simulate_learning_improvement(feedback_data)
            self.learning_data["learning_improvements"].append(improvement)
            
            # Update user preferences
            self._update_user_preferences(feedback_data)
            
            # Simulate model confidence improvement
            self._update_model_confidence()
            
            # Save learning data
            self._save_learning_data()
            
            return self._generate_learning_message(improvement)
            
        except Exception as e:
            return f"❌ Error processing feedback: {str(e)}"
    
    def _simulate_learning_improvement(self, feedback_data: Dict) -> Dict:
        """Simulate a learning improvement based on feedback"""
        liked = feedback_data.get("liked", "no").lower() == "yes"
        gender = feedback_data.get("gender", "unknown")
        season = feedback_data.get("season", "unknown")
        
        improvements = []
        
        if liked:
            # Positive feedback - model learns what works
            if gender == "men":
                improvements.append(f"✅ Learned: Men prefer {feedback_data.get('top_label', 'tops')} in {season}")
            elif gender == "women":
                improvements.append(f"✅ Learned: Women prefer {feedback_data.get('top_label', 'tops')} in {season}")
            
            improvements.append(f"📈 Improved accuracy for {season} season recommendations")
            improvements.append(f"🎯 Enhanced {feedback_data.get('occasion', 'casual')} occasion predictions")
        else:
            # Negative feedback - model learns what to avoid
            improvements.append(f"⚠️ Learned: Avoid {feedback_data.get('top_label', 'tops')} + {feedback_data.get('bottom_label', 'bottoms')} combination")
            improvements.append(f"🔄 Adjusted weights for {season} season")
            improvements.append(f"📉 Reduced confidence in {feedback_data.get('occasion', 'casual')} predictions")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "feedback_type": "positive" if liked else "negative",
            "improvements": improvements,
            "confidence_change": random.uniform(0.01, 0.05) if liked else random.uniform(-0.03, -0.01)
        }
    
    def _update_user_preferences(self, feedback_data: Dict):
        """Update user preference patterns"""
        gender = feedback_data.get("gender", "unknown")
        season = feedback_data.get("season", "unknown")
        occasion = feedback_data.get("occasion", "unknown")
        
        if gender not in self.learning_data["user_preferences"]:
            self.learning_data["user_preferences"][gender] = {}
        
        if season not in self.learning_data["user_preferences"][gender]:
            self.learning_data["user_preferences"][gender][season] = {}
        
        if occasion not in self.learning_data["user_preferences"][gender][season]:
            self.learning_data["user_preferences"][gender][season][occasion] = {
                "positive": 0,
                "negative": 0,
                "preferred_items": []
            }
        
        pref = self.learning_data["user_preferences"][gender][season][occasion]
        if feedback_data.get("liked", "no").lower() == "yes":
            pref["positive"] += 1
            # Add preferred items
            for item in [feedback_data.get('top_label'), feedback_data.get('bottom_label'), feedback_data.get('outer_label')]:
                if item and item not in pref["preferred_items"]:
                    pref["preferred_items"].append(item)
        else:
            pref["negative"] += 1
    
    def _update_model_confidence(self):
        """Simulate model confidence updates"""
        total = self.learning_data["total_feedback"]
        positive = self.learning_data["positive_feedback"]
        
        if total > 0:
            # Base confidence on positive feedback ratio
            base_confidence = positive / total
            
            # Add some randomness to simulate learning fluctuations
            noise = random.uniform(-0.05, 0.05)
            self.learning_data["model_confidence"] = max(0.5, min(0.95, base_confidence + noise))
    
    def _generate_learning_message(self, improvement: Dict) -> str:
        """Generate a user-friendly learning message"""
        improvements = improvement["improvements"]
        confidence_change = improvement["confidence_change"]
        
        message = "🧠 **Adaptive Learning Update**\n\n"
        message += f"📊 **Total Feedback Processed:** {self.learning_data['total_feedback']}\n"
        message += f"✅ **Positive Feedback:** {self.learning_data['positive_feedback']}\n"
        message += f"❌ **Negative Feedback:** {self.learning_data['negative_feedback']}\n"
        message += f"🎯 **Model Confidence:** {self.learning_data['model_confidence']:.2%}\n\n"
        
        message += "📈 **Recent Learning Improvements:**\n"
        for imp in improvements:
            message += f"• {imp}\n"
        
        if confidence_change > 0:
            message += f"\n🚀 **Confidence Increased:** +{confidence_change:.1%}"
        else:
            message += f"\n📉 **Confidence Adjusted:** {confidence_change:.1%}"
        
        message += f"\n\n⏰ **Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return message
    
    def get_learning_summary(self) -> str:
        """Get a summary of model learning progress"""
        total = self.learning_data["total_feedback"]
        if total == 0:
            return "🤖 **Adaptive Learning Status:** No feedback received yet. Start using the system to help the AI learn!"
        
        positive_ratio = self.learning_data["positive_feedback"] / total
        confidence = self.learning_data["model_confidence"]
        
        summary = f"🤖 **Adaptive Learning Summary**\n\n"
        summary += f"📊 **Total Interactions:** {total}\n"
        summary += f"✅ **Success Rate:** {positive_ratio:.1%}\n"
        summary += f"🎯 **Model Confidence:** {confidence:.1%}\n"
        summary += f"📈 **Learning Improvements:** {len(self.learning_data['learning_improvements'])}\n"
        
        if confidence > 0.8:
            summary += "\n🌟 **Status:** AI is performing excellently!"
        elif confidence > 0.7:
            summary += "\n👍 **Status:** AI is learning well!"
        else:
            summary += "\n📚 **Status:** AI is still learning..."
        
        return summary

# Global instance for easy access
adaptive_learning_model = AdaptiveLearningModel()

def process_user_feedback_for_learning(feedback_data: Dict) -> str:
    """Process user feedback and return learning message"""
    return adaptive_learning_model.process_user_feedback(feedback_data)

def get_model_learning_summary() -> str:
    """Get model learning summary"""
    return adaptive_learning_model.get_learning_summary()
