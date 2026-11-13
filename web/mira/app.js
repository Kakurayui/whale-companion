'use strict';
const $ = (id) => document.getElementById(id);
const storage = {
  get(key) { try { return localStorage.getItem(key); } catch { return null; } },
  set(key, value) { try { localStorage.setItem(key, value); } catch { /* Session works without persistence. */ } },
};
const visitor = storage.get('mira-visitor') || crypto.randomUUID();
storage.set('mira-visitor', visitor);
let session = null, memory = {}, status = null, busy = false;

async function api(path, data) {
  const response = await fetch(path, data === undefined ? {} : {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data),
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Something went wrong. Please try again.');
  return result;
}

function showError(message) { $('error').textContent = message; $('error').hidden = !message; }
function setBusy(value) {
  busy = value;
  for (const id of ['send','new-chat','mode-baseline','mode-enhanced','forget','memory-edit','settings-open','connect-banner','export']) $(id).disabled = value;
  for (const button of $('suggestions').querySelectorAll('button')) button.disabled = value;
  $('message-input').disabled = value;
}

function addMessage(role, text, waiting = false) {
  const article = document.createElement('article');
  article.className = `message ${role}${waiting ? ' waiting' : ''}`;
  if (role === 'assistant') {
    const avatar = document.createElement('img'); avatar.src = '/mira.svg'; avatar.alt = ''; avatar.className = 'avatar'; article.append(avatar);
  }
  const body = document.createElement('div'); body.className = 'message-body';
  const label = document.createElement('p'); label.className = 'message-label'; label.textContent = role === 'user' ? 'YOU' : 'MIRA';
  const content = document.createElement('p'); content.className = 'message-content'; content.textContent = text;
  body.append(label, content); article.append(body); $('messages').append(article);
  $('messages').scrollTop = $('messages').scrollHeight;
  return article;
}

function renderMemory() {
  $('memory-list').replaceChildren();
  $('memory-empty').hidden = Object.keys(memory).length > 0;
  for (const [field, label] of Object.entries({name:'Your name',preference:'A preference',goal:'Your goal'})) {
    if (!memory[field]) continue;
    const dt = document.createElement('dt'); dt.textContent = label;
    const dd = document.createElement('dd'); dd.textContent = memory[field];
    $('memory-list').append(dt, dd);
  }
}

function research(metadata) {
  $('research-mode').textContent = session?.mode === 'baseline' ? 'Baseline' : 'Enhanced';
  $('research-model').textContent = metadata?.model || status?.model || '—';
  $('research-latency').textContent = metadata ? `${metadata.latency_seconds.toFixed(2)} s` : '—';
  $('research-lore').textContent = metadata ? (metadata.retrieved.map(d => d.title).join(', ') || 'None') : 'No reply yet';
}

function renderSession() {
  $('messages').replaceChildren();
  addMessage('assistant', status.character.greeting);
  for (const message of session.messages) addMessage(message.role, message.content);
  const enhanced = session.mode === 'enhanced';
  for (const mode of ['baseline','enhanced']) {
    $(`mode-${mode}`).classList.toggle('active', session.mode === mode);
    $(`mode-${mode}`).setAttribute('aria-pressed', String(session.mode === mode));
  }
  $('mode-note').textContent = enhanced ? 'Mira can draw on her world and remember the details you share.' : 'Baseline uses the character profile and the last three exchanges. Saved details and world notes are not supplied.';
  $('suggestions').hidden = session.messages.length > 0;
  research([...session.messages].reverse().find(m => m.metadata)?.metadata);
  renderMemory();
}

async function newSession(mode = session?.mode || 'enhanced') {
  const result = await api('/api/session', {visitor,mode});
  session = result.session; memory = result.memory;
  storage.set('mira-session', session.id); renderSession(); showError('');
}

async function refreshStatus() {
  status = await api('/api/status');
  $('connection-status').textContent = status.configured ? `${status.provider === 'deepseek' ? 'DeepSeek' : 'Ollama'} · ${status.model}` : 'Waiting for a model connection';
  $('status-dot').classList.toggle('ready', status.configured);
  $('connection-banner').hidden = status.configured;
}

async function sendMessage(event) {
  event?.preventDefault();
  const text = $('message-input').value.trim();
  if (!text || busy || !session) return;
  if (!status.configured) { $('settings-dialog').showModal(); return; }
  setBusy(true); showError(''); $('suggestions').hidden = true;
  const userBubble = addMessage('user', text);
  const waiting = addMessage('assistant', 'Mira is gathering her thoughts…', true);
  try {
    const result = await api('/api/chat', {visitor,session:session.id,message:text});
    waiting.remove(); addMessage('assistant', result.answer);
    session.messages.push({role:'user',content:text},{role:'assistant',content:result.answer,metadata:result.metadata});
    memory = result.memory; renderMemory(); research(result.metadata); $('message-input').value = '';
  } catch (error) { waiting.remove(); userBubble.remove(); showError(error.message); }
  finally { setBusy(false); $('message-input').focus(); }
}

$('chat-form').addEventListener('submit', sendMessage);
$('message-input').addEventListener('keydown', event => {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) { event.preventDefault(); sendMessage(); }
});
for (const mode of ['baseline','enhanced']) $(`mode-${mode}`).addEventListener('click', async () => {
  if (busy || session?.mode === mode) return;
  setBusy(true); try { await newSession(mode); } catch (error) { showError(error.message); } finally { setBusy(false); }
});
$('new-chat').addEventListener('click', async () => {
  if (busy) return; setBusy(true);
  try { await newSession(); } catch (error) { showError(error.message); } finally { setBusy(false); }
});
for (const id of ['settings-open','connect-banner']) $(id).addEventListener('click', () => $('settings-dialog').showModal());
for (const close of document.querySelectorAll('[data-close]')) close.addEventListener('click', () => $(close.dataset.close).close());
$('settings-dialog').addEventListener('close', () => { $('api-key').value = ''; $('settings-status').textContent = ''; });
$('settings-form').addEventListener('submit', async event => {
  event.preventDefault(); $('connect-submit').disabled = true; $('settings-status').textContent = 'Checking your connection…';
  try {
    await api('/api/connect', {key:$('api-key').value,model:$('model').value});
    $('api-key').value = ''; await refreshStatus(); $('settings-dialog').close(); research(); $('message-input').focus();
  } catch (error) { $('settings-status').textContent = error.message; }
  finally { $('connect-submit').disabled = false; }
});
$('memory-edit').addEventListener('click', () => {
  for (const field of ['name','preference','goal']) $(`memory-${field}`).value = memory[field] || '';
  $('memory-dialog').showModal();
});
$('memory-form').addEventListener('submit', async event => {
  event.preventDefault(); const button = event.submitter; button.disabled = true;
  try {
    const values = Object.fromEntries(['name','preference','goal'].map(field => [field,$(`memory-${field}`).value]));
    const result = await api('/api/memory', {visitor,values}); memory = result.memory; renderMemory(); $('memory-dialog').close();
  } catch (error) { $('memory-dialog').close(); showError(error.message); }
  finally { button.disabled = false; }
});
$('forget').addEventListener('click', async () => {
  if (busy || !confirm('Forget your saved details and delete all your conversations on this computer?')) return;
  setBusy(true);
  try { await api('/api/forget', {visitor}); await newSession(); } catch (error) { showError(error.message); } finally { setBusy(false); }
});
$('export').addEventListener('click', () => {
  if (!session) return;
  const a = document.createElement('a'); a.href = `/api/export?visitor=${encodeURIComponent(visitor)}&session=${encodeURIComponent(session.id)}`; a.download = 'mira-conversation.json'; a.click();
});

(async function init() {
  setBusy(true);
  try {
    await refreshStatus();
    for (const text of status.character.suggestions) {
      const button = document.createElement('button'); button.textContent = text;
      button.addEventListener('click', () => { if (!busy) { $('message-input').value = text; $('message-input').focus(); } });
      $('suggestions').append(button);
    }
    const saved = storage.get('mira-session');
    if (saved) {
      try { const result = await api(`/api/session?visitor=${encodeURIComponent(visitor)}&session=${encodeURIComponent(saved)}`); session = result.session; memory = result.memory; renderSession(); }
      catch { await newSession(); }
    } else await newSession();
  } catch (error) { showError(error.message); }
  finally { setBusy(false); }
})();
