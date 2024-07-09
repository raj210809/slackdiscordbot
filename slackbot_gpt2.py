from langchain_huggingface import HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

model_id = "gpt2-medium"
model = AutoModelForCausalLM.from_pretrained(model_id)
tokenizer = AutoTokenizer.from_pretrained(model_id)
pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=200)
hf = HuggingFacePipeline(pipeline=pipe)

async def generate_response(user_text):
    try:
        return hf.invoke(f"Q: {user_text[7:]}\nA: Let's think step by step.")
    except Exception as e:
        print(f"Error generating response: {e}")
        return "Sorry, I couldn't generate any response."
