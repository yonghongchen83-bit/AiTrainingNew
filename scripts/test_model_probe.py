"""Quick probe test: send digit counting questions to Qwen and show raw output."""
import json
import re
import sys
sys.path.insert(0, __import__("pathlib").Path(__file__).resolve().parent.parent)

def extract_json_block(text: str) -> dict | None:
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return None
    try:
        payload = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None

from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "Qwen/Qwen2.5-0.5B-Instruct"
print(f"Loading {model_name}...", flush=True)
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto", torch_dtype="auto")
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
print(f"Loaded on {model.device}\n", flush=True)

questions = [
    # Digit counting (Chinese — as asked by the training framework)
    "数字 4 一共有几位？",       # 1 digit
    "数字 42 一共有几位？",      # 2 digits
    "数字 473 一共有几位？",     # 3 digits
    "数字 9473 一共有几位？",    # 4 digits
    "数字 39473 一共有几位？",   # 5 digits
    # Place value (Chinese)
    "数字 473 的百位是几？",
    # Simple English
    "What is 2+2?",
    "How many digits in the number 9473?",
]

for q in questions:
    messages = [
        {"role": "system", "content": "Return JSON only with keys: answer (string), confidence (number 0 to 1)."},
        {"role": "user", "content": f"Question: {q}"},
    ]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs, max_new_tokens=64, temperature=0.0, do_sample=False,
        pad_token_id=tokenizer.pad_token_id,
    )
    content = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
    parsed = extract_json_block(content)
    print(f"Q: {q}")
    print(f"  Raw: {content}")
    if parsed:
        print(f"  >> answer={parsed.get('answer')!r}  confidence={parsed.get('confidence')!r}")
    else:
        print(f"  >> (not valid JSON)")
    print()
