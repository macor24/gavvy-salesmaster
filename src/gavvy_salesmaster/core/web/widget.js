/*!
 * gavvy · 销售宗师嵌入式获客插件
 * 在任何网页嵌入即可收集销售线索
 * 
 * 用法:
 *   <script src="https://你的域名/widget.js" data-api-url="https://你的域名" data-welcome="你好！有什么可以帮助您的？"></script>
 */

(function() {
  'use strict';

  var SCRIPT = document.currentScript || document.querySelector('script[src*="widget.js"]');
  var API_URL = SCRIPT?.getAttribute('data-api-url') || 'http://localhost:8877';
  var WELCOME_MSG = SCRIPT?.getAttribute('data-welcome') || '👋 您好！我是gavvy销售助手，请问怎么称呼您？有什么需求可以告诉我～';
  var SITE_NAME = SCRIPT?.getAttribute('data-site-name') || document.title || '在线咨询';

  // ── 状态 ──
  var state = {
    open: false,
    step: 'form',          // form → chatting
    visitorName: '',
    visitorContact: '',
    leadId: '',
    messages: [],
  };

  // ── 创建 DOM ──
  var container = document.createElement('div');
  container.id = 'tlsales-widget-container';
  container.innerHTML = `
    <style>
      #tlsales-widget-container * { box-sizing: border-box; }
      #tlsales-widget-container button { cursor: pointer; }
      .tlsales-btn {
        position: fixed; bottom: 24px; right: 24px; z-index: 2147483647;
        width: 56px; height: 56px; border-radius: 50%;
        background: #ddf7f2; border: none;
        box-shadow: 0 4px 16px rgba(0,0,0,0.2);
        font-size: 26px; display: flex; align-items: center; justify-content: center;
        transition: transform 0.2s, box-shadow 0.2s;
      }
      .tlsales-btn:hover { transform: scale(1.1); box-shadow: 0 6px 24px rgba(0,0,0,0.25); }
      .tlsales-panel {
        position: fixed; bottom: 92px; right: 24px; z-index: 2147483646;
        width: 360px; max-height: 520px;
        background: white; border-radius: 16px;
        box-shadow: 0 8px 40px rgba(0,0,0,0.18);
        display: none; flex-direction: column;
        overflow: hidden; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: 14px; color: #0f172a;
        animation: tlsalesSlideIn 0.3s ease;
      }
      @keyframes tlsalesSlideIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
      .tlsales-panel.open { display: flex; }
      .tlsales-header {
        background: #ddf7f2; padding: 14px 16px; display: flex;
        align-items: center; justify-content: space-between;
        font-weight: 600; font-size: 15px; color: #0f172a;
      }
      .tlsales-close { background: none; border: none; font-size: 20px; color: #64748b; padding: 0 4px; }
      .tlsales-close:hover { color: #0f172a; }
      .tlsales-body { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 10px; min-height: 200px; }
      .tlsales-msg { max-width: 85%; padding: 8px 12px; border-radius: 12px; line-height: 1.5; font-size: 13px; }
      .tlsales-msg.bot { align-self: flex-start; background: #f1f5f9; color: #0f172a; border-bottom-left-radius: 4px; }
      .tlsales-msg.user { align-self: flex-end; background: #ddf7f2; color: #0f172a; border-bottom-right-radius: 4px; }
      .tlsales-form { padding: 16px; display: flex; flex-direction: column; gap: 10px; }
      .tlsales-form input {
        width: 100%; padding: 10px 12px; border: 1px solid #e2e8f0; border-radius: 8px;
        font-size: 13px; outline: none; transition: border-color 0.2s;
      }
      .tlsales-form input:focus { border-color: #ddf7f2; box-shadow: 0 0 0 3px rgba(221,247,242,0.3); }
      .tlsales-form .tlsales-submit {
        padding: 10px; border: none; border-radius: 8px; background: #2563eb; color: white;
        font-size: 14px; font-weight: 500; transition: opacity 0.2s;
      }
      .tlsales-form .tlsales-submit:hover { opacity: 0.9; }
      .tlsales-form .tlsales-submit:disabled { opacity: 0.5; cursor: not-allowed; }
      .tlsales-input-row { display: flex; gap: 6px; padding: 10px 12px; border-top: 1px solid #e2e8f0; }
      .tlsales-input-row input { flex:1; border: none; padding: 6px 0; font-size: 13px; outline: none; }
      .tlsales-input-row button { border: none; background: #2563eb; color: white; border-radius: 8px; padding: 6px 14px; font-size: 13px; }
    </style>
    <button class="tlsales-btn" id="tlsales-btn">💬</button>
    <div class="tlsales-panel" id="tlsales-panel">
      <div class="tlsales-header">
        <span>🪸 gavvy · 销售助手</span>
        <button class="tlsales-close" id="tlsales-close">✕</button>
      </div>
      <div class="tlsales-body" id="tlsales-body">
        <div class="tlsales-msg bot">${WELCOME_MSG}</div>
      </div>
      <div class="tlsales-form" id="tlsales-form">
        <input type="text" id="tlsales-name" placeholder="您的姓名" autocomplete="name">
        <input type="text" id="tlsales-contact" placeholder="手机号 / 微信号 / 邮箱">
        <button class="tlsales-submit" id="tlsales-submit">开始咨询 →</button>
      </div>
      <div class="tlsales-input-row" id="tlsales-input-row" style="display:none;">
        <input type="text" id="tlsales-msg-input" placeholder="输入消息...">
        <button id="tlsales-send">发送</button>
      </div>
    </div>
  `;

  document.body.appendChild(container);

  // ── DOM 元素引用 ──
  var btn = document.getElementById('tlsales-btn');
  var panel = document.getElementById('tlsales-panel');
  var closeBtn = document.getElementById('tlsales-close');
  var body = document.getElementById('tlsales-body');
  var form = document.getElementById('tlsales-form');
  var nameInput = document.getElementById('tlsales-name');
  var contactInput = document.getElementById('tlsales-contact');
  var submitBtn = document.getElementById('tlsales-submit');
  var inputRow = document.getElementById('tlsales-input-row');
  var msgInput = document.getElementById('tlsales-msg-input');
  var sendBtn = document.getElementById('tlsales-send');

  // ── 工具 ──
  function escHtml(str) {
    var d = document.createElement('div');
    d.appendChild(document.createTextNode(str || ''));
    return d.innerHTML;
  }

  function addMsg(text, role) {
    var div = document.createElement('div');
    div.className = 'tlsales-msg ' + (role === 'user' ? 'user' : 'bot');
    div.textContent = text;
    body.appendChild(div);
    body.scrollTop = body.scrollHeight;
  }

  function now() {
    return new Date().toLocaleTimeString('zh-CN', {hour:'2-digit',minute:'2-digit'});
  }

  // ── 打开/关闭 ──
  function openPanel() {
    panel.classList.add('open');
    btn.style.display = 'none';
    state.open = true;
    if (state.step === 'form') {
      nameInput.focus();
    } else {
      msgInput.focus();
    }
  }

  function closePanel() {
    panel.classList.remove('open');
    btn.style.display = 'flex';
    state.open = false;
  }

  // ── 提交表单 → 创建 Lead ──
  function submitForm() {
    var name = nameInput.value.trim();
    var contact = contactInput.value.trim();
    if (!name) { nameInput.focus(); nameInput.style.borderColor = '#ef4444'; return; }
    if (!contact) { contactInput.focus(); contactInput.style.borderColor = '#ef4444'; return; }

    nameInput.style.borderColor = '#e2e8f0';
    contactInput.style.borderColor = '#e2e8f0';
    submitBtn.disabled = true;
    submitBtn.textContent = '正在接入...';

    state.visitorName = name;
    state.visitorContact = contact;
    addMsg('我是 ' + name + '，联系方式：' + contact, 'user');

    // 调 API 创建客户/Lead
    var customerId = 'widget_' + Date.now();
    fetch(API_URL + '/api/leads/from_widget', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        name: name,
        contact: contact,
        source: 'widget',
        site: SITE_NAME,
        customer_id: customerId,
      })
    }).then(function(r) { return r.json(); }).then(function(data) {
      state.leadId = data.lead_id || customerId;
      // 发送欢迎后的AI回复
      return fetch(API_URL + '/api/chat/send', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          message: '您好，我是' + name + '，' + contact + '，想咨询产品信息',
          channel: 'widget',
          customer: name,
        })
      });
    }).then(function(r) { return r.json(); }).then(function(data) {
      var reply = data.reply || '您好' + name + '！欢迎咨询，我们马上为您服务～';
      addMsg(reply, 'bot');
      // 将AI回复保存到该客户的消息记录
      fetch(API_URL + '/api/customers/' + customerId + '/messages', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({role:'agent', sender:'销售助手', text:reply, time:now()})
      }).catch(function(){});
    }).catch(function() {
      addMsg('您好' + name + '！欢迎咨询，我们马上为您服务～', 'bot');
    }).finally(function() {
      state.step = 'chatting';
      form.style.display = 'none';
      inputRow.style.display = 'flex';
      msgInput.focus();
    });
  }

  // ── 发送聊天消息 ──
  function sendMsg() {
    var text = msgInput.value.trim();
    if (!text) return;
    msgInput.value = '';
    addMsg(text, 'user');
    msgInput.focus();

    // 保存用户消息
    if (state.leadId) {
      fetch(API_URL + '/api/customers/' + state.leadId + '/messages', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({role:'customer', text:text, time:now()})
      }).catch(function(){});
    }

    // 调AI回复
    fetch(API_URL + '/api/chat/send', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: text, channel: 'widget', customer: state.visitorName})
    }).then(function(r) { return r.json(); }).then(function(data) {
      var reply = data.reply || data.text || '好的，我记下了。';
      addMsg(reply, 'bot');
      if (state.leadId) {
        fetch(API_URL + '/api/customers/' + state.leadId + '/messages', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({role:'agent', sender:'销售助手', text:reply, time:now()})
        }).catch(function(){});
      }
    }).catch(function() {
      addMsg('好的，感谢您的反馈！我们会尽快跟进。', 'bot');
    });
  }

  // ── 事件绑定 ──
  btn.addEventListener('click', openPanel);
  closeBtn.addEventListener('click', closePanel);
  submitBtn.addEventListener('click', submitForm);
  sendBtn.addEventListener('click', sendMsg);

  nameInput.addEventListener('keydown', function(e) { if (e.key === 'Enter') contactInput.focus(); });
  contactInput.addEventListener('keydown', function(e) { if (e.key === 'Enter') submitForm(); });
  msgInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMsg(); }
  });
})();
