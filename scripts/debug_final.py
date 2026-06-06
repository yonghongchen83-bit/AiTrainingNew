"""Final debug: compare predict() vs manual generate() with full token dump."""
import re, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.llm_provider import RealLocalProvider
from src.models import Mode, StageConfig

provider = RealLocalProvider("Qwen/Qwen2.5-0.5B-Instruct")
stage = StageConfig(1, "DigitCounting", False, None, False, False)
mode = Mode.EXPERT

# Load the model
provider._ensure_loaded()

# 1. Manual generate first (before any predict call)
print("=== 1. Manual generate (fresh model) ===")
messages = [
    {"role": "system", "content": "You are a careful math assistant. Return JSON only with keys: answer (string), confidence (number 0 to 1)."},
    {"role": "user", "content": "Question: 数字 2 一共有几位？"},
]
text = provider._tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = provider._tokenizer(text, return_tensors="pt").to(provider._model.device)
print(f"  text: {text!r}")
print(f"  input_ids: {inputs['input_ids'][0].tolist()}")
outputs = provider._model.generate(**inputs, max_new_tokens=64, do_sample=False)
generated = outputs[0][inputs["input_ids"].shape[1]:]
content = provider._tokenizer.decode(generated, skip_special_tokens=True).strip()
print(f"  generated ids: {generated.tolist()}")
print(f"  content: {content!r}")

print()

# 2. Now call predict()
print("=== 2. predict() call ===")
out = provider.predict(
    question="数字 2 一共有几位？",
    expected_answer="2",
    budget=100.0,
    mode=mode,
    stage=stage,
)
print(f"  answer={out.answer!r} conf={out.confidence}")

print()

# 3. Manual generate again
print("=== 3. Manual generate (after predict) ===")
outputs2 = provider._model.generate(**inputs, max_new_tokens=64, do_sample=False)
generated2 = outputs2[0][inputs["input_ids"].shape[1]:]
content2 = provider._tokenizer.decode(generated2, skip_special_tokens=True).strip()
print(f"  generated ids: {generated2.tolist()}")
print(f"  content: {content2!r}")
