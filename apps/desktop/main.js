const {app,BrowserWindow}=require('electron');
function create(){const w=new BrowserWindow({width:1440,height:900,webPreferences:{contextIsolation:true,preload:require('path').join(__dirname,'preload.js')}}); w.loadURL(process.env.AGENT_WEB_URL||'http://localhost:5173');}
app.whenReady().then(create); app.on('window-all-closed',()=>{if(process.platform!=='darwin')app.quit()});
