"""Test if generation order affects output."""
import re, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.llm_provider import RealLocalProvider
from src.models import Mode, StageConfig

provider = RealLocalProvider("Qwen/Qwen2.5-0.5B-Instruct")
stage = StageConfig(1, "DigitCounting", False, None, False, False)
mode = Mode.EXPERT

# Call predict FIRST
print("=== First call: provider.predict() ===")
out1 = provider.predict(
    question="数字 2 一共有几位？",
    expected_answer="2",
    budget=100.0,
    mode=mode,
    stage=stage,
)
print(f"  answer={out1.answer!r} conf={out1.confidence}")

# Then do manual generation
print("\n=== Second call: manual generate ===")
provider._ensure_loaded()
question = "数字 2 一共有几位？"
messages = [
    {"role": "system", "content": "Return JSON only with keys: answer (string), confidence (number 0 to 1)."},
    {"role": "user", "content": f"Question: {question}"},
]
text = provider._tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = provider._tokenizer(text, return_tensors="pt").to(provider._model.device)
outputs = provider._model.generate(
    **inputs,
    max_new_tokens=64,
    temperature=0.0,
    do_sample=False,
    pad_token_id=provider._tokenizer.pad_token_id,
)
generated = outputs[0][inputs["input_ids"].shape[1]:]
content = provider._tokenizer.decode(generated, skip_special_tokens=True).strip()
print(f"  Raw: {repr(content)}")
match = re.search(r"\{.*\}", content, flags=re.DOTALL)
if match:
    payload = json.loads(match.group(0))
    print(f"  Parsed: answer={payload.get('answer')!r} conf={payload.get('confidence')}")
else:
    print("  (no JSON block)")

# Try predict again
print("\n=== Third call: provider.predict() again ===")
out3 = provider.predict(
    question="数字 2 一共有几位？",
    expected_answer="2",
    budget=100.0,
    mode=mode,
    stage=stage,
)
print(f"  answer={out3.answer!r} conf={out3.confidence}")
