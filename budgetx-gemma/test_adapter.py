import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

model_name = "google/gemma-2b"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    dtype=torch.float16,
    device_map="auto"
)

model = PeftModel.from_pretrained(model, "./budgetx_gemma_adapter")

prompt = """Financial Summary:
Income: 70000, Expense: 68000, Savings Rate: 0.02

Professional Financial Advice:
"""

inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

output = model.generate(
    **inputs,
    max_new_tokens=100
)

print(tokenizer.decode(output[0], skip_special_tokens=True))