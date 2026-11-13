const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('pet', {
  getSkin: () => ipcRenderer.invoke('pet:skin'),
  setMask: value => ipcRenderer.send('pet:mask', value),
  dragStart: point => ipcRenderer.send('pet:drag-start', point),
  dragEnd: () => ipcRenderer.send('pet:drag-end'),
  openMenu: () => ipcRenderer.send('pet:menu'),
  openChat: () => ipcRenderer.send('pet:chat'),
  onCommand: cb => ipcRenderer.on('pet:command', (_e, cmd) => cb(cmd)),
  onScale: cb => ipcRenderer.on('pet:scale', (_e, scale) => cb(scale)),
  onInputMode: cb => ipcRenderer.on('pet:input', (_e, interactive) => cb(interactive)),
  log: message => ipcRenderer.send('pet:log', String(message).slice(0, 240))
});
