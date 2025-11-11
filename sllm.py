# -*- coding: utf-8 -*-
"""
Full-dataset inference with a single LoRA checkpoint (checkpoint-16)
- Loads BASE_MODEL + LoRA at CKPT_PATH
- Runs on ALL rows of EVAL_PATH
- Saves one CSV with original cols + pred column
"""

import os, re, json, gc
from typing import List, Dict, Any
from tqdm.auto import tqdm

import torch
import pandas as pd
from peft import PeftModel
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

# ========= Paths =========
BASE_MODEL = "Qwen/Qwen2.5-14B-Instruct"
CKPT_PATH  = "./qwen2.5-14b-qlora-r1/r1/checkpoint-16"   # ← 여기를 checkpoint-16로 고정
EVAL_PATH  = "sllm_pairs_with_gold_filtered.jsonl"
OUT_DIR    = os.path.dirname(CKPT_PATH)
OUT_CSV    = os.path.join(OUT_DIR, "infer_checkpoint-16_full.csv")

# ========= Inference params =========
TOP_K_SIM      = 3
REQ_END        = "따라서 특허를 받을 수 없습니다."
MAX_INPUT_LEN  = 1792
GEN_KW = dict(
    max_new_tokens=256,
    do_sample=False,
    num_beams=3,
    no_repeat_ngram_size=3,
    length_penalty=0.9,
    repetition_penalty=1.1,
)

# ========= Template utils =========
def _clean(x: str) -> str:
    return re.sub(r"\s+", " ", str(x)).strip() if isinstance(x, str) else ""

def _sim_block_and_map(similar_claims: list, k:int=TOP_K_SIM):
    if not isinstance(similar_claims, list) or not similar_claims:
        return "(유사 청구항 없음)", []
    ranked = similar_claims[:k]
    rows, mapping = [], []
    for i, s in enumerate(ranked, 1):
        did = s.get("doc_id","")
        cno = s.get("claim_no","")
        txt = _clean(s.get("text",""))
        rows.append(f"{i}) [{did} / Claim {cno}]\n{txt}")
        mapping.append({"label": f"인용발명{i}", "doc_id": did})
    return ("\n\n".join(rows) if rows else "(유사 청구항 없음)"), mapping

SYSTEM_PROMPT = (
    "You are Qwen, a helpful patent analysis assistant.\n"
    "규칙:\n"
    "1) 반드시 한국어만 사용하고 중국어, 일본어 등 외국어(한자 포함)를 절대 사용하지 마십시오.\n"
    "2) 출력은 줄바꿈 없이 한 단락의 한국어 공식 문장으로만 작성하십시오.\n"
    "3) 본문에서 인용발명을 언급할 때는 반드시 '인용발명N(출원번호 XXXXX)' 형식으로 표기하십시오.\n"
)

def _mapping_lines(mapping):
    s = "\n".join([f"- {m['label']}: 출원번호 {m['doc_id']}" for m in mapping if m.get("doc_id")])
    return s if s else "- (유사문서 출원번호 없음)"

def build_messages_from_row(row: dict, k:int=TOP_K_SIM):
    claim = _clean(row.get("claim_text",""))
    sim_block, mapping = _sim_block_and_map(row.get("similar_claims", []), k=k)
    prior_art_no = row.get("prior_art_no") or row.get("prior_art_code") or row.get("prior")
    prior_line = f"{prior_art_no}" if isinstance(prior_art_no, str) else (str(prior_art_no) if prior_art_no is not None else "")
    user = (
        "다음 (선행문헌/유사문서의 청구항 목록과 대상 청구항)을 바탕으로, "
        "거절 사유(신규성, 진보성, 명확성 등)를 판별하고 핵심 근거를 3줄 이내로 간결히 설명해줘. "
        "유사점과 차이점을 명확히 지적해.\n\n"
        f"[선행문헌/인용 번호]\n{prior_line}\n\n"
        f"[대상 청구항]\n{claim}\n\n"
        f"[유사 문서의 청구항 목록 (상위 {k}개)]\n{sim_block}\n\n"
        "[인용발명 라벨-출원번호 매핑]\n"
        f"{_mapping_lines(mapping)}\n\n"
        "주의: 본문에서 인용발명을 언급할 때는 반드시 '인용발명N(출원번호 XXXXX)' 형식으로 표기하고, "
        "한국어만 사용하며 한 단락으로 작성하라."
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user},
    ]

# ========= Load model (4-bit + LoRA checkpoint) =========
bnb_cfg = BitsAndBytesConfig(
    load_in_4bit=True, bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True
)
tok = AutoTokenizer.from_pretrained(BASE_MODEL, use_fast=True)
if tok.pad_token_id is None:
    tok.pad_token = tok.eos_token

base = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    device_map="auto",
    torch_dtype=torch.bfloat16,
    low_cpu_mem_usage=True,
    quantization_config=bnb_cfg,
)
model = PeftModel.from_pretrained(base, CKPT_PATH)
model.eval()
print("✅ Loaded:", CKPT_PATH)

# ========= Load full data =========
rows = []
with open(EVAL_PATH, "r", encoding="utf-8") as f:
    for line in f:
        rows.append(json.loads(line))
print("Samples (full):", len(rows))

# ========= Generate =========
preds, prompt_lens = [], []
for row in tqdm(rows, desc="Generating (checkpoint-16, full)"):
    messages = build_messages_from_row(row, k=TOP_K_SIM)
    prompt = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    enc = tok([prompt], return_tensors="pt", truncation=True, max_length=MAX_INPUT_LEN)
    enc = {k: v.to(model.device) for k, v in enc.items()}

    with torch.inference_mode():
        out = model.generate(**enc, **GEN_KW, pad_token_id=tok.eos_token_id, eos_token_id=tok.eos_token_id)

    input_len = enc["input_ids"].shape[1]
    gen_ids = out[0][input_len:]
    gen_text = tok.decode(gen_ids, skip_special_tokens=True).strip()

    # post-process
    gen_text = re.sub(r"[\u4E00-\u9FFF]+", "", gen_text)
    gen_text = re.sub(r"\s*\n\s*", " ", gen_text).strip()
    if not gen_text.endswith(REQ_END):
        if not gen_text.endswith("."):
            gen_text += "."
        gen_text += f" {REQ_END}"

    preds.append(gen_text)
    prompt_lens.append(input_len)

# ========= Save =========
df_src = pd.DataFrame(rows)
df_src["pred_checkpoint16"] = preds
df_src["prompt_len_checkpoint16"] = prompt_lens
df_src.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

print(f"💾 Saved: {OUT_CSV}")