const WIDTHS_STORAGE_KEY = "nemo-todo-column-widths";
const DEFAULT_ITEM_WIDTH = 140;
const DEFAULT_CHECKBOX_WIDTH = 60;
const DEFAULT_TEXT_WIDTH = 130;
const GEAR_ICON = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>';

function loadWidths() {
  try {
    return JSON.parse(window.localStorage.getItem(WIDTHS_STORAGE_KEY) || "{}");
  } catch (error) {
    return {};
  }
}

function saveWidths() {
  try {
    window.localStorage.setItem(WIDTHS_STORAGE_KEY, JSON.stringify(state.widths));
  } catch (error) { /* ignore persistence failures (e.g. storage disabled) */ }
}

function defaultWidth(column) {
  return column.type === "text" ? DEFAULT_TEXT_WIDTH : DEFAULT_CHECKBOX_WIDTH;
}

function resolveDefaultWidth(tableId, columnId) {
  if (columnId === "__item") return DEFAULT_ITEM_WIDTH;
  const table = (state.data.tables || []).find(item => item.id === tableId);
  const column = table && table.columns.find(item => item.id === Number(columnId));
  return column ? defaultWidth(column) : DEFAULT_CHECKBOX_WIDTH;
}

const state = { data: { tasks: [], tables: [] }, view: "table", widths: loadWidths(), columnSettingsTableId: null };

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
  renderColumnSettings();
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
  const itemWidth = state.widths[`${table.id}:__item`] || DEFAULT_ITEM_WIDTH;
  const widths = [itemWidth, ...columns.map(column => state.widths[`${table.id}:${column.id}`] || defaultWidth(column))];
  const gridStyle = `grid-template-columns:${widths.map(width => `${width}px`).join(" ")}`;
  return `<article class="table-card">
    <div class="table-top"><input class="table-title" data-table-name="${table.id}" value="${escapeHtml(table.name)}"><span class="table-summary">${completed}/${total} completed</span><button class="icon-button" data-table-delete="${table.id}" title="Delete checklist">&#215;</button></div>
    <div class="table-scroll"><div class="grid" style="${gridStyle}">
      <div class="grid-cell grid-header item-header"><span>Item</span><button class="icon-button gear-button" data-columns-settings="${table.id}" title="Manage columns">${GEAR_ICON}</button><span class="resize-handle" data-resize-table="${table.id}" data-resize-column="__item"></span></div>${columns.map(column => `<div class="grid-cell grid-header"><input class="column-name" data-column-name="${column.id}" value="${escapeHtml(column.name)}"><span class="resize-handle" data-resize-table="${table.id}" data-resize-column="${column.id}"></span></div>`).join("")}
      ${rows.map(row => `<div class="grid-cell grid-row-name"><input class="row-name" data-row-name="${row.id}" value="${escapeHtml(row.name)}"><button class="icon-button" data-row-delete="${row.id}" title="Delete row">&#215;</button></div>${columns.map(column => `<div class="grid-cell">${renderCellInput(table, row, column)}</div>`).join("")}`).join("")}
    </div></div>
    <div class="table-actions"><button data-add-row="${table.id}">+ Row</button><button data-add-column="${table.id}">+ Column</button></div>
  </article>`;
}

function renderCellInput(table, row, column) {
  const label = `${escapeHtml(row.name)} / ${escapeHtml(column.name)}`;
  if (column.type === "text") {
    return `<input type="text" class="cell-text" data-cell-text-row="${row.id}" data-cell-text-column="${column.id}" value="${escapeHtml(cellText(table, row.id, column.id))}" aria-label="${label}">`;
  }
  return `<input type="checkbox" data-cell-row="${row.id}" data-cell-column="${column.id}" ${cellValue(table, row.id, column.id) ? "checked" : ""} aria-label="${label}">`;
}

function renderCards(table) {
  const columns = table.columns || [];
  const completed = table.cells.filter(cell => cell.completed).length;
  const total = table.rows.length * columns.length;
  return `<article class="table-card"><div class="table-top"><input class="table-title" data-table-name="${table.id}" value="${escapeHtml(table.name)}"><span class="table-summary">${completed}/${total} completed</span><button class="icon-button gear-button" data-columns-settings="${table.id}" title="Manage columns">${GEAR_ICON}</button><button class="icon-button" data-table-delete="${table.id}" title="Delete checklist">&#215;</button></div>${table.rows.map(row => `<div class="card-row"><div class="card-check"><input class="row-name" data-row-name="${row.id}" value="${escapeHtml(row.name)}"><button class="icon-button" data-row-delete="${row.id}" title="Delete row">&#215;</button></div>${columns.map(column => `<label class="card-check"><span>${escapeHtml(column.name)}</span>${renderCellInput(table, row, column)}</label>`).join("")}</div>`).join("")}<div class="table-actions"><button data-add-row="${table.id}">+ Row</button><button data-add-column="${table.id}">+ Column</button></div></article>`;
}

function cellValue(table, rowId, columnId) {
  return table.cells.some(cell => cell.row_id === rowId && cell.column_id === columnId && cell.completed);
}

function cellText(table, rowId, columnId) {
  const cell = table.cells.find(cell => cell.row_id === rowId && cell.column_id === columnId);
  return (cell && cell.text_value) || "";
}

function openColumnSettings(tableId) {
  state.columnSettingsTableId = tableId;
  renderColumnSettings();
}

function closeColumnSettings() {
  state.columnSettingsTableId = null;
  renderColumnSettings();
}

function renderColumnSettings() {
  const overlay = document.querySelector("#column-modal");
  const table = (state.data.tables || []).find(item => item.id === state.columnSettingsTableId);
  if (!table) {
    overlay.hidden = true;
    overlay.innerHTML = "";
    return;
  }
  const columns = table.columns || [];
  overlay.hidden = false;
  overlay.innerHTML = `<div class="modal">
    <div class="modal-header"><h3>Manage columns</h3><button class="icon-button" data-modal-close title="Close">&#215;</button></div>
    <div class="modal-body">${columns.length ? columns.map(column => `
      <div class="modal-row">
        <span class="modal-column-name">${escapeHtml(column.name)}</span>
        <select data-column-type="${column.id}">
          <option value="checkbox" ${column.type === "checkbox" ? "selected" : ""}>Checkbox</option>
          <option value="text" ${column.type === "text" ? "selected" : ""}>Text</option>
        </select>
        <button class="icon-button" data-column-delete="${column.id}" title="Delete column">&#215;</button>
      </div>`).join("") : '<div class="empty">No columns yet.</div>'}
    </div>
  </div>`;
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
  if (target.matches("[data-columns-settings]")) openColumnSettings(Number(target.dataset.columnsSettings));
  if (target.matches("[data-modal-close]") || target.matches("#column-modal")) closeColumnSettings();
  if (target.matches("[data-column-delete]")) send("delete_column", { column_id: Number(target.dataset.columnDelete) });
});

document.addEventListener("change", event => {
  const target = event.target;
  if (target.matches("[data-task-toggle]")) send("toggle_task", { task_id: Number(target.dataset.taskToggle), completed: target.checked });
  if (target.matches("[data-cell-row]")) send("toggle_cell", { row_id: Number(target.dataset.cellRow), column_id: Number(target.dataset.cellColumn), completed: target.checked });
  if (target.matches("[data-cell-text-row]")) send("set_cell_text", { row_id: Number(target.dataset.cellTextRow), column_id: Number(target.dataset.cellTextColumn), text: target.value });
  if (target.matches("[data-column-type]")) send("update_column_type", { column_id: Number(target.dataset.columnType), type: target.value });
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
  const tableId = Number(handle.dataset.resizeTable);
  const columnId = handle.dataset.resizeColumn;
  const key = `${tableId}:${columnId}`;
  const startWidth = state.widths[key] || resolveDefaultWidth(tableId, columnId);
  const minWidth = columnId === "__item" ? 90 : 40;
  const move = moveEvent => { state.widths[key] = Math.max(minWidth, startWidth + moveEvent.clientX - startX); renderTables(); };
  const stop = () => {
    saveWidths();
    document.removeEventListener("pointermove", move);
    document.removeEventListener("pointerup", stop);
  };
  document.addEventListener("pointermove", move);
  document.addEventListener("pointerup", stop);
});
