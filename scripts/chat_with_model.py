"""
Interactive chat with Qwen2.5-0.5B-Instruct (or any HuggingFace model).
Useful for probing the model's raw capabilities outside the training framework.

Usage:
    python scripts/chat_with_model.py
    python scripts/chat_with_model.py --model Qwen/Qwen2.5-0.5B-Instruct
    python scripts/chat_with_model.py --model Qwen/Qwen2.5-0.5B-Instruct --json-mode
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Add repo root to path so we can reuse RealLocalProvider
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def extract_json_block(text: str) -> dict | None:
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return None
    try:
        payload = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def main():
    parser = argparse.ArgumentParser(description="Chat with a local HuggingFace model")
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct",
                        help="HuggingFace model ID (default: Qwen/Qwen2.5-0.5B-Instruct)")
    parser.add_argument("--json-mode", action="store_true",
                        help="Request JSON output (like the training framework does)")
    parser.add_argument("--max-tokens", type=int, default=128,
                        help="Max new tokens per response (default: 128)")
    parser.add_argument("--system-prompt", default=None,
                        help="Override the system prompt")
    args = parser.parse_args()

    # Lazy imports so script starts fast
    from transformers import AutoModelForCausalLM, AutoTokenizer

    print(f"Loading {args.model} ...", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        device_map="auto",
        torch_dtype="auto",
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    print(f"Model loaded on {model.device}\n")

    system_prompt = args.system_prompt or (
        "You are a careful math assistant. "
        "Return JSON only with keys: answer (string), confidence (number 0 to 1)."
        if args.json_mode else
        "You are a helpful assistant. Answer concisely."
    )

    history: list[dict] = [{"role": "system", "content": system_prompt}]

    print("─── Interactive Chat ───")
    print("Type 'quit' to exit, 'clear' to reset history, 'show prompt' to see current prompt.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue
        if user_input.lower() == "quit":
            break
        if user_input.lower() == "clear":
            history = [{"role": "system", "content": system_prompt}]
            print("[History cleared]\n")
            continue
        if user_input.lower() == "show prompt":
            print(f"System prompt: {system_prompt}\n")
            continue

        history.append({"role": "user", "content": user_input})

        text = tokenizer.apply_chat_template(
            history, tokenize=False, add_generation_prompt=True
        )
        inputs = tokenizer(text, return_tensors="pt").to(model.device)
        outputs = model.generate(
            **inputs,
            max_new_tokens=args.max_tokens,
            temperature=0.0,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
        )
        generated = outputs[0][inputs["input_ids"].shape[1]:]
        content = tokenizer.decode(generated, skip_special_tokens=True).strip()

        print(f"Model: {content}")

        if args.json_mode:
            parsed = extract_json_block(content)
            if parsed:
                print(f"  → Parsed: answer={parsed.get('answer')!r}, "
                      f"confidence={parsed.get('confidence')!r}")
            else:
                print(f"  → (not valid JSON)")

        history.append({"role": "assistant", "content": content})
        print()


if __name__ == "__main__":
    main()
