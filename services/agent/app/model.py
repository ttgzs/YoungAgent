import httpx
from .config import settings

class ModelGateway:
    """OpenAI-compatible chat gateway with normalized tool-call responses."""
    def __init__(self):
        self.last_usage = None

    async def chat(self, messages, tools=None):
        if not settings.api_key or not settings.model_name:
            return {'content': '未配置模型 API。', 'tool_calls': [], 'message': {'role': 'assistant', 'content': '未配置模型 API。'}}
        payload = {'model': settings.model_name, 'messages': messages, 'temperature': 0.2}
        if tools:
            payload['tools'] = tools
            payload['tool_choice'] = 'auto'
        headers = {'Authorization': f'Bearer {settings.api_key}', 'Content-Type': 'application/json'}
        async with httpx.AsyncClient(timeout=120) as c:
            r = await c.post(settings.base_url.rstrip('/') + '/chat/completions', json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
        self.last_usage = data.get('usage')
        msg = data['choices'][0]['message']
        return {
            'content': msg.get('content') or '',
            'tool_calls': msg.get('tool_calls') or [],
            'message': msg,
            'usage': data.get('usage'),
            'finish_reason': data['choices'][0].get('finish_reason')
        }
