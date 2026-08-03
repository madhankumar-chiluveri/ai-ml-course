import sys
import tiktoken
from transformers import AutoTokenizer

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

texts = {
    "English": "Madhusudhan Reddy",
    "Telugu": "మధుసూదన్ రెడ్డి",
    "PL/SQL": "CREATE OR REPLACE PROCEDURE update_invoice(p_id IN NUMBER, p_status IN VARCHAR2) IS BEGIN UPDATE invoices SET status = p_status WHERE id = p_id; COMMIT; END;"
}

print("=" * 85)
print(" 0.1 LOCAL TOKENIZATION COMPARISON (NO API KEY NEEDED)")
print("=" * 85)

# A. OpenAI Tiktoken (GPT-4o vs GPT-4)
enc_gpt4o = tiktoken.get_encoding("o200k_base")
enc_gpt4  = tiktoken.get_encoding("cl100k_base")

# B. Open Source Model Tokenizer (Qwen 2.5 - non-gated open weights tokenizer)
print("[Downloading / Loading Qwen 2.5 tokenizer from Hugging Face...]")
tok_qwen25 = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B")

print(f"\n{'Script':<10} | {'Chars':<6} | {'GPT-4o':<8} | {'GPT-4':<8} | {'Qwen-2.5':<8} | {'GPT-4o Chars/Token'}")
print("-" * 85)

for label, text in texts.items():
    chars = len(text)
    t_gpt4o = len(enc_gpt4o.encode(text))
    t_gpt4  = len(enc_gpt4.encode(text))
    t_qwen  = len(tok_qwen25.encode(text))
    ratio_gpt4o = chars / t_gpt4o if t_gpt4o > 0 else 0
    
    print(f"{label:<10} | {chars:<6} | {t_gpt4o:<8} | {t_gpt4:<8} | {t_qwen:<8} | {ratio_gpt4o:.2f}")

print("\n" + "=" * 85)
print(" DETAILED TOKEN BREAKDOWN (Telugu across Tokenizers)")
print("=" * 85)

telugu_text = texts["Telugu"]
print(f"\nOriginal Telugu Text: {telugu_text} ({len(telugu_text)} characters)")
print(f"GPT-4o Tokens  ({len(enc_gpt4o.encode(telugu_text))}): {[enc_gpt4o.decode_bytes([t]).decode('utf-8', errors='replace') for t in enc_gpt4o.encode(telugu_text)]}")
print(f"GPT-4 Tokens   ({len(enc_gpt4.encode(telugu_text))}):  {[enc_gpt4.decode_bytes([t]).decode('utf-8', errors='replace') for t in enc_gpt4.encode(telugu_text)]}")
print(f"Qwen-2.5 Tokens({len(tok_qwen25.encode(telugu_text))}): {tok_qwen25.tokenize(telugu_text)}")

print("\n" + "=" * 85)
print(" DETAILED TOKEN BREAKDOWN (PL/SQL in GPT-4o)")
print("=" * 85)
plsql_text = texts["PL/SQL"]
token_ids = enc_gpt4o.encode(plsql_text)
token_strings = [enc_gpt4o.decode_bytes([t]).decode('utf-8', errors='replace') for t in token_ids]
print(f"PL/SQL Tokens ({len(token_ids)} tokens for {len(plsql_text)} characters):")
print(token_strings)
