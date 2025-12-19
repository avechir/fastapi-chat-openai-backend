import os
from openai import OpenAI

MODEL_NAME = "gpt-5-nano"
PRICE_PER_1M_INPUT = 0.05  
PRICE_PER_1M_OUTPUT = 0.4

class ChatService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            print('there is a key')
        else:
            print('no key')
            self.client = OpenAI(api_key="sk-demo-mode-key")

    def get_response(self, history: list):
        if not self.api_key:
            return "no key. could be answer from AI", 10, 20

        try:
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=history
            )
            text = response.choices[0].message.content
            usage = response.usage
            return text, usage.prompt_tokens, usage.completion_tokens
        except Exception as e:
            raise e
        
    def calculate_cost(self, prompt_tokens: int, response_tokens: int) -> tuple[float, float]:
        input_cost = (prompt_tokens / 1_000_000) * PRICE_PER_1M_INPUT
        output_cost = (response_tokens / 1_000_000) * PRICE_PER_1M_OUTPUT
        return input_cost, output_cost

chat_service = ChatService()