/**
 * api_client.js — 销售宗师统一API客户端
 *
 * 封装所有后端API调用，提供：
 * - 统一错误处理
 * - mock降级（后端不可用时自动回退到模拟数据）
 * - 请求超时控制
 * - 请求/响应日志
 *
 * 所有前端视图通过此模块获取数据，不再直接调用 fetch。
 */

const SalesAPI = (function() {

  // ── 配置 ───────────────────────────────────
  const BASE = '';  // 同源，前端服务已代理 API
  const TIMEOUT_MS = 10000;

  // ── Mock 数据（降级用） ────────────────────

  const _mockSummary = {
    total_leads: 12,
    agent_count: 7,
    history_count: 86,
    stage_counts: { discovery: 3, research: 4, contact: 2, negotiation: 2, after_sales: 1 },
    safety_mode: { mode: 'open', mode_label: '开放模式', price_ceiling: 50000 }
  };

  const _mockAgents = {
    agents: {
      market_research_agent: { role_en: 'market_research_agent', role_cn: '市场调研官', description: '负责市场趋势分析、潜在客户挖掘与行业洞察' },
      competitor_intel_agent: { role_en: 'competitor_intel_agent', role_cn: '竞品分析官', description: '负责竞品追踪、差异化策略与市场定位' },
      presales_agent: { role_en: 'presales_agent', role_cn: '售前谈判官', description: '负责客户沟通、价值传递与谈判推进' },
      aftersales_agent: { role_en: 'aftersales_agent', role_cn: '售后维系官', description: '负责售后服务、客户复购与口碑传播' },
      procurement_agent: { role_en: 'procurement_agent', role_cn: '采购供应链官', description: '负责成本分析、供应商匹配与利润核算' },
      operations_agent: { role_en: 'operations_agent', role_cn: '运营增长官', description: '负责客户分层、话术迭代与渠道优化' },
      platform_ops_agent: { role_en: 'platform_ops_agent', role_cn: '运营助理', description: '负责商品上架审核、平台规则检测与违禁词过滤' }
    }
  };

  const _mockLeads = {
    count: 12,
    leads: [
      { id: 'lead_1', info: { name: '张先生', company: '星辰科技', stage: 'contact' }, score: 82, stage: 'contact' },
      { id: 'lead_2', info: { name: '李女士', company: '明达集团', stage: 'research' }, score: 68, stage: 'research' },
      { id: 'lead_3', info: { name: '王先生', company: '鼎盛实业', stage: 'closing' }, score: 91, stage: 'closing' },
    ]
  };

  const _mockSafety = {
    mode: 'open',
    mode_label: '开放模式',
    price_ceiling: 50000,
    daily_deal_limit: 20,
    auto_approve_below: 10000,
    sensitive_keywords: ['免费', '承诺', '保证'],
    logs: ['[10:00] 安全模式已启动: open', '[09:30] 自动审批 ¥8,500 交易']
  };

  const _mockChatReply = {
    reply: '好的，我理解您的需求。让我为您详细介绍一下相关方案。',
    agent: '售前谈判官',
    action: '人工回复',
    summary: '预设回复'
  };

  const _mockMemoryStats = {
    episodes: 8, insights: 15, skills: 6,
    patterns: 12, rules: 24, evolution_events: 3
  };

  // ── 缓存 ──────────────────────────────────

  let _cache = {};
  let _inflight = {};  // 去重：同一 key 并发只发一次

  function _cacheGet(key, ttlMs) {
    const entry = _cache[key];
    if (entry && (Date.now() - entry.ts) < ttlMs) return entry.data;
    return null;
  }

  function _cacheSet(key, data) {
    _cache[key] = { data, ts: Date.now() };
    // 限制缓存大小，删除最旧条目
    const keys = Object.keys(_cache);
    if (keys.length > 50) {
      let oldest = keys[0], oldestTs = _cache[keys[0]].ts;
      for (let i = 1; i < keys.length; i++) {
        if (_cache[keys[i]].ts < oldestTs) { oldest = keys[i]; oldestTs = _cache[keys[i]].ts; }
      }
      delete _cache[oldest];
    }
  }

  // ── 网络请求 ──────────────────────────────

  function _fetch(url, options) {
    const cacheKey = options?.method === 'POST' ? null : url;
    if (cacheKey) {
      const cached = _cacheGet(cacheKey, 15000);
      if (cached) return Promise.resolve(cached);
      // 去重：同一 URL 同时发起的请求只发一次
      if (_inflight[cacheKey]) return _inflight[cacheKey].then(data => JSON.parse(JSON.stringify(data)));
    }

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
    const promise = fetch(BASE + url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers || {})
      }
    })
    .then(r => {
      clearTimeout(timer);
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    })
    .catch(err => {
      clearTimeout(timer);
      throw err;
    });

    if (cacheKey) {
      _inflight[cacheKey] = promise;
      return promise.then(data => {
        _cacheSet(cacheKey, data);
        delete _inflight[cacheKey];
        return JSON.parse(JSON.stringify(data));
      }).catch(err => {
        delete _inflight[cacheKey];
        throw err;
      });
    }
    return promise;
  }

  function _fetchWithFallback(url, options, fallback) {
    return _fetch(url, options)
      .catch(() => fallback);
  }

  // ── 公共 API ──────────────────────────────

  return {

    // ========== 编排器 ==========

    /** 获取编排器摘要（仪表盘） */
    getSummary() {
      const cached = _cacheGet('summary', 15000);
      if (cached) return Promise.resolve(cached);

      return _fetchWithFallback('/api/orchestrator/summary', {}, _mockSummary)
        .then(data => {
          if (data !== _mockSummary) _cacheSet('summary', data);
          return data;
        });
    },

    /** 获取Agent列表 */
    getAgents() {
      const cached = _cacheGet('agents', 30000);
      if (cached) return Promise.resolve(cached);

      return _fetchWithFallback('/api/orchestrator/agents', {}, _mockAgents)
        .then(data => {
          if (data !== _mockAgents) _cacheSet('agents', data);
          return data;
        });
    },

    /** 获取Leads列表（客户中心） */
    getLeads() {
      return _fetchWithFallback('/api/orchestrator/leads', {}, _mockLeads);
    },

    /** 获取单个Lead详情 */
    getLead(leadId) {
      return _fetchWithFallback('/api/orchestrator/lead?id=' + encodeURIComponent(leadId), {}, null)
        .then(data => data || { id: leadId, info: { name: '未知客户' } });
    },

    /** 添加Lead */
    addLead(leadData) {
      return _fetchWithFallback('/api/leads', {
        method: 'POST',
        body: JSON.stringify(leadData)
      }, { id: 'local_' + Date.now(), info: leadData.info || {} });
    },

    /** 自动调度Agent处理Lead */
    dispatchLead(leadId) {
      return _fetchWithFallback('/api/leads/dispatch', {
        method: 'POST',
        body: JSON.stringify({ lead_id: leadId })
      }, {
        result: {
          status: 'success',
          action: '预设回复',
          summary: '客户咨询已收到，正在分析最佳方案。',
          output_text: '好的，我理解您的需求。让我为您详细介绍一下相关方案。',
          agent_cn: '售前谈判官'
        }
      });
    },

    /** 获取Lead评分 */
    getLeadScore(leadId) {
      return _fetchWithFallback('/api/orchestrator/lead/score?id=' + encodeURIComponent(leadId), {}, {
        total_score: 75,
        dimensions: [
          { name: '需求匹配', score: 80, weight: 35 },
          { name: '资金实力', score: 70, weight: 20 },
          { name: '决策链', score: 65, weight: 15 },
          { name: '紧迫性', score: 75, weight: 10 },
          { name: '竞品威胁', score: 60, weight: 10 },
          { name: '关系深度', score: 50, weight: 10 }
        ]
      });
    },

    /** 获取所有Leads评分 */
    getAllScores() {
      return _fetchWithFallback('/api/orchestrator/scores', {}, { scores: [] });
    },

    /** 获取Lead洞察 */
    getLeadInsight(leadId) {
      return _fetchWithFallback('/api/orchestrator/lead/insight?id=' + encodeURIComponent(leadId), {}, {
        insights: [
          { type: 'win', priority: 'high', content: '客户需求匹配度高' }
        ]
      });
    },

    // ========== 聊天 ==========

    /** 发送聊天消息 */
    sendMessage(message, customer, product) {
      return _fetchWithFallback('/api/chat/send', {
        method: 'POST',
        body: JSON.stringify({
          message: message,
          customer: customer || '在线客户',
          product: product || '通用咨询'
        })
      }, {
        reply: _mockChatReply.reply,
        agent: _mockChatReply.agent,
        action: _mockChatReply.action,
        summary: _mockChatReply.summary
      });
    },

    // ========== 安全模式 ==========

    /** 获取安全模式状态 */
    getSafetyStatus() {
      return _fetchWithFallback('/api/safety/status', {}, _mockSafety);
    },

    /** 设置安全模式 */
    setSafetyMode(mode) {
      return _fetchWithFallback('/api/safety/mode', {
        method: 'POST',
        body: JSON.stringify({ mode: mode })
      }, { status: 'ok', mode: mode });
    },

    // ========== 设置 ==========

    /** 获取API配置 */
    getSettings() {
      return _fetchWithFallback('/api/settings', {}, { api_keys: {}, platforms: {}, config: {} });
    },

    /** 保存API配置 */
    saveSettings(data) {
      return _fetchWithFallback('/api/settings', {
        method: 'POST',
        body: JSON.stringify(data)
      }, { status: 'ok', saved: true });
    },

    // ========== CRM 系统集成 ==========

    /** CRM 概览 */
    crmOverview() {
      return _fetchWithFallback('/api/crm/overview', {}, { customers: { total: 0, stages: {} }, deals: { total: 0 }, contracts: { total: 0 } });
    },

    /** CRM 客户列表 */
    crmCustomers(stage, search) {
      let url = '/api/crm/customers';
      const params = [];
      if (stage) params.push('stage=' + encodeURIComponent(stage));
      if (search) params.push('search=' + encodeURIComponent(search));
      if (params.length) url += '?' + params.join('&');
      return _fetchWithFallback(url, {}, { customers: [] });
    },

    /** CRM 客户详情（含联系人/商机/合同/活动） */
    crmCustomerDetail(id) {
      return _fetchWithFallback('/api/crm/customers/' + encodeURIComponent(id), {}, { customer: null, contacts: [], deals: [], contracts: [], activities: [] });
    },

    /** CRM 创建客户 */
    crmCreateCustomer(data) {
      return _fetchWithFallback('/api/crm/customers', { method: 'POST', body: JSON.stringify(data) }, { id: 'new', name: data.name });
    },

    /** CRM 更新客户 */
    crmUpdateCustomer(id, data) {
      return _fetchWithFallback('/api/crm/customers/' + encodeURIComponent(id), { method: 'PUT', body: JSON.stringify(data) }, { id: id });
    },

    /** CRM 删除客户 */
    crmDeleteCustomer(id) {
      return _fetchWithFallback('/api/crm/customers/' + encodeURIComponent(id), { method: 'DELETE' }, { status: 'ok' });
    },

    /** CRM 创建联系人 */
    crmCreateContact(data) {
      return _fetchWithFallback('/api/crm/contacts', { method: 'POST', body: JSON.stringify(data) }, { id: 'new' });
    },

    /** CRM 删除联系人 */
    crmDeleteContact(id) {
      return _fetchWithFallback('/api/crm/contacts/' + encodeURIComponent(id), { method: 'DELETE' }, { status: 'ok' });
    },

    /** CRM 商机列表 */
    crmDeals(customerId) {
      let url = '/api/crm/deals';
      if (customerId) url += '?customer_id=' + encodeURIComponent(customerId);
      return _fetchWithFallback(url, {}, { deals: [] });
    },

    /** CRM 创建商机 */
    crmCreateDeal(data) {
      return _fetchWithFallback('/api/crm/deals', { method: 'POST', body: JSON.stringify(data) }, { id: 'new' });
    },

    /** CRM 更新商机 */
    crmUpdateDeal(id, data) {
      return _fetchWithFallback('/api/crm/deals/' + encodeURIComponent(id), { method: 'PUT', body: JSON.stringify(data) }, { id: id });
    },

    /** CRM 合同列表 */
    crmContracts(customerId) {
      let url = '/api/crm/contracts';
      if (customerId) url += '?customer_id=' + encodeURIComponent(customerId);
      return _fetchWithFallback(url, {}, { contracts: [] });
    },

    /** CRM 创建合同 */
    crmCreateContract(data) {
      return _fetchWithFallback('/api/crm/contracts', { method: 'POST', body: JSON.stringify(data) }, { id: 'new' });
    },

    /** CRM 更新合同 */
    crmUpdateContract(id, data) {
      return _fetchWithFallback('/api/crm/contracts/' + encodeURIComponent(id), { method: 'PUT', body: JSON.stringify(data) }, { id: id });
    },

    /** CRM 活动记录 */
    crmActivities(customerId, limit) {
      let url = '/api/crm/activities';
      const params = [];
      if (customerId) params.push('customer_id=' + encodeURIComponent(customerId));
      if (limit) params.push('limit=' + limit);
      if (params.length) url += '?' + params.join('&');
      return _fetchWithFallback(url, {}, { activities: [] });
    },

    /** CRM 创建活动 */
    crmCreateActivity(data) {
      return _fetchWithFallback('/api/crm/activities', { method: 'POST', body: JSON.stringify(data) }, { id: 'new' });
    },

    // ========== 话术训练系统 ==========

    /** 获取话术场景 */
    getScriptScenarios() {
      return _fetchWithFallback('/api/scripts/scenarios', {}, { scenarios: [] });
    },

    /** 获取话术列表 */
    getScripts(scenario, search) {
      let url = '/api/scripts';
      const params = [];
      if (scenario) params.push('scenario=' + encodeURIComponent(scenario));
      if (search) params.push('search=' + encodeURIComponent(search));
      if (params.length) url += '?' + params.join('&');
      return _fetchWithFallback(url, {}, { scripts: [] });
    },

    /** 获取话术详情 */
    getScript(id) {
      return _fetchWithFallback('/api/scripts/' + encodeURIComponent(id), {}, { id: '', title: '', content: '' });
    },

    /** 创建话术 */
    createScript(data) {
      return _fetchWithFallback('/api/scripts', { method: 'POST', body: JSON.stringify(data) }, { id: 'new' });
    },

    /** 更新话术 */
    updateScript(id, data) {
      return _fetchWithFallback('/api/scripts/' + encodeURIComponent(id), { method: 'PUT', body: JSON.stringify(data) }, { id: id });
    },

    /** 删除话术 */
    deleteScript(id) {
      return _fetchWithFallback('/api/scripts/' + encodeURIComponent(id), { method: 'DELETE' }, { status: 'ok' });
    },

    /** 评分话术 */
    rateScript(id, score, comment) {
      return _fetchWithFallback('/api/scripts/' + encodeURIComponent(id) + '/rate', { method: 'POST', body: JSON.stringify({ score: score, comment: comment || '' }) }, { id: id });
    },

    /** 获取话术推荐 */
    getScriptRecommend(scenario, tags) {
      let url = '/api/scripts/recommend';
      const params = [];
      if (scenario) params.push('scenario=' + encodeURIComponent(scenario));
      if (tags) params.push('tags=' + encodeURIComponent(tags));
      if (params.length) url += '?' + params.join('&');
      return _fetchWithFallback(url, {}, { scripts: [] });
    },

    /** 开始训练会话 */
    startTraining(scenario, scriptId) {
      return _fetchWithFallback('/api/scripts/training/start', { method: 'POST', body: JSON.stringify({ scenario: scenario, script_id: scriptId || '' }) }, { id: 'new' });
    },

    /** 训练步骤 */
    trainingStep(sessionId, message) {
      return _fetchWithFallback('/api/scripts/training/' + encodeURIComponent(sessionId) + '/step', { method: 'POST', body: JSON.stringify({ message: message }) }, { feedback: '' });
    },

    /** 完成训练 */
    completeTraining(sessionId, score, feedback) {
      return _fetchWithFallback('/api/scripts/training/' + encodeURIComponent(sessionId) + '/complete', { method: 'POST', body: JSON.stringify({ score: score, feedback: feedback || '' }) }, { state: 'completed' });
    },

    /** 训练会话历史 */
    getTrainingSessions(scenario) {
      let url = '/api/scripts/training/sessions';
      if (scenario) url += '?scenario=' + encodeURIComponent(scenario);
      return _fetchWithFallback(url, {}, { sessions: [] });
    },

    /** 话术统计 */
    getScriptStats() {
      return _fetchWithFallback('/api/scripts/stats', {}, { total_scripts: 0, total_sessions: 0 });
    },

    // ========== 多渠道消息发送 ==========

    /** 列出已注册渠道 */
    getChannels() {
      return _fetchWithFallback('/api/channels', {}, { channels: {}, count: 0 });
    },

    /** 获取渠道发送统计 */
    getChannelStats() {
      return _fetchWithFallback('/api/channels/stats', {}, { total: 0, sent: 0, failed: 0, registered_channels: [], by_channel: {} });
    },

    /** 获取发送历史 */
    getChannelHistory(limit) {
      return _fetchWithFallback('/api/channels/history?limit=' + (limit || 50), {}, { history: [] });
    },

    /** 发送消息到指定渠道 */
    sendChannelMessage(channel, to, body, subject) {
      return _fetchWithFallback('/api/channels/send', {
        method: 'POST',
        body: JSON.stringify({ channel: channel, to: to || '', body: body, subject: subject || '' })
      }, { channel: channel, status: 'sent' });
    },

    /** 分发消息到多个渠道 */
    dispatchMessage(data) {
      return _fetchWithFallback('/api/channels/dispatch', {
        method: 'POST',
        body: JSON.stringify(data)
      }, { results: [], total: 0, sent: 0, failed: 0 });
    },

    /** 配置渠道 */
    configureChannel(name, config) {
      return _fetchWithFallback('/api/channels/config', {
        method: 'POST',
        body: JSON.stringify({ name: name, config: config })
      }, { status: 'ok', name: name, configured: false });
    },

    /** 删除渠道配置 */
    deleteChannel(name) {
      return _fetchWithFallback('/api/channels/config', {
        method: 'DELETE',
        body: JSON.stringify({ name: name })
      }, { status: 'ok', name: name });
    },

    // ========== 天龙1号集成 ==========

    /** 获取天龙1号状态 */
    getTianlongStatus() {
      return _fetchWithFallback('/api/tianlong/status', {}, { available: false, enabled: false, active: false });
    },

    /** 切换天龙1号集成 */
    toggleTianlong(enabled) {
      return _fetchWithFallback('/api/tianlong/toggle', {
        method: 'POST',
        body: JSON.stringify({ enabled: enabled })
      }, { enabled: enabled });
    },

    // ========== 学习记忆库 ==========

    /** 获取记忆库统计 */
    getMemoryStats() {
      return _fetchWithFallback('/api/memory/stats', {}, _mockMemoryStats);
    },

    // ========== Agent 手动停止开关 ==========

    /** 获取所有 Agent 启用状态 */
    getAgentEnabled() {
      return _fetchWithFallback('/api/orchestrator/agent/enabled', {}, { agents: {} });
    },

    /** 切换 Agent 启用/禁用 */
    toggleAgent(agentName, action) {
      return _fetchWithFallback('/api/orchestrator/agent/toggle', {
        method: 'POST',
        body: JSON.stringify({ agent_name: agentName, action: action || 'toggle' })
      }, { agent_name: agentName, enabled: true });
    },

    // ========== 流程手动停止开关 ==========

    /** 获取所有流程开关状态 */
    getFlowToggles() {
      return _fetchWithFallback('/api/flow/toggles', {}, { toggles: {} });
    },

    /** 切换流程开关 */
    setFlowToggle(name, enabled) {
      return _fetchWithFallback('/api/flow/toggle', {
        method: 'POST',
        body: JSON.stringify({ name: name, enabled: enabled })
      }, { name: name, enabled: enabled });
    },

    /** 获取技能列表 */
    getMemorySkills(agentFilter) {
      let url = '/api/memory/skills';
      if (agentFilter) url += '?agent=' + encodeURIComponent(agentFilter);
      return _fetchWithFallback(url, {}, { skills: [] });
    },

    /** 获取洞察列表 */
    getMemoryInsights(category) {
      let url = '/api/memory/insights';
      if (category) url += '?category=' + encodeURIComponent(category);
      return _fetchWithFallback(url, {}, { insights: [] });
    },

    /** 获取进化日志 */
    getEvolutionLog() {
      return _fetchWithFallback('/api/memory/evolution', {}, { log: [] });
    },

    /** 触发进化 */
    triggerEvolution() {
      return _fetchWithFallback('/api/memory/evolve', { method: 'POST' }, { new_skills: 0, pruned: 0, rules_discovered: 0 });
    },
    getPerformance() {
      return _fetchWithFallback('/api/memory/performance', {}, { performance: {} });
    },

    // ========== 知识库 ==========

    /** 获取知识库分类 */
    getKnowledgeCategories() {
      return _fetchWithFallback('/api/knowledge/categories', {}, { categories: [] });
    },

    /** 创建知识库分类 */
    createKnowledgeCategory(data) {
      return _fetchWithFallback('/api/knowledge/categories', { method: 'POST', body: JSON.stringify(data) }, { id: 'new' });
    },

    /** 获取知识库条目 */
    getKnowledgeItems(category) {
      let url = '/api/knowledge/items';
      if (category) url += '?category=' + encodeURIComponent(category);
      return _fetchWithFallback(url, {}, { items: [] });
    },

    /** 获取知识库FAQ */
    getKnowledgeFaqs() {
      return _fetchWithFallback('/api/knowledge/faqs', {}, { faqs: [] });
    },

    /** 创建FAQ */
    createFaq(data) {
      return _fetchWithFallback('/api/knowledge/faqs', { method: 'POST', body: JSON.stringify(data) }, { id: 'new' });
    },

    /** 搜索知识库 */
    searchKnowledge(query) {
      return _fetchWithFallback('/api/knowledge/search?q=' + encodeURIComponent(query), {}, { results: [] });
    },

    /** 导出知识库 */
    exportKnowledge(format) {
      return _fetchWithFallback('/api/knowledge/export', { method: 'POST', body: JSON.stringify({ format: format || 'json' }) }, { status: 'ok' });
    },

    // ========== 权限管理 ==========

    /** 获取用户列表 */
    getUsers() {
      return _fetchWithFallback('/api/rbac/users', {}, { users: [] });
    },

    /** 创建用户 */
    createUser(data) {
      return _fetchWithFallback('/api/rbac/users', { method: 'POST', body: JSON.stringify(data) }, { id: 'new' });
    },

    /** 更新用户 */
    updateUser(id, data) {
      return _fetchWithFallback('/api/rbac/users/' + encodeURIComponent(id), { method: 'PUT', body: JSON.stringify(data) }, { id: id });
    },

    /** 删除用户 */
    deleteUser(id) {
      return _fetchWithFallback('/api/rbac/users/' + encodeURIComponent(id), { method: 'DELETE' }, { status: 'ok' });
    },

    /** 设置用户角色 */
    setUserRole(id, role) {
      return _fetchWithFallback('/api/rbac/users/' + encodeURIComponent(id) + '/role', { method: 'POST', body: JSON.stringify({ role: role }) }, { id: id });
    },

    /** 获取角色列表 */
    getRoles() {
      return _fetchWithFallback('/api/rbac/roles', {}, { roles: [] });
    },

    /** 创建角色 */
    createRole(data) {
      return _fetchWithFallback('/api/rbac/roles', { method: 'POST', body: JSON.stringify(data) }, { id: 'new' });
    },

    /** 更新角色 */
    updateRole(id, data) {
      return _fetchWithFallback('/api/rbac/roles/' + encodeURIComponent(id), { method: 'PUT', body: JSON.stringify(data) }, { id: id });
    },

    /** 获取权限组 */
    getPermissionGroups() {
      return _fetchWithFallback('/api/rbac/permission-groups', {}, { permission_groups: [] });
    },

    // ========== 支付订单 ==========

    /** 获取订单列表 */
    getPaymentOrders(status) {
      let url = '/api/payment/orders';
      if (status) url += '?status=' + encodeURIComponent(status);
      return _fetchWithFallback(url, {}, { orders: [] });
    },

    /** 获取订单状态 */
    getPaymentOrderStatus(id) {
      return _fetchWithFallback('/api/payment/orders/' + encodeURIComponent(id) + '/status', {}, { status: 'unknown' });
    },

    /** 创建订单 */
    createPaymentOrder(data) {
      return _fetchWithFallback('/api/payment/orders', { method: 'POST', body: JSON.stringify(data) }, { id: 'new' });
    },

    /** 发起支付 */
    initiatePayment(orderId) {
      return _fetchWithFallback('/api/payment/orders/' + encodeURIComponent(orderId) + '/pay', { method: 'POST' }, { status: 'pending' });
    },

    /** 申请退款 */
    refundPayment(orderId, amount) {
      return _fetchWithFallback('/api/payment/orders/' + encodeURIComponent(orderId) + '/refund', { method: 'POST', body: JSON.stringify({ amount: amount || 0 }) }, { status: 'refunded' });
    },

    // ========== 工具 ==========

    /** 清除缓存 */
    clearCache() {
      _cache = {};
    },

    /** 可用性检查（探测后端是否在线） */
    checkHealth() {
      return _fetch('/api/health', {})
        .then(data => data && data.status === 'ok')
        .catch(() => false);
    }
  };
})();

// 全局导出
if (typeof window !== 'undefined') {
  window.SalesAPI = SalesAPI;
}
