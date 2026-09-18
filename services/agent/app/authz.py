from fastapi import Header, HTTPException
from .auth import verify_token
from .security import Principal, allowed

async def principal_from_header(authorization: str|None=Header(default=None)):
    if not authorization:
        return Principal()
    if not authorization.lower().startswith('bearer '): raise HTTPException(401,'invalid authorization')
    try: return verify_token(authorization.split(' ',1)[1])
    except Exception as e: raise HTTPException(401,f'invalid token: {e}')

def require(principal, permission):
    if not allowed(principal,permission): raise HTTPException(403,'permission denied')
    return principal
