import json
import random
from . import Plugin


class RecipesPlugin(Plugin):
    def __init__(self):
        super().__init__("recipes", "Recipe suggestions and cooking tips", "1.0.0")
        self.commands = ["recipe", "cooking", "kya khayein", "banao", "recipe batao"]
        self.keywords = ["recipe", "cooking", "khana", "banana", "food", "dish", "meal"]

        self.recipes = {
            "indian": [
                {
                    "name": "Dal Makhani",
                    "time": "45 min",
                    "difficulty": "Medium",
                    "ingredients": ["urad dal", "rajma", "butter", "cream", "tomato", "spices"],
                    "steps": ["Soak dal overnight", "Cook till soft", "Add butter and cream", "Simmer 20 min"],
                },
                {
                    "name": "Paneer Butter Masala",
                    "time": "30 min",
                    "difficulty": "Easy",
                    "ingredients": ["paneer", "butter", "tomato", "cream", "cashew", "spices"],
                    "steps": ["Make tomato gravy", "Add cashew paste", "Add paneer cubes", "Finish with cream"],
                },
                {
                    "name": "Chicken Biryani",
                    "time": "60 min",
                    "difficulty": "Hard",
                    "ingredients": ["chicken", "rice", "yogurt", "onion", "spices", "saffron"],
                    "steps": ["Marinate chicken", "Cook rice partially", "Layer and dum cook", "Rest 10 min"],
                },
                {
                    "name": "Aloo Paratha",
                    "time": "25 min",
                    "difficulty": "Easy",
                    "ingredients": ["potato", "wheat flour", "onion", "spices", "butter"],
                    "steps": ["Boil and mash potatoes", "Make dough", "Stuff and roll", "Cook on tawa"],
                },
            ],
            "snacks": [
                {"name": "Samosa", "time": "40 min", "difficulty": "Medium"},
                {"name": "Pani Puri", "time": "30 min", "difficulty": "Medium"},
                {"name": "Vada Pav", "time": "20 min", "difficulty": "Easy"},
                {"name": "Momos", "time": "45 min", "difficulty": "Medium"},
            ],
            "quick": [
                {"name": "Maggi", "time": "5 min", "difficulty": "Easy"},
                {"name": "Sandwich", "time": "10 min", "difficulty": "Easy"},
                {"name": "Omelette", "time": "10 min", "difficulty": "Easy"},
                {"name": "Fruit Salad", "time": "5 min", "difficulty": "Easy"},
            ],
        }

    def can_handle(self, intent: str, message: str) -> bool:
        recipe_keywords = [
            "recipe", "cook", "banana", "khana", "kya khayein",
            "dish", "meal", "breakfast", "lunch", "dinner",
            "snack", "tiffin", "nashta",
        ]
        msg_lower = message.lower()
        return any(kw in msg_lower for kw in recipe_keywords)

    def execute(self, user_id: str, message: str, context: dict) -> dict:
        msg_lower = message.lower()

        if any(word in msg_lower for word in ["quick", "jaldi", "5 min", "fast"]):
            return self._get_random_recipe("quick")
        elif any(word in msg_lower for word in ["snack", "nashta", "chota"]):
            return self._get_random_recipe("snacks")
        elif any(word in msg_lower for word in ["breakfast", "nashta"]):
            return self._get_breakfast_recipe()
        elif any(word in msg_lower for word in ["lunch", "dophar"]):
            return self._get_lunch_recipe()
        elif any(word in msg_lower for word in ["dinner", "raat"]):
            return self._get_dinner_recipe()
        else:
            return self._get_random_recipe("indian")

    def _get_random_recipe(self, category: str) -> dict:
        recipes = self.recipes.get(category, self.recipes["indian"])
        recipe = random.choice(recipes)

        response = f"🍳 {recipe['name']}\n\n"
        response += f"Time: {recipe.get('time', '30 min')}\n"
        response += f"Difficulty: {recipe.get('difficulty', 'Medium')}\n\n"

        if "ingredients" in recipe:
            response += "Ingredients:\n"
            for ing in recipe["ingredients"]:
                response += f"• {ing}\n"
            response += "\nSteps:\n"
            for i, step in enumerate(recipe["steps"], 1):
                response += f"{i}. {step}\n"

        return {
            "response": response,
            "command": {"type": "recipe", "name": recipe["name"]},
            "intent": "recipes",
        }

    def _get_breakfast_recipe(self) -> dict:
        breakfast = [
            "Poha - 15 min, Easy",
            "Upma - 20 min, Easy",
            "Idli Sambar - 30 min, Medium",
            "Paratha with Curd - 20 min, Easy",
            "Toast and Eggs - 10 min, Easy",
        ]
        chosen = random.choice(breakfast)
        return {
            "response": f"🌅 Breakfast Ideas:\n\n"
                       f"Today's Suggestion: {chosen}\n\n"
                       f"Healthy start to the day!",
            "command": {"type": "recipe_breakfast"},
            "intent": "recipes",
        }

    def _get_lunch_recipe(self) -> dict:
        lunch = [
            "Rajma Chawal - 40 min",
            "Jeera Rice with Dal - 30 min",
            "Chicken Curry with Roti - 45 min",
            "Vegetable Biryani - 40 min",
        ]
        chosen = random.choice(lunch)
        return {
            "response": f"🌞 Lunch Ideas:\n\n"
                       f"Today's Suggestion: {chosen}\n\n"
                       f"Enjoy your meal!",
            "command": {"type": "recipe_lunch"},
            "intent": "recipes",
        }

    def _get_dinner_recipe(self) -> dict:
        dinner = [
            "Dal Fry with Rice - 30 min",
            "Paneer Tikka - 35 min",
            "Chicken Grilled - 40 min",
            "Vegetable Soup - 25 min",
        ]
        chosen = random.choice(dinner)
        return {
            "response": f"🌙 Dinner Ideas:\n\n"
                       f"Today's Suggestion: {chosen}\n\n"
                       f"Light and healthy!",
            "command": {"type": "recipe_dinner"},
            "intent": "recipes",
        }
