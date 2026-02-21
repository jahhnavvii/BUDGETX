import torch
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model

# -----------------------------
# CONFIG
# -----------------------------
model_name = "google/gemma-2b"
output_dir = "./budgetx_gemma_adapter"

# -----------------------------
# LOAD TOKENIZER
# -----------------------------
tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token

# -----------------------------
# LOAD MODEL (FP16 + GPU)
# -----------------------------
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    dtype=torch.float16,
    device_map="auto"
)

# Enable gradient checkpointing (saves VRAM)
model.gradient_checkpointing_enable()
model.config.use_cache = False

# -----------------------------
# APPLY LORA
# -----------------------------
lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# -----------------------------
# LOAD DATASET
# -----------------------------
dataset = load_dataset("json", data_files="finance_dataset.jsonl")

# -----------------------------
# FORMAT + TOKENIZE
# -----------------------------
def format_prompt(example):
    prompt = f"""Financial Summary:
{example['input']}

Professional Financial Advice:
{example['output']}"""

    tokenized = tokenizer(
        prompt,
        truncation=True,
        padding="max_length",
        max_length=256
    )

    # IMPORTANT FOR TRAINING
    tokenized["labels"] = tokenized["input_ids"].copy()

    return tokenized


tokenized_dataset = dataset.map(format_prompt, remove_columns=dataset["train"].column_names)

# -----------------------------
# DATA COLLATOR
# -----------------------------
data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False
)

# -----------------------------
# TRAINING ARGUMENTS
# -----------------------------
training_args = TrainingArguments(
    output_dir=output_dir,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    num_train_epochs=3,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=5,
    save_strategy="epoch",
    optim="adamw_torch",
    report_to="none"
)

# -----------------------------
# TRAINER
# -----------------------------
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset["train"],
    data_collator=data_collator
)

# -----------------------------
# START TRAINING
# -----------------------------
trainer.train()

# -----------------------------
# SAVE ADAPTER
# -----------------------------
model.save_pretrained(output_dir)

print("\n✅ Training Complete. Adapter saved.") #budgetx_gemma_adapter is the name of the folder where the trained model will be saved. You can change it to any name you prefer.