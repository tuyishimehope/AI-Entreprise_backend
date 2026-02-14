import os
from openai import OpenAI
from typing import Optional

from app.services.rag import RAGService


class OpenAIService:
    def __init__(self, api_key: Optional[str], model: str = "gpt-4o"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API Key is missing.")

        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.embedding_model = "text-embedding-3-small"

    def get_embeddings(self, text_chunks: list[str]):
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text_chunks
        )
        return [item.embedding for item in response.data]

    async def ask_question_about_document(self, db, session_id, sources, context_text, user_question):
        system_prompt = """
        You are a helpful assistant. Use ONLY the provided context to answer the question. 
        If the answer is not in the context, say you don't know. 
        Context:
        {context}
        """.format(context=context_text)

        full_answer = ""
        user_prompt = f"Question: {user_question}"
        stream = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,
            stream=True
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                full_answer += content
                yield content
