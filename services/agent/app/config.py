import os
from dataclasses import dataclass
@dataclass(frozen=True)
class Settings:
    model_provider:str=os.getenv('MODEL_PROVIDER','openai'); model_name:str=os.getenv('MODEL_NAME',''); model_fallbacks:str=os.getenv('MODEL_FALLBACKS',''); model_timeout_seconds:int=int(os.getenv('MODEL_TIMEOUT_SECONDS','120')); model_retry_delay_seconds:float=float(os.getenv('MODEL_RETRY_DELAY_SECONDS','0.5')); api_key:str=os.getenv('OPENAI_API_KEY',''); base_url:str=os.getenv('OPENAI_BASE_URL','https://api.openai.com/v1')
    database_url:str=os.getenv('DATABASE_URL','sqlite+aiosqlite:///./agent.db'); redis_url:str=os.getenv('REDIS_URL','redis://localhost:6379/0')
    max_steps:int=int(os.getenv('AGENT_MAX_STEPS','8')); tool_timeout_seconds:int=int(os.getenv('TOOL_TIMEOUT_SECONDS','30')); worker_queue:str=os.getenv('AGENT_QUEUE','youngagent:tasks')
    mcp_gateway_url:str=os.getenv('MCP_GATEWAY_URL','http://mcp-gateway:8100'); browser_service_url:str=os.getenv('BROWSER_SERVICE_URL','http://browser:8090'); computer_use_url:str=os.getenv('COMPUTER_USE_URL','http://computer-use:8091')
    jwt_secret:str=os.getenv('JWT_SECRET','change-me-in-production'); oidc_issuer:str=os.getenv('OIDC_ISSUER',''); oidc_audience:str=os.getenv('OIDC_AUDIENCE',''); artifact_dir:str=os.getenv('ARTIFACT_DIR','/tmp/youngagent-artifacts'); embedding_model:str=os.getenv('EMBEDDING_MODEL',''); oidc_jwks_url:str=os.getenv('OIDC_JWKS_URL',''); access_token_ttl_seconds:int=int(os.getenv('ACCESS_TOKEN_TTL_SECONDS','3600'))
settings=Settings()
