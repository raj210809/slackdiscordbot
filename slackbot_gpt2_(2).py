from langchain_huggingface import HuggingFacePipeline
from transformers import GPT2Tokenizer, GPT2LMHeadModel, pipeline

model_name = "gpt2-medium"
model = GPT2LMHeadModel.from_pretrained(model_name)
tokenizer = GPT2Tokenizer.from_pretrained(model_name)
pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=200)
hf = HuggingFacePipeline(pipeline=pipe)


def generate_response(user_text):
    try:
        return hf.invoke(f"Q: {user_text}")

    except Exception as e:
        print(f"Error generating response: {e}")
        return "Sorry, I couldn't generate any response."


# sample test
print(hf.invoke("What is geological capital of India?"))
