from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import base64, io
from PIL import Image
app=FastAPI(title='Computer Use Service',version='1.0.0')
class Action(BaseModel): session_id:str; action:dict; approved:bool=False
@app.get('/health')
async def health(): return {'status':'ok','provider':'abstract','mode':'safe'}
@app.get('/snapshot/{session_id}')
async def snapshot(session_id:str):
    im=Image.new('RGB',(1280,720)); b=io.BytesIO(); im.save(b,format='PNG')
    return {'session_id':session_id,'screenshot_base64':base64.b64encode(b.getvalue()).decode(),'observation':{'type':'placeholder','message':'接入真实桌面 provider 后返回截图、窗口、坐标和可交互元素'}}
@app.post('/action')
async def action(a:Action):
    if not a.approved: raise HTTPException(428,'approval_required')
    return {'session_id':a.session_id,'status':'accepted','action':a.action}
