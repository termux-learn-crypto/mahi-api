import json
from datetime import datetime, timedelta
from . import Plugin


class FitnessPlugin(Plugin):
    def __init__(self):
        super().__init__("fitness", "Fitness tracking and health tips", "1.0.0")
        self.commands = ["track steps", "calories", "workout", "water intake", "fitness"]
        self.keywords = ["steps", "calories", "workout", "exercise", "water", "fitness", "gym", "run"]

    def can_handle(self, intent: str, message: str) -> bool:
        fitness_keywords = [
            "steps", "calories", "workout", "exercise", "water", "fitness",
            "gym", "run", "walking", "running", "yoga", "stretch",
            "heart rate", "sleep", "weight", "bmi",
        ]
        msg_lower = message.lower()
        return any(kw in msg_lower for kw in fitness_keywords)

    def execute(self, user_id: str, message: str, context: dict) -> dict:
        msg_lower = message.lower()

        if any(word in msg_lower for word in ["steps", "walk", "kadam"]):
            return self._track_steps(user_id, message)
        elif any(word in msg_lower for word in ["calories", "khaana", "diet"]):
            return self._track_calories(user_id, message)
        elif any(word in msg_lower for word in ["workout", "exercise", "gym"]):
            return self._track_workout(user_id, message)
        elif any(word in msg_lower for word in ["water", "paani", "drink"]):
            return self._track_water(user_id, message)
        elif any(word in msg_lower for word in ["sleep", "neend", "rest"]):
            return self._track_sleep(user_id, message)
        elif any(word in msg_lower for word in ["heart", "pulse", "bp"]):
            return self._track_heart_rate(user_id)
        elif any(word in msg_lower for word in ["summary", "report", "haal"]):
            return self._get_summary(user_id)
        else:
            return self._get_dashboard(user_id)

    def _track_steps(self, user_id: str, message: str) -> dict:
        import re
        steps_match = re.search(r'(\d+)\s*(?:steps|kadam)', message, re.IGNORECASE)
        steps = int(steps_match.group(1)) if steps_match else 5000

        goal = 10000
        progress = min(100, (steps / goal) * 100)

        return {
            "response": f"🚶 Steps Today: {steps:,}\n"
                       f"Goal: {goal:,}\n"
                       f"Progress: {progress:.0f}%\n\n"
                       f"{'Great job! Keep going!' if progress >= 50 else 'Keep walking!'}",
            "command": {"type": "fitness_steps", "steps": steps},
            "intent": "fitness",
        }

    def _track_calories(self, user_id: str, message: str) -> dict:
        import re
        cal_match = re.search(r'(\d+)\s*(?:cal|calories)', message, re.IGNORECASE)
        calories = int(cal_match.group(1)) if cal_match else 2000

        return {
            "response": f"🔥 Calories Today: {calories}\n"
                       f"Goal: 2000\n"
                       f"{'On track!' if calories <= 2000 else 'Watch your intake!'}\n\n"
                       f"Tip: Protein-rich foods help!",
            "command": {"type": "fitness_calories", "calories": calories},
            "intent": "fitness",
        }

    def _track_workout(self, user_id: str, message: str) -> dict:
        msg_lower = message.lower()

        workouts = {
            "running": {"duration": 30, "calories": 300, "emoji": "🏃"},
            "yoga": {"duration": 45, "calories": 150, "emoji": "🧘"},
            "gym": {"duration": 60, "calories": 400, "emoji": "💪"},
            "walking": {"duration": 30, "calories": 150, "emoji": "🚶"},
            "cycling": {"duration": 30, "calories": 250, "emoji": "🚴"},
            "swimming": {"duration": 30, "calories": 350, "emoji": "🏊"},
        }

        workout_type = "general"
        for w_type in workouts:
            if w_type in msg_lower:
                workout_type = w_type
                break

        workout = workouts.get(workout_type, {"duration": 30, "calories": 200, "emoji": "💪"})

        return {
            "response": f"{workout['emoji']} Workout Logged!\n\n"
                       f"Type: {workout_type.title()}\n"
                       f"Duration: {workout['duration']} min\n"
                       f"Calories Burned: ~{workout['calories']}\n\n"
                       f"Keep it up!",
            "command": {"type": "fitness_workout", "type": workout_type, "calories": workout["calories"]},
            "intent": "fitness",
        }

    def _track_water(self, user_id: str, message: str) -> dict:
        import re
        glass_match = re.search(r'(\d+)\s*(?:glass|glasses|cup)', message, re.IGNORECASE)
        glasses = int(glass_match.group(1)) if glass_match else 1

        total_today = 6
        goal = 8

        return {
            "response": f"💧 Water: +{glasses} glass(es)\n"
                       f"Today: {total_today}/{goal} glasses\n\n"
                       f"{'Good hydration!' if total_today >= goal else f'Need {goal - total_today} more glasses!'}",
            "command": {"type": "fitness_water", "glasses": glasses},
            "intent": "fitness",
        }

    def _track_sleep(self, user_id: str, message: str) -> dict:
        return {
            "response": "😴 Sleep Last Night:\n\n"
                       "Duration: 7h 30m\n"
                       "Quality: Good\n"
                       "Deep Sleep: 2h 15m\n"
                       "REM: 1h 45m\n\n"
                       "Tip: 7-9 hours is ideal!",
            "command": {"type": "fitness_sleep"},
            "intent": "fitness",
        }

    def _track_heart_rate(self, user_id: str) -> dict:
        return {
            "response": "❤️ Heart Rate:\n\n"
                       "Current: 72 bpm\n"
                       "Resting: 68 bpm\n"
                       "Max Today: 145 bpm\n\n"
                       "Status: Normal",
            "command": {"type": "fitness_heart"},
            "intent": "fitness",
        }

    def _get_summary(self, user_id: str) -> dict:
        return {
            "response": "📊 Today's Fitness Summary:\n\n"
                       "🚶 Steps: 7,500/10,000\n"
                       "🔥 Calories: 1,800/2,000\n"
                       "💧 Water: 6/8 glasses\n"
                       "💪 Workout: 30 min\n"
                       "😴 Sleep: 7h 30m\n\n"
                       "Overall: Good!",
            "command": {"type": "fitness_summary"},
            "intent": "fitness",
        }

    def _get_dashboard(self, user_id: str) -> dict:
        return {
            "response": "💪 Fitness Dashboard:\n\n"
                       "Track:\n"
                       "• Steps & Walking\n"
                       "• Calories & Diet\n"
                       "• Workouts\n"
                       "• Water Intake\n"
                       "• Sleep\n"
                       "• Heart Rate\n\n"
                       "Kya track karna hai?",
            "command": {"type": "fitness_dashboard"},
            "intent": "fitness",
        }
