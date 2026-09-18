import base64, os, uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from playwright.async_api import async_playwright

app = FastAPI(title="Agent Browser Service", version="0.3.0")
browser = None
pw = None
contexts = {}

class NavigateRequest(BaseModel):
    url: HttpUrl
    wait_until: str = "domcontentloaded"

class ClickRequest(BaseModel):
    session_id: str
    selector: str
    approved: bool = False

class TypeRequest(BaseModel):
    session_id: str
    selector: str
    text: str
    approved: bool = False

@app.on_event("startup")
async def startup():
    global pw, browser
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=True)

@app.on_event("shutdown")
async def shutdown():
    global browser, pw
    for c in contexts.values(): await c.close()
    if browser: await browser.close()
    if pw: await pw.stop()

@app.get('/health')
async def health(): return {'status':'ok','version':'0.3.0'}

@app.post('/session')
async def create_session():
    sid = str(uuid.uuid4())
    contexts[sid] = await browser.new_context()
    page = await contexts[sid].new_page()
    await page.goto('about:blank')
    return {'session_id':sid}

@app.post('/navigate')
async def navigate(req: NavigateRequest):
    sid = str(uuid.uuid4()); context = await browser.new_context(); contexts[sid] = context
    page = await context.new_page()
    await page.goto(str(req.url), wait_until=req.wait_until)
    return {'session_id':sid,'url':page.url,'title':await page.title(),'text':(await page.locator('body').inner_text())[:12000]}

async def page_for(sid):
    c = contexts.get(sid)
    if not c: raise HTTPException(404,'session_not_found')
    pages = c.pages
    if not pages: raise HTTPException(404,'page_not_found')
    return pages[-1]

@app.post('/click')
async def click(req: ClickRequest):
    if not req.approved: raise HTTPException(428,'approval_required')
    page = await page_for(req.session_id); await page.locator(req.selector).click()
    return {'ok':True,'url':page.url,'title':await page.title()}

@app.post('/type')
async def type_text(req: TypeRequest):
    if not req.approved: raise HTTPException(428,'approval_required')
    page = await page_for(req.session_id); await page.locator(req.selector).fill(req.text)
    return {'ok':True}

@app.get('/snapshot/{session_id}')
async def snapshot(session_id:str):
    page = await page_for(session_id)
    png = await page.screenshot(type='png', full_page=True)
    return {'url':page.url,'title':await page.title(),'image_base64':base64.b64encode(png).decode(),'text':(await page.locator('body').inner_text())[:12000]}
