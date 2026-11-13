'use strict';
const { app, BrowserWindow, Menu, Tray, ipcMain, screen, shell } = require('electron');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const stateDir = path.resolve(__dirname, '../.runtime/whale-desktop');
fs.mkdirSync(stateDir, { recursive: true });
app.setPath('userData', stateDir);
app.setPath('sessionData', stateDir);
app.setPath('crashDumps', path.join(stateDir, 'crashes'));
app.setAppUserModelId('WhaleCompanion.Desktop');
const port = Number(process.env.COMPANION_PORT || 8765);
if (!Number.isInteger(port) || port < 1024 || port > 65535) throw new Error('Invalid local port');
const chatUrl = `http://127.0.0.1:${port}/`;
const petUrl = pathToFileURL(path.join(__dirname, 'pet.html')).href;
const stateFile = path.join(stateDir, 'settings.json');
function diagnostic(event, detail = '') { fs.appendFileSync(path.join(stateDir, 'desktop.log'), `${new Date().toISOString()} ${event} ${detail}\n`); }
let saved = {};
try { saved = JSON.parse(fs.readFileSync(stateFile, 'utf8')); } catch {}
let skinId = ['feiyu-02', 'feiyu-03'].includes(saved.skin) ? saved.skin : 'feiyu-02';
let pet, chat, tray, mask, drag, poll, manifest, talkTimer;
let ignored = false, menuOpen = false, closing = false;
let scale = [0.24, 0.32, 0.4].includes(saved.scale) ? saved.scale : 0.32;
function persist() {
  if (!pet || pet.isDestroyed()) return;
  const bounds = pet.getBounds();
  fs.writeFileSync(stateFile, JSON.stringify({ skin: skinId, scale, x: bounds.x, y: bounds.y }));
}
function command(cmd) { if (pet && !pet.isDestroyed()) pet.webContents.send('pet:command', cmd); }
function validPet(event) { return pet && event.sender === pet.webContents && event.senderFrame?.url === petUrl; }
function validChat(event) { return chat && event.sender === chat.webContents && event.senderFrame?.url === chatUrl; }
function lockWindow(win, allowed) {
  win.webContents.on('will-navigate', (event, url) => { if (url !== allowed) event.preventDefault(); });
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (url === 'https://platform.deepseek.com/api_keys') shell.openExternal(url);
    return { action: 'deny' };
  });
  win.webContents.session.setPermissionRequestHandler((_wc, _permission, cb) => cb(false));
  win.webContents.on('will-attach-webview', event => event.preventDefault());
}
function keepOnScreen(bounds) {
  const area = screen.getDisplayMatching(bounds).workArea;
  return { ...bounds, x: Math.round(Math.max(area.x, Math.min(bounds.x, area.x + area.width - bounds.width))),
    y: Math.round(Math.max(area.y, Math.min(bounds.y, area.y + area.height - bounds.height))) };
}
function resizePet() {
  if (!pet) return;
  const old = pet.getBounds();
  const width = Math.ceil(manifest.canvas.w * scale + 50);
  const height = Math.ceil(manifest.canvas.h * scale + 50);
  pet.setBounds(keepOnScreen({ x: old.x + old.width - width, y: old.y + old.height - height, width, height }));
  pet.webContents.send('pet:scale', scale);
}
function showPet() { pet.showInactive(); pet.setBounds(keepOnScreen(pet.getBounds())); }
function openChat() {
  if (chat && !chat.isDestroyed()) { chat.show(); chat.focus(); return; }
  chat = new BrowserWindow({ title: '小肥魚 · 鯨日陪伴', width: 1100, height: 800, minWidth: 480, minHeight: 600,
    backgroundColor: '#f4f8ff', icon: path.join(__dirname, 'icon.png'), autoHideMenuBar: true,
    webPreferences: { preload: path.join(__dirname, 'chat-preload.cjs'), sandbox: true, contextIsolation: true, nodeIntegration: false } });
  lockWindow(chat, chatUrl);
  chat.loadURL(chatUrl);
  chat.once('ready-to-show', () => { chat.show(); chat.focus(); });
  chat.on('closed', () => { chat = null; });
}
function changeSkin(id) {
  if (!['feiyu-02', 'feiyu-03'].includes(id) || skinId === id) return;
  skinId = id; mask = null; drag = null;
  manifest = JSON.parse(fs.readFileSync(path.join(__dirname, 'skins', skinId, 'manifest.json'), 'utf8'));
  resizePet(); persist(); pet.reload();
  diagnostic('skin-change', id);
}
function menu() {
  return Menu.buildFromTemplate([
    { label: '和小肥魚聊天 / DeepSeek 設定', click: openChat },
    { type: 'separator' },
    { label: '摸摸頭', click: () => command('pat') },
    { label: '搖搖尾巴', click: () => command('wag') },
    { label: '換個造型', submenu: [
      { label: '全身鯨魚娘', type: 'radio', checked: skinId === 'feiyu-02', click: () => changeSkin('feiyu-02') },
      { label: 'Q 版小肥魚', type: 'radio', checked: skinId === 'feiyu-03', click: () => changeSkin('feiyu-03') }] },
    { label: '桌寵大小', submenu: [ ['小', 0.24], ['中', 0.32], ['大', 0.4] ].map(([label, value]) => ({
      label, type: 'radio', checked: scale === value, click: () => { scale = value; resizePet(); persist(); } })) },
    { label: '找回小肥魚', click: showPet },
    { label: '暫時隱藏', click: () => pet.hide() },
    { type: 'separator' },
    { label: '退出桌寵', click: () => app.quit() }
  ]);
}
function setIgnored(value) {
  if (ignored === value) return;
  ignored = value;
  pet.setIgnoreMouseEvents(value, { forward: true });
  pet.webContents.send('pet:input', !value);
}
function pollPointer() {
  if (!pet || pet.isDestroyed() || !pet.isVisible()) return;
  const point = screen.getCursorScreenPoint();
  if (drag) {
    const bounds = keepOnScreen({ x: point.x - drag.dx, y: point.y - drag.dy, width: drag.width, height: drag.height });
    pet.setBounds(bounds); setIgnored(false); return;
  }
  if (!mask || menuOpen) return;
  const bounds = pet.getBounds();
  const x = (point.x - bounds.x - (bounds.width - manifest.canvas.w * scale) / 2) / scale;
  const y = (point.y - bounds.y - (bounds.height - manifest.canvas.h * scale)) / scale;
  const mx = Math.floor(x / manifest.canvas.w * mask.w), my = Math.floor(y / manifest.canvas.h * mask.h);
  // A small margin accommodates sway and animated edges of the static alpha mask.
  let hit = false;
  for (let dy = -3; dy <= 3 && !hit; dy++) for (let dx = -3; dx <= 3; dx++) {
    const xx = mx + dx, yy = my + dy;
    if (xx >= 0 && yy >= 0 && xx < mask.w && yy < mask.h && mask.bits[yy * mask.w + xx]) { hit = true; break; }
  }
  setIgnored(!hit);
}
ipcMain.handle('pet:skin', event => {
  if (!validPet(event)) return null;
  diagnostic('skin-request', skinId);
  return { manifest, id: skinId, scale, baseUrl: pathToFileURL(path.join(__dirname, 'skins', skinId) + path.sep).href };
});
ipcMain.on('pet:log', (event, message) => { if (validPet(event) && typeof message === 'string') diagnostic('pet', message.slice(0, 240)); });
ipcMain.on('pet:mask', (event, data) => {
  if (!validPet(event) || data?.w !== 256 || data?.h !== 256 || data?.bits?.length !== 65536) return;
  mask = data;
  diagnostic('mask-ready', skinId);
});
ipcMain.on('pet:drag-start', (event, point) => {
  if (!validPet(event)) return;
  const bounds = pet.getBounds();
  if (!point || !Number.isFinite(point.x) || !Number.isFinite(point.y) || point.x < 0 || point.y < 0 || point.x > bounds.width || point.y > bounds.height) return;
  drag = { dx: point.x, dy: point.y, width: bounds.width, height: bounds.height };
  pollPointer();
  setIgnored(false);
  diagnostic('drag-start');
});
ipcMain.on('pet:drag-end', event => { if (validPet(event)) { if (drag) pollPointer(); drag = null; persist(); diagnostic('drag-end'); } });
ipcMain.on('pet:menu', event => {
  if (!validPet(event)) return;
  drag = null; menuOpen = true; setIgnored(false);
  menu().popup({ window: pet, callback: () => { menuOpen = false; } });
});
ipcMain.on('pet:chat', event => { if (validPet(event)) openChat(); });
ipcMain.on('chat:action', (event, action) => {
  if (!validChat(event)) return;
  if (['pat', 'wag', 'blink'].includes(action)) command(action);
  if (action === 'show') showPet();
  if (['feiyu-02', 'feiyu-03'].includes(action)) changeSkin(action);
  if (action === 'reply') {
    command('talk-start'); clearTimeout(talkTimer);
    talkTimer = setTimeout(() => command('talk-stop'), 4000);
  }
});
if (!app.requestSingleInstanceLock()) app.quit();
else {
  app.on('second-instance', () => { showPet(); openChat(); });
  app.whenReady().then(() => {
    manifest = JSON.parse(fs.readFileSync(path.join(__dirname, 'skins', skinId, 'manifest.json'), 'utf8'));
    const area = screen.getPrimaryDisplay().workArea;
    const size = Math.ceil(1280 * scale + 50);
    const bounds = keepOnScreen({ width: size, height: size,
      x: Number.isFinite(saved.x) ? saved.x : area.x + area.width - size - 35,
      y: Number.isFinite(saved.y) ? saved.y : area.y + area.height - size });
    pet = new BrowserWindow({ ...bounds, title: '小肥魚桌寵', transparent: true, frame: false, resizable: false,
      alwaysOnTop: true, skipTaskbar: true, hasShadow: false, backgroundColor: '#00000000', show: false,
      webPreferences: { preload: path.join(__dirname, 'preload.cjs'), sandbox: true, contextIsolation: true, nodeIntegration: false, backgroundThrottling: false } });
    lockWindow(pet, petUrl);
    pet.setAlwaysOnTop(true, 'screen-saver');
    pet.webContents.on('render-process-gone', (_event, details) => diagnostic('renderer-exited', JSON.stringify(details)));
    pet.webContents.on('did-fail-load', (_event, code, description) => diagnostic('load-failed', `${code} ${description}`));
    pet.webContents.on('console-message', details => diagnostic('renderer', details.message));
    pet.webContents.on('did-finish-load', () => diagnostic('loaded', skinId));
    pet.loadURL(petUrl);
    pet.once('ready-to-show', () => pet.show());
    pet.on('close', event => { if (!closing) { event.preventDefault(); pet.hide(); } });
    tray = new Tray(path.join(__dirname, 'icon.png'));
    tray.setToolTip('小肥魚 · 雙擊聊天 / 右鍵選單');
    tray.on('double-click', openChat);
    tray.on('right-click', () => menu().popup());
    poll = setInterval(pollPointer, 32);
    screen.on('display-removed', showPet);
    openChat();
  });
}
app.on('window-all-closed', () => {});
app.on('before-quit', () => { closing = true; persist(); clearInterval(poll); clearTimeout(talkTimer); });
