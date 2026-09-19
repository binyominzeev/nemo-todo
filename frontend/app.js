const state = { data: { tasks: [], tables: [] }, view: "table", widths: {} };

function send(command, payload = {}) {
  const handler = window.webkit?.messageHandlers?.nemo;
  if (handler) handler.postMessage(JSON.stringify({ command, payload }));
}

window.nemoTodoReceive = function (data) {
  state.data = data;
  render();
};

window.nemoTodoError = function (message) {
  const error = document.querySelector("#error");
  error.textContent = message;
  error.hidden = false;
  window.setTimeout(() => { error.hidden = true; }, 3500);
};

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[char]));
}

function render() {
  document.querySelector("#folder").textContent = state.data.folder || "No folder selected";
  renderTasks();
  renderTables();
}

function renderTasks() {
  const tasks = state.data.tasks || [];
  document.querySelector("#task-count").textContent = `${tasks.filter(task => task.completed).length}/${tasks.length}`;
  document.querySelector("#tasks").innerHTML = tasks.length ? tasks.map(task => `
    <div class="task ${task.completed ? "done" : ""}">
      <input type="checkbox" data-task-toggle="${task.id}" ${task.completed ? "checked" : ""} aria-label="Complete ${escapeHtml(task.text)}">
      <input type="text" data-task-text="${task.id}" value="${escapeHtml(task.text)}">
      <button class="icon-button" data-task-delete="${task.id}" title="Delete TODO">&#215;</button>
    </div>`).join("") : '<div class="empty">No TODOs in this folder.</div>';
}

function renderTables() {
  const tables = state.data.tables || [];
  document.querySelector("#tables").innerHTML = tables.length ? tables.map(table => state.view === "cards" ? renderCards(table) : renderTable(table)).join("") : '<div class="empty">No checklists in this folder.</div>';
}

function renderTable(table) {
  const columns = table.columns || [];
  const rows = table.rows || [];
  const completed = table.cells.filter(cell => cell.completed).length;
  const total = rows.length * columns.length;
  const widths = [190, ...columns.map(column => state.widths[`${table.id}:${column.id}`] || 120)];
  const gridStyle = `grid-template-columns:${widths.map(width => `${width}px`).join(" ")}`;
  return `<article class="table-card">
    <div class="table-top"><input class="table-title" data-table-name="${table.id}" value="${escapeHtml(table.name)}"><span class="table-summary">${completed}/${total} completed</span><button class="icon-button" data-table-delete="${table.id}" title="Delete checklist">&#215;</button></div>
    <div class="table-scroll"><div class="grid" style="${gridStyle}">
      <div class="grid-cell grid-header">Item</div>${columns.map(column => `<div class="grid-cell grid-header"><input class="column-name" data-column-name="${column.id}" value="${escapeHtml(column.name)}"><span class="resize-handle" data-resize-table="${table.id}" data-resize-column="${column.id}"></span></div>`).join("")}
      ${rows.map(row => `<div class="grid-cell grid-row-name"><input class="row-name" data-row-name="${row.id}" value="${escapeHtml(row.name)}"><button class="icon-button" data-row-delete="${row.id}" title="Delete row">&#215;</button></div>${columns.map(column => `<div class="grid-cell"><input type="checkbox" data-cell-row="${row.id}" data-cell-column="${column.id}" ${cellValue(table, row.id, column.id) ? "checked" : ""} aria-label="${escapeHtml(row.name)} / ${escapeHtml(column.name)}"></div>`).join("")}`).join("")}
    </div></div>
    <div class="table-actions"><button data-add-row="${table.id}">+ Row</button><button data-add-column="${table.id}">+ Column</button></div>
  </article>`;
}

function renderCards(table) {
  const columns = table.columns || [];
  const completed = table.cells.filter(cell => cell.completed).length;
  const total = table.rows.length * columns.length;
  return `<article class="table-card"><div class="table-top"><input class="table-title" data-table-name="${table.id}" value="${escapeHtml(table.name)}"><span class="table-summary">${completed}/${total} completed</span><button class="icon-button" data-table-delete="${table.id}" title="Delete checklist">&#215;</button></div>${table.rows.map(row => `<div class="card-row"><div class="card-check"><input class="row-name" data-row-name="${row.id}" value="${escapeHtml(row.name)}"><button class="icon-button" data-row-delete="${row.id}" title="Delete row">&#215;</button></div>${columns.map(column => `<label class="card-check"><span>${escapeHtml(column.name)}</span><input type="checkbox" data-cell-row="${row.id}" data-cell-column="${column.id}" ${cellValue(table, row.id, column.id) ? "checked" : ""}></label>`).join("")}</div>`).join("")}<div class="table-actions"><button data-add-row="${table.id}">+ Row</button><button data-add-column="${table.id}">+ Column</button></div></article>`;
}

function cellValue(table, rowId, columnId) {
  return table.cells.some(cell => cell.row_id === rowId && cell.column_id === columnId && cell.completed);
}

async function promptValue(label) {
  const value = window.prompt(label);
  return value && value.trim();
}

document.addEventListener("click", async event => {
  const target = event.target;
  if (target.matches("[data-action=create-task]")) { const text = await promptValue("TODO text"); if (text) send("create_task", { text }); }
  if (target.matches("[data-action=create-table]")) { const name = await promptValue("Checklist name"); if (name) send("create_table", { name }); }
  if (target.matches("[data-view]")) { state.view = target.dataset.view; document.querySelectorAll("[data-view]").forEach(button => button.classList.toggle("active", button === target)); renderTables(); }
  if (target.matches("[data-task-delete]")) send("delete_task", { task_id: Number(target.dataset.taskDelete) });
  if (target.matches("[data-table-delete]")) send("delete_table", { table_id: Number(target.dataset.tableDelete) });
  if (target.matches("[data-row-delete]")) send("delete_row", { row_id: Number(target.dataset.rowDelete) });
  if (target.matches("[data-add-row]")) { const name = await promptValue("Row name"); if (name) send("create_row", { table_id: Number(target.dataset.addRow), name }); }
  if (target.matches("[data-add-column]")) { const name = await promptValue("Column name"); if (name) send("create_column", { table_id: Number(target.dataset.addColumn), name }); }
});

document.addEventListener("change", event => {
  const target = event.target;
  if (target.matches("[data-task-toggle]")) send("toggle_task", { task_id: Number(target.dataset.taskToggle), completed: target.checked });
  if (target.matches("[data-cell-row]")) send("toggle_cell", { row_id: Number(target.dataset.cellRow), column_id: Number(target.dataset.cellColumn), completed: target.checked });
});

document.addEventListener("keydown", event => {
  if (event.key !== "Enter") return;
  const target = event.target;
  if (target.matches("[data-task-text]")) send("update_task", { task_id: Number(target.dataset.taskText), text: target.value });
  if (target.matches("[data-table-name]")) send("rename_table", { table_id: Number(target.dataset.tableName), name: target.value });
  if (target.matches("[data-row-name]")) send("rename_row", { row_id: Number(target.dataset.rowName), name: target.value });
  if (target.matches("[data-column-name]")) send("rename_column", { column_id: Number(target.dataset.columnName), name: target.value });
});

document.addEventListener("pointerdown", event => {
  const handle = event.target.closest("[data-resize-column]");
  if (!handle) return;
  const startX = event.clientX;
  const key = `${handle.dataset.resizeTable}:${handle.dataset.resizeColumn}`;
  const startWidth = state.widths[key] || 120;
  const move = moveEvent => { state.widths[key] = Math.max(80, startWidth + moveEvent.clientX - startX); renderTables(); };
  const stop = () => { document.removeEventListener("pointermove", move); document.removeEventListener("pointerup", stop); };
  document.addEventListener("pointermove", move);
  document.addEventListener("pointerup", stop);
});
