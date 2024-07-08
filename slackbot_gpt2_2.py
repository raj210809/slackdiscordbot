from langchain_huggingface import HuggingFacePipeline
from transformers import GPT2Tokenizer, GPT2LMHeadModel, pipeline

model_name = "gpt2-medium"
model = GPT2LMHeadModel.from_pretrained(model_name)
tokenizer = GPT2Tokenizer.from_pretrained(model_name)
pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=200)
hf = HuggingFacePipeline(pipeline=pipe)


def generate_response(user_text):
    try:
        generated_text = hf.invoke(user_text)
        # Remove the question from the generated response
        response = generated_text.replace(user_text, "", 1).strip()
        return response
    except Exception as e:
        print(f"Error generating response: {e}")
        return "Sorry, I couldn't generate any response."


# Sample test
# print(generate_response("What is the geological capital of India?"))
