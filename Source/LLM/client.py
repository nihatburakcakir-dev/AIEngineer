import ollama


class LLMClient:

    def __init__(self):

        self.model = "qwen3:8b"


    def generate(
        self,
        prompt: str
    ):

        response = ollama.chat(

            model=self.model,

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]

        )

        return response["message"]["content"]
