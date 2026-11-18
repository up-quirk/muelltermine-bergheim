'use strict';
const $ = id => document.getElementById(id);
let state, draft, selectedRule = 0, selectedDocument = '', result, dirty = false, previewTimer, previewSequence = 0, editRevision = 0, pdfPage = 1;
const settingKeys = ['district', 'overview_url', 'source_format', 'pdf_url_pattern', 'ics_url_pattern', 'link_pattern', 'next_year_month'];
const escapeHTML = text => String(text ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function api(path, body, options = {}) {
  const response = await fetch(path, body === undefined ? options : {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body), ...options});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Die Anfrage ist fehlgeschlagen.');
  return data;
}
function notice(message, error = false) {
  $('notice').textContent = message; $('notice').className = error ? 'error' : ''; $('notice').hidden = false;
}
function setDirty(value = true) {
  if (value) editRevision++;
  dirty = value; $('dirty').textContent = value ? 'Ungespeicherte Änderungen' : 'Alles gespeichert';
  $('dirty').classList.toggle('changed', value);
}
function renderRules() {
  $('rule-list').innerHTML = draft.rules.map((r, i) => `<button class="rule-card ${selectedRule === i ? 'active' : ''} ${r.enabled === false ? 'disabled' : ''}" data-rule="${i}" aria-pressed="${selectedRule === i}"><span class="rule-dot" data-color="${escapeHTML(r.color)}"></span><span class="rule-label">${escapeHTML(r.name)}</span><span class="rule-count">${result?.counts?.[r.id] ?? '—'}</span></button>`).join('');
  document.querySelectorAll('[data-color]').forEach(el => el.style.backgroundColor = el.dataset.color);
  document.querySelectorAll('[data-rule]').forEach(button => button.onclick = () => {selectedRule = Number(button.dataset.rule); renderRules(); renderEditor(); renderResults();});
}
function renderEditor() {
  const r = draft.rules[selectedRule];
  $('rule-name').value = r.name; $('rule-id').value = r.id; $('rule-pattern').value = r.pattern;
  $('rule-color').value = r.color || '#64748b'; $('case-sensitive').checked = Boolean(r.case_sensitive);
  $('rule-enabled').checked = r.enabled !== false; $('delete-rule').disabled = draft.rules.length <= 1;
}
function renderDocuments(preferred) {
  const available = state.documents;
  if (preferred) selectedDocument = preferred;
  if (!available.some(d => d.id === selectedDocument)) selectedDocument = available.find(d => d.format === 'pdf')?.id || available[0]?.id || '';
  $('document').innerHTML = available.length ? available.map(d => `<option value="${d.id}">${d.year} · ${escapeHTML(d.district)} · ${d.format.toUpperCase()}${d.active ? ' · aktiv' : ' · Test / Archiv'}</option>`).join('') : '<option value="">Noch kein Dokument geladen</option>';
  $('document').value = selectedDocument;
  const doc = available.find(d => d.id === selectedDocument);
  $('document-info').textContent = doc ? `${doc.record_count} Einträge · ${doc.year} · ${doc.format.toUpperCase()}` : 'Noch kein Dokument ausgewählt';
  const src = doc?.format === 'pdf' ? `api/documents/${doc.id}` : '';
  $('open-pdf').href = src || '#'; $('open-pdf').hidden = !src;
  renderPDF();
}
function renderPDF() {
  const doc = state.documents.find(d => d.id === selectedDocument);
  const count = doc?.page_count || (doc?.format === 'pdf' ? 2 : 0);
  pdfPage = Math.max(1, Math.min(pdfPage,count));
  const src = doc?.format === 'pdf' ? `api/documents/${doc.id}/page/${pdfPage}.png` : '';
  if ($('pdf-image').getAttribute('src') !== src) {if (src) $('pdf-image').src = src; else $('pdf-image').removeAttribute('src');}
  $('pdf-image').hidden = !src; $('pdf-page-label').textContent = count ? `Seite ${pdfPage} von ${count}` : 'Kein PDF ausgewählt';
  $('pdf-prev').disabled = pdfPage <= 1; $('pdf-next').disabled = pdfPage >= count;
}
$('pdf-prev').onclick = () => {pdfPage--; renderPDF();};
$('pdf-next').onclick = () => {pdfPage++; renderPDF();};
function renderStatus() {
  const s = state.status;
  const last = s.last_success ? new Date(s.last_success).toLocaleString('de-DE') : 'noch kein erfolgreicher Abruf';
  $('status-text').textContent = s.refreshing ? 'Kalender werden abgerufen …' : `${s.event_count} aktive Termine · Letzter Abruf: ${last}${s.errors.length ? ` · ${s.errors.length} Abrufhinweis(e)` : ''}`;
  $('refresh').disabled = s.refreshing;
  $('status-details').textContent = `Aktive Kalenderjahre: ${s.active_years.join(', ') || 'keine'}\nLetzter Versuch: ${s.last_attempt ? new Date(s.last_attempt).toLocaleString('de-DE') : 'noch keiner'}\n\n${s.errors.join('\n\n') || 'Keine Abruffehler.'}`;
}
async function loadState(initial = false, preferred) {
  state = await api('api/state');
  if (initial) {draft = structuredClone(state.config); settingKeys.forEach(key => $(key).value = draft[key]); renderRules(); renderEditor();}
  renderDocuments(preferred); renderStatus();
}
function highlight(text, spans) {
  let cursor = 0, html = '';
  for (const span of spans) {html += escapeHTML(text.slice(cursor, span.start)) + '<mark>' + escapeHTML(text.slice(span.start, span.end)) + '</mark>'; cursor = span.end;}
  return html + escapeHTML(text.slice(cursor));
}
function renderResults() {
  if (!result) return;
  const all = $('result-filter').value === 'all';
  const rule = draft.rules[selectedRule];
  const matches = result.matches.filter(m => all || m.rule_id === rule.id);
  const count = all ? result.events.length : (result.counts[rule.id] || 0);
  $('result-summary').innerHTML = `<strong>${count}</strong><div>Termine erkannt<small>${all ? 'Alle aktiven Tonnen' : escapeHTML(rule.name)} · ${result.record_count} Kalendereinträge geprüft</small></div>`;
  if (!matches.length) {$('match-list').innerHTML = '<div class="empty"><span aria-hidden="true">⌕</span><h3>Keine Treffer für dieses Muster</h3><p>Prüfe die Schreibweise oder passe den Ausdruck an.</p></div>'; return;}
  let lastMonth = '';
  $('match-list').innerHTML = matches.map(m => {
    const d = new Date(m.date + 'T12:00:00'); const month = d.toLocaleDateString('de-DE',{month:'long',year:'numeric'});
    const heading = month !== lastMonth ? `<div class="match-year">${escapeHTML(month.toUpperCase())}</div>` : ''; lastMonth = month;
    return heading + `<div class="match-row"><div class="date-tile"><strong>${d.getDate().toString().padStart(2,'0')}</strong><small>${d.toLocaleDateString('de-DE',{weekday:'short'}).replace('.','').toUpperCase()}</small></div><div class="match-content"><div class="match-title">${escapeHTML(m.name)}</div><div class="match-text">${highlight(m.text,m.spans)}</div></div>${m.page ? `<a class="page-link" href="api/documents/${selectedDocument}#page=${m.page}" target="_blank" rel="noopener">Seite ${m.page} ↗</a>` : '<span class="page-link">ICS</span>'}</div>`;
  }).join('');
}
function schedulePreview() {
  clearTimeout(previewTimer); previewSequence++;
  $('preview-state').textContent = '● Wird geprüft …'; $('preview-state').classList.add('busy');
  previewTimer = setTimeout(runPreview, 350);
}
async function runPreview() {
  const seq = ++previewSequence;
  if (!selectedDocument) {$('preview-state').textContent = '● PDF auswählen'; $('preview-state').classList.remove('busy'); return;}
  try {
    const next = await api('api/preview', {document_id:selectedDocument, rules:draft.rules});
    if (seq !== previewSequence) return;
    result = next; $('result-error').hidden = true; renderRules(); renderResults();
    $('preview-state').textContent = '● Live-Vorschau';
  } catch (error) {
    if (seq !== previewSequence) return;
    result = null; $('result-error').textContent = error.message; $('result-error').hidden = false;
    $('match-list').innerHTML = ''; $('result-summary').innerHTML = '<strong>—</strong><div>Muster prüfen<small>Die letzte Vorschau wurde verworfen.</small></div>';
    $('preview-state').textContent = '● Muster prüfen';
  } finally {if (seq === previewSequence) $('preview-state').classList.remove('busy');}
}
for (const [field,key] of [['rule-name','name'],['rule-id','id'],['rule-pattern','pattern'],['rule-color','color'],['case-sensitive','case_sensitive'],['rule-enabled','enabled']]) {
  $(field).addEventListener('input', () => {draft.rules[selectedRule][key] = $(field).type === 'checkbox' ? $(field).checked : $(field).value; setDirty(); if (field !== 'rule-pattern') renderRules(); schedulePreview();});
}
for (const key of settingKeys) $(key).addEventListener('input', () => {draft[key] = key === 'next_year_month' ? Number($(key).value) : $(key).value; setDirty();});
$('document').onchange = () => {selectedDocument = $('document').value; pdfPage = 1; result = null; renderDocuments(); schedulePreview();};
$('result-filter').onchange = renderResults;
$('add-rule').onclick = () => {const id = 'tonne_' + Date.now().toString(36); draft.rules.push({id,name:'Neue Tonne',pattern:'Suchtext',enabled:true,case_sensitive:false,color:'#64748b'}); selectedRule = draft.rules.length-1; setDirty(); renderRules(); renderEditor(); schedulePreview();};
$('delete-rule').onclick = () => {if (draft.rules.length <= 1) return; draft.rules.splice(selectedRule,1); selectedRule = Math.max(0,selectedRule-1); setDirty(); renderRules(); renderEditor(); schedulePreview();};
$('save').onclick = async () => {
  $('save').disabled = true;
  const revision = editRevision, submitted = structuredClone(draft);
  try {const saved = await api('api/config',submitted); if (revision === editRevision) {draft = saved; setDirty(false); notice('Einstellungen übernommen. Der Kalender verwendet jetzt diese Regeln.');} else {notice('Einstellungen gespeichert. Deine neueren Eingaben sind noch nicht übernommen.');} await loadState(); await runPreview();}
  catch(error) {notice(error.message,true);} finally {$('save').disabled = false;}
};
$('refresh').onclick = async () => {try {await api('api/refresh',{}); notice('Abruf mit den gespeicherten Einstellungen gestartet.'); $('refresh').disabled = true; setTimeout(poll,1000);} catch(error) {notice(error.message,true);}};
$('upload-toggle').onclick = () => {$('upload-form').hidden = !$('upload-form').hidden;};
$('upload-form').onsubmit = async event => {
  event.preventDefault(); const file = $('upload-file').files[0]; if (!file) return;
  if (file.size > 20*1024*1024) {notice('Die Datei ist größer als 20 MB.',true); return;}
  const button = $('upload-form').querySelector('button'); button.disabled = true;
  try {const response = await fetch(`api/upload?year=${encodeURIComponent($('upload-year').value)}`,{method:'POST',headers:{'Content-Type':'application/pdf'},body:file}); const value = await response.json(); if (!response.ok) throw new Error(value.error); await loadState(false,value.id); await runPreview(); $('upload-form').hidden = true; notice('PDF zum Testen geladen. Die aktive Kalenderquelle wurde nicht geändert.');}
  catch(error) {notice(error.message,true);} finally {button.disabled = false;}
};
document.querySelectorAll('[data-view]').forEach(button => button.onclick = () => {document.querySelectorAll('[data-view]').forEach(b => b.classList.toggle('active',b===button)); $('rules-view').hidden = button.dataset.view !== 'rules'; $('settings-view').hidden = button.dataset.view !== 'settings';});
document.querySelectorAll('[data-tab]').forEach(button => button.onclick = () => {document.querySelectorAll('[data-tab]').forEach(b => b.classList.toggle('active',b===button)); const pdf = button.dataset.tab === 'pdf'; $('match-list').hidden = pdf; $('result-summary').hidden = pdf; $('result-filter').disabled = pdf; $('pdf-panel').hidden = !pdf;});
window.addEventListener('beforeunload',event => {if (dirty) {event.preventDefault(); event.returnValue = '';}});
async function poll() {try {const previous = state?.status?.last_attempt; await loadState(); if (state.status.last_attempt !== previous) await runPreview();} catch(error) {notice('Verbindung zur App unterbrochen. ' + error.message,true);}}
$('upload-year').value = new Date().getFullYear();
loadState(true).then(runPreview).catch(error => notice(error.message,true));
setInterval(poll,5000);
