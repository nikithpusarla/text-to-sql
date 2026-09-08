const form = document.querySelector('#query-form');
const input = document.querySelector('#query-input');
const conversation = document.querySelector('#conversation');
let sessionId = null;

function showConversation(html) {
  conversation.classList.remove('hidden');
  conversation.innerHTML = html;
  conversation.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function loading() { showConversation('<div class="loading">Reading your question...</div>'); }

async function ask(query) {
  loading();
  const response = await fetch('/query', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ query, session_id: sessionId }) });
  if (!response.ok) throw new Error('The query could not be processed.');
  const data = await response.json();
  sessionId = data.session_id;
  if (data.questions?.length) return renderQuestions(data.questions);
  return renderResult(data.result);
}

function renderQuestions(questions) {
  const cards = questions.map(question => `<div class="question-card"><p>CLARIFYING ${question.slot_name.toUpperCase()}</p><h3>${question.question_text}</h3><div class="options">${question.options.map(option => `<button class="option" data-slot="${question.slot_name}" data-value="${option}">${option.replaceAll('_', ' ')}</button>`).join('')}</div></div>`).join('');
  showConversation(cards);
  document.querySelectorAll('.option').forEach(button => button.addEventListener('click', () => clarify(button.dataset.slot, button.dataset.value)));
}

async function clarify(slotName, value) {
  showConversation('<div class="loading">Resolving intent and preparing your answer...</div>');
  const response = await fetch('/clarify', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ session_id: sessionId, slot_name: slotName, chosen_value: value }) });
  if (!response.ok) throw new Error('The clarification could not be processed.');
  const data = await response.json();
  if (data.questions?.length) return renderQuestions(data.questions);
  return renderResult(data.result);
}

async function renderResult(result) {
  const response = await fetch('/execute', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ sql: result.sql }) });
  if (!response.ok) throw new Error('The answer could not be loaded from the database.');
  const data = await response.json();
  const columns = data.rows.length ? Object.keys(data.rows[0]) : [];
  const header = columns.map(column => `<th>${column.replaceAll('_', ' ')}</th>`).join('');
  const rows = data.rows.slice(0, 20).map(row => `<tr>${columns.map(column => `<td>${row[column] ?? ''}</td>`).join('')}</tr>`).join('');
  showConversation(`<div class="answer-card"><div class="result-label"><strong>Your answer</strong><span>${data.row_count} ROWS</span></div>${data.rows.length ? `<table class="answer-table"><thead><tr>${header}</tr></thead><tbody>${rows}</tbody></table>` : '<p class="loading">No matching rows found.</p>'}<details><summary>View generated SQL</summary><pre class="sql">${data.sql}</pre></details></div>`);
}

form.addEventListener('submit', event => { event.preventDefault(); const query = input.value.trim(); if (query) ask(query).catch(error => showConversation(`<div class="question-card"><h3>Something went wrong</h3><p>${error.message}</p></div>`)); });
input.addEventListener('keydown', event => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); form.requestSubmit(); } });
document.querySelectorAll('[data-query]').forEach(button => button.addEventListener('click', () => { input.value = button.dataset.query; input.focus(); }));
