"""Answer checker that normalizes Chinese numerals and English words to Arabic digits."""

import random
import re

from src.stage_validator import MathProblem, StageValidator

# Chinese numeral to Arabic digit mapping
_CN_DIGITS = {
    "零": "0", "一": "1", "二": "2", "两": "2", "三": "3",
    "四": "4", "五": "5", "六": "6", "七": "7", "八": "8",
    "九": "9", "十": "10",
}

# English number words to Arabic digit mapping
_EN_WORDS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
}

# Chinese compound patterns: "一位"→1, "两位数"→2, "三位数"→3, etc.
_CN_COMPOUND = re.compile(r"[零一二三四五六七八九十两]+(?=位|位数|个)")


def _normalize(text: str) -> str:
    """Convert Chinese/English number representations to Arabic digits."""
    text = text.strip().lower()

    # Try direct Arabic digit match first
    m = re.search(r"-?\d+", text)
    if m:
        return m.group(0)

    # Try Chinese compound patterns like "一位" → 1
    m = _CN_COMPOUND.search(text)
    if m:
        ch = m.group(0)
        # Handle multi-character like "十二" → needs special handling
        # For simplicity, take the first character
        for ch_char in ch:
            if ch_char in _CN_DIGITS:
                return _CN_DIGITS[ch_char]
        return "1"

    # Try single Chinese character
    for ch, digit in _CN_DIGITS.items():
        if ch in text:
            return digit

    # Try English word
    for word, digit in _EN_WORDS.items():
        if word in text:
            return digit

    return text


class DigitCountingValidator(StageValidator):
    """Normalizes Chinese numerals and English words before comparing answers."""

    def generate_problem(self, difficulty: int | None, stage, rng: random.Random) -> MathProblem:
        """Generate a digit counting question."""
        _ = stage
        digits = max(1, difficulty or 1)
        if digits == 1:
            n = rng.randint(0, 9)
        else:
            low = 10 ** (digits - 1)
            high = (10**digits) - 1
            n = rng.randint(low, high)
        return MathProblem(
            question=f"数字 {n} 一共有几位？",
            expected_answer=str(len(str(n))),
        )

    def check_answer(self, question: str, answer: str, expected: str) -> bool:
        return _normalize(answer) == _normalize(expected)
