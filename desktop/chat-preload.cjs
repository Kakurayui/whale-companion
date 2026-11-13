const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('whale', { action: action => {
  if (['pat', 'wag', 'blink', 'show', 'reply', 'feiyu-02', 'feiyu-03'].includes(action)) ipcRenderer.send('chat:action', action);
} });
