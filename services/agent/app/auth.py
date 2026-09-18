import jwt
from datetime import datetime, timedelta, timezone
from .config import settings
from .security import Principal

def issue_token(user_id,tenant_id,roles):
    now=datetime.now(timezone.utc); return jwt.encode({'sub':user_id,'tenant_id':tenant_id,'roles':roles,'iat':now,'exp':now+timedelta(seconds=settings.access_token_ttl_seconds)},settings.jwt_secret,algorithm='HS256')

def verify_token(token):
    p=jwt.decode(token,settings.jwt_secret,algorithms=['HS256'],audience=settings.oidc_audience or None, options={'verify_aud':bool(settings.oidc_audience)})
    return Principal(str(p.get('sub','anonymous')),str(p.get('tenant_id','default')),tuple(p.get('roles',['user'])))
