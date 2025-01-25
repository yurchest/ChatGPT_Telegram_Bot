import pytest
from . import OpenAI_API

@pytest.mark.asyncio
async def test_get_response():
    openai_instance = OpenAI_API()
    conversation_log = [{'role': 'user', 'content': 'Hello!'}]
    response = await openai_instance._get_response(conversation_log)
    assert response.choices[0].message.role == "assistant"
