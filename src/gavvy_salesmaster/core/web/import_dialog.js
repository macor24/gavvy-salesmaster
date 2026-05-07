
// ── 批量导入对话框 ────────────────────────────
window.showImportDialog = function() {
  var old = document.getElementById('import-dialog-overlay');
  if (old) old.remove();

  var overlay = document.createElement('div');
  overlay.id = 'import-dialog-overlay';
  overlay.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(0,0,0,0.5);z-index:99999;display:flex;align-items:center;justify-content:center;';

  overlay.innerHTML = '<div style="background:#fff;border-radius:16px;padding:24px;max-width:560px;width:90%;max-height:80vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,0.3);">' +
    '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">' +
      '<h3 style="margin:0;font-size:18px;">📋 批量导入客户</h3>' +
      '<button id="import-close" style="background:none;border:none;font-size:22px;cursor:pointer;color:#94a3b8;">✕</button>' +
    '</div>' +
    '<p style="font-size:13px;color:#64748b;margin-bottom:12px;">每行一条，格式：<code>姓名,联系方式,意向</code></p>' +
    '<textarea id="import-textarea" style="width:100%;height:200px;padding:10px;border:1px solid #e2e8f0;border-radius:8px;font-size:13px;font-family:monospace;outline:none;resize:vertical;" placeholder="张先生,13800138000,高意向&#10;李女士,13900139000,跟进中"></textarea>' +
    '<div style="display:flex;gap:8px;margin-top:12px;">' +
      '<button id="import-btn-parsedemo" style="flex:1;padding:8px;border:1px solid #e2e8f0;border-radius:8px;background:white;font-size:13px;cursor:pointer;">📄 演示数据</button>' +
      '<button id="import-btn-submit" style="flex:2;padding:8px;border:none;border-radius:8px;background:#2563eb;color:white;font-size:13px;font-weight:500;cursor:pointer;">🚀 导入</button>' +
    '</div>' +
    '<div id="import-result" style="margin-top:12px;font-size:13px;color:#475569;"></div>' +
  '</div>';

  document.body.appendChild(overlay);
  document.getElementById('import-close').onclick = function() { overlay.remove(); };
  overlay.onclick = function(e) { if (e.target === this) overlay.remove(); };

  document.getElementById('import-btn-parsedemo').onclick = function() {
    document.getElementById('import-textarea').value =
      '张总,13912345678,高意向\n李经理,13898765432,跟进中\n王老板,13711112222,新客户\n陈总,13633334444,高意向\n刘先生,13555556666,跟进中';
  };

  document.getElementById('import-btn-submit').onclick = function() {
    var text = document.getElementById('import-textarea').value.trim();
    if (!text) { document.getElementById('import-result').textContent = '⚠️ 请填写客户数据'; return; }
    var lines = text.split('\n').filter(Boolean);
    var leads = lines.map(function(line) {
      var parts = line.split(',').map(function(s) { return s.trim(); });
      return {name: parts[0] || '', contact: parts[1] || '', intent: parts[2] || '新客户'};
    }).filter(function(l) { return l.name; });
    if (leads.length === 0) { document.getElementById('import-result').textContent = '⚠️ 无效数据'; return; }

    var btn = this;
    btn.textContent = '⏳ 导入中 (' + leads.length + '条)...';
    btn.disabled = true;

    fetch('/api/leads/import_csv', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({leads: leads})
    }).then(function(r){return r.json()}).then(function(data) {
      document.getElementById('import-result').innerHTML = '✅ 成功导入 <strong>' + data.imported + '</strong> 位客户';
      btn.textContent = '🚀 导入';
      btn.disabled = false;
      setTimeout(function() { overlay.remove(); loadSummary(); loadCustomerList(); loadPipelineStages(); }, 1200);
    }).catch(function() {
      document.getElementById('import-result').textContent = '❌ 导入失败';
      btn.textContent = '🚀 导入';
      btn.disabled = false;
    });
  };
};
