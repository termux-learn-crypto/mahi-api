import re
import math


def calculate(expression: str) -> dict | None:
    try:
        expr = expression.lower().strip()
        expr = expr.replace("x", "*").replace("X", "*")
        expr = expr.replace("÷", "/").replace("into", "*").replace("plus", "+")
        expr = expr.replace("minus", "-").replace("times", "*").replace("divided by", "/")
        expr = expr.replace("power", "**").replace("raised to", "**")
        expr = re.sub(r'[^0-9+\-*/().%^ ]', '', expr)

        if not expr or not any(c.isdigit() for c in expr):
            return None

        allowed_chars = set("0123456789+-*/.()%^ ")
        if not all(c in allowed_chars for c in expr):
            return None

        result = eval(expr, {"__builtins__": {}}, {"math": math})

        if isinstance(result, float) and result == int(result) and abs(result) < 1e15:
            result = int(result)

        return {"result": result, "expression": expression}
    except:
        return None


def solve_math(word: str) -> str:
    word = word.lower().strip()

    if "square root" in word or "vroot" in word or "√" in word:
        nums = re.findall(r'[\d.]+', word)
        if nums:
            try:
                n = float(nums[0])
                if n < 0:
                    return "Negative number ka square root nahi ho sakta! 😅"
                result = math.sqrt(n)
                return f"√{int(n)} = {result}"
            except:
                return "Number samajh nahi aaya! 😅"

    if "square" in word and "root" not in word:
        nums = re.findall(r'[\d.]+', word)
        if nums:
            n = float(nums[0])
            return f"{int(n)}² = {int(n**2)}"

    if "cube" in word and "root" not in word:
        nums = re.findall(r'[\d.]+', word)
        if nums:
            n = float(nums[0])
            return f"{int(n)}³ = {int(n**3)}"

    if "ka" in word and "percent" in word:
        nums = re.findall(r'[\d.]+', word)
        if len(nums) >= 2:
            try:
                total = float(nums[0])
                percent = float(nums[1])
                result = (percent / 100) * total
                return f"{int(percent)}% of {int(total)} = {int(result)}"
            except:
                return "Calculation mein dikkat aa gayi! 😅"

    if "%" in word or "percent" in word:
        nums = re.findall(r'[\d.]+', word)
        if len(nums) >= 2:
            try:
                part = float(nums[0])
                total = float(nums[1])
                result = (part / total) * 100
                return f"{int(part)} is {int(result)}% of {int(total)}"
            except:
                return "Calculation mein dikkat aa gayi! 😅"

    if "of" in word and any(c.isdigit() for c in word):
        match = re.search(r'([\d.]+)\s*(?:%)?\s*of\s*([\d.]+)', word)
        if match:
            percentage = float(match.group(1))
            number = float(match.group(2))
            result = (percentage / 100) * number
            return f"{percentage}% of {int(number)} = {result}"

    return None
