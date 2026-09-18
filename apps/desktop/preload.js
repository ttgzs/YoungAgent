const { contextBridge } = require('electron');
contextBridge.exposeInMainWorld('youngagent', { version: '4.0.0' });
