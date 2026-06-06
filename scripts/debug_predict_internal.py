"""Monkey-patch RealLocalProvider.predict to dump all internal state."""
import re, json, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import src.llm_provider as lp
from src.models import Mode, StageConfig, LLMOutput

original_predict = lp.RealLocalProvider.predict

def debug_predict(self, question, expected_answer, budget, mode, stage):
    try:
        self._ensure_loaded()
        system_prompt = (
            "You are a careful math assistant. "
            "Return JSON only with keys: answer (string), confidence (number 0 to 1)."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Question: {question}"},
        ]
        text = self._tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self._tokenizer(text, return_tensors="pt").to(self._model.device)
        
        print(f"  [DEBUG] input_ids shape: {inputs['input_ids'].shape}")
        print(f"  [DEBUG] input device: {inputs['input_ids'].device}")
        print(f"  [DEBUG] model device: {self._model.device}")
        print(f"  [DEBUG] model dtype: {self._model.dtype}")
        
        outputs = self._model.generate(
            **inputs,
            max_new_tokens=64,
            temperature=0.0,
            do_sample=False,
            pad_token_id=self._tokenizer.pad_token_id,
        )
        print(f"  [DEBUG] output shape: {outputs.shape}")
        
        generated = outputs[0][inputs["input_ids"].shape[1]:]
        content = self._tokenizer.decode(generated, skip_special_tokens=True).strip()
        print(f"  [DEBUG] raw content: {repr(content)}")
        print(f"  [DEBUG] content type: {type(content)}")
        print(f"  [DEBUG] content len: {len(content)}")
        print(f"  [DEBUG] content bytes: {content.encode('utf-8')}")
        
        match = re.search(r"\{.*\}", content, flags=re.DOTALL)
        print(f"  [DEBUG] regex match: {match is not None}")
        if match:
            print(f"  [DEBUG] matched: {repr(match.group(0))}")
            try:
                payload = json.loads(match.group(0))
                print(f"  [DEBUG] parsed: {payload}")
                ans = str(payload.get("answer", "0")).strip()
                conf = float(payload.get("confidence", 0.35))
                print(f"  [DEBUG] would return: answer={ans!r} conf={conf}")
            except Exception as e:
                print(f"  [DEBUG] parse error: {e}")
        
        parsed = self._extract_json_block(content)
        print(f"  [DEBUG] _extract_json_block result: {parsed}")
        if parsed is None:
            fb = self._extract_answer_fallback(content)
            print(f"  [DEBUG] fallback answer: {fb!r}")
        
    except Exception as e:
        print(f"  [DEBUG] EXCEPTION in predict: {e}")
        traceback.print_exc()

    return original_predict(self, question, expected_answer, budget, mode, stage)

lp.RealLocalProvider.predict = debug_predict

provider = lp.RealLocalProvider("Qwen/Qwen2.5-0.5B-Instruct")
stage = StageConfig(1, "DigitCounting", False, None, False, False)
mode = Mode.EXPERT
out = provider.predict(
    question="数字 2 一共有几位？",
    expected_answer="2",
    budget=100.0,
    mode=mode,
    stage=stage,
)
print(f"\nFinal: answer={out.answer!r} conf={out.confidence}")
