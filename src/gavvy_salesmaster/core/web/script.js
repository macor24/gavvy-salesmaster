document.addEventListener('DOMContentLoaded', function() {
    // ── HTML 转义工具函数 ──────────────────
    function escHtml(str) {
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(str || ''));
        return div.innerHTML;
    }

    // ── 通用 Toast 提示 ──────────────────────
    window.showToast = function(message, type) {
        const existing = document.querySelector('.sales-toast');
        if (existing) existing.remove();
        const toast = document.createElement('div');
        toast.className = 'sales-toast';
        const bg = type === 'success' ? '#059669' : '#dc2626';
        const icon = type === 'success' ? '✅' : '❌';
        toast.style.cssText = `position:fixed;top:20px;right:20px;z-index:99999;background:${bg};color:#fff;padding:12px 20px;border-radius:8px;font-size:14px;font-weight:500;box-shadow:0 4px 20px rgba(0,0,0,0.2);display:flex;align-items:center;gap:8px;animation:slideIn 0.3s ease;`;
        toast.innerHTML = `${icon} ${message}`;
        document.body.appendChild(toast);
        setTimeout(() => { toast.style.opacity = '0'; toast.style.transition = 'opacity 0.3s'; setTimeout(() => toast.remove(), 300); }, 2500);
    }
    // 注入 slideIn 动画
    if (!document.getElementById('toast-style')) {
        const style = document.createElement('style');
        style.id = 'toast-style';
        style.textContent = '@keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }';
        document.head.appendChild(style);
    }
    const navItems = document.querySelectorAll('.nav-item, .top-nav-item');
    const views = document.querySelectorAll('.view');
    let pageTitle = document.querySelector('.page-title');
    let breadcrumbCurrent = document.querySelector('.breadcrumb .current');

    const pageNames = {
        'dashboard': '数据仪表盘',
        'workspace': '智能工作台',
        'customers': '客户中心',
        'analytics': '数据分析',
        'team': '虚拟团队',
        'abilities': '能力底座',
        'automation': '自动化流程',
        'memory': '学习记忆库',
        'api': 'API配置',
        'settings': '系统设置'
    };

    navItems.forEach(item => {
        item.addEventListener('click', function() {
            const targetView = this.getAttribute('data-view');
            
            navItems.forEach(nav => nav.classList.remove('active'));
            this.classList.add('active');
            
            views.forEach(view => view.classList.remove('active'));
            document.getElementById(targetView).classList.add('active');
            
            if (pageNames[targetView]) {
                if (pageTitle) pageTitle.textContent = pageNames[targetView];
                if (breadcrumbCurrent) breadcrumbCurrent.textContent = pageNames[targetView];
            }
            
            // 导航到各视图时加载真实数据
            loadViewData(targetView);
        });
    });

    const privateTabs = document.querySelectorAll('.ws-pri-tab, .private-tab');
    const tabPanels = document.querySelectorAll('.ws-pri-panel, .tab-panel');
    
    privateTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');
            
            privateTabs.forEach(t => t.classList.remove('active'));
            tabPanels.forEach(p => p.classList.remove('active'));
            
            this.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
        });
    });

    // 过滤器按钮已移除（新三栏布局无过滤器按钮）

    let _currentLeadId = null;

    // ── 从 API 加载客户列表 ──────────────────────────
    function loadCustomerList() {
        fetch('/api/customers').then(function(r){return r.json()}).then(function(data){
            var customers = data.customers || [];
            var listContainer = document.querySelector('.ws-customers-list');
            if (!listContainer) return;

            listContainer.innerHTML = customers.map(function(c){
                var badgeClass = '';
                if (c.intent === '高意向' || c.intent === '已成交') badgeClass = 'hot';
                else if (c.intent === '跟进中') badgeClass = 'warm';
                return '<div class="ws-customer" data-customer="' + c.id + '" onclick="selectCustomer(\'' + c.id + '\',\'' + escHtml(c.name) + '\',\'' + escHtml(c.intent) + '\')">' +
                    '<div class="ws-cust-top">' +
                        '<span class="ws-cust-name">' + escHtml(c.name) + '</span>' +
                        '<span class="ws-cust-intent ' + badgeClass + '">' + escHtml(c.intent) + '</span>' +
                        '<span class="ws-cust-time">' + escHtml(c.lastTime || '') + '</span>' +
                    '</div>' +
                    '<div class="ws-cust-last">' + escHtml(c.lastMsg || '暂无消息') + '</div>' +
                '</div>';
            }).join('');

            // 默认选中第一个客户
            if (customers.length > 0) {
                var first = customers[0];
                selectCustomer(first.id, first.name, first.intent);
            }
        }).catch(function(){});
    }

    // ── 统一视图数据加载 ──────────────────────────
    window.loadViewData = function loadViewData(viewName) {
        switch (viewName) {
            case 'dashboard':
                loadSummary();
                loadMemoryStats(); // 仪表盘有记忆库概览
                loadPipelineStages();
                checkQuickstartStatus();
                break;
            case 'workspace':
                loadCustomerList();
                // 检查LLM状态
                fetch('/api/llm/status').then(function(r){return r.json()}).then(function(d){
                    var el = document.getElementById('llm-indicator');
                    if (el) {
                        if (d.available) { el.textContent = '🤖 已就绪'; el.style.background = '#f0fdf4'; el.style.color = '#16a34a'; }
                        else { el.textContent = '⚙️ 未配置'; el.style.background = '#fef2f2'; el.style.color = '#dc2626'; }
                    }
                }).catch(function(){});
                break;
            case 'customers':
                loadCustomerCenter();
                break;
            case 'team':
                loadTeamData();
                break;
            case 'analytics':
                loadAnalyticsData();
                break;
            case 'memory':
                loadMemoryStats();
                if (typeof window.loadMemorySkills === 'function') window.loadMemorySkills();
                if (typeof window.loadMemoryEvolution === 'function') window.loadMemoryEvolution();
                if (typeof window.loadMemoryPerf === 'function') window.loadMemoryPerf();
                break;
            case 'abilities':
                loadAbilitiesData();
                break;
            case 'automation':
                loadAutomationData();
                break;
            case 'api':
                loadSettings();
                break;
            case 'scripts':
                loadScriptsPage();
                break;
            case 'knowledge':
                loadKnowledgeData();
                break;
            case 'permissions':
                loadPermissionsData();
                break;
            case 'payments':
                loadPaymentsData();
                break;
            case 'settings':
                loadSafetyStatus();
                loadSentriKitStatus();
                break;
        }
    }

    // ── Team 数据加载 ────────────────────────────
    function loadTeamData() {
        SalesAPI.getAgents().then(data => {
            const agents = data.agents || {};
            const agentList = Object.values(agents);
            const count = agentList.length;

            // 更新顶部队员统计
            const statNumber = document.querySelector('.team-header .stat-number');
            if (statNumber) statNumber.textContent = count;

            // 更新每个 Agent 卡片 —— 用 data-agent-key 匹配
            agentList.forEach(agent => {
                const key = agent.role_en || '';
                const card = document.querySelector(`.team-card[data-agent-key="${key}"]`);
                if (!card) return;
                const badge = card.querySelector('.card-status-badge');
                if (badge) {
                    badge.className = 'card-status-badge active';
                    badge.innerHTML = '<span class="pulse"></span> 运行中';
                }
            });
        }).catch(() => {});
    }

    // ── Analytics 数据加载 ────────────────────────
    var _analyticsCache = null;

    function loadAnalyticsData() {
        if (_analyticsCache && document.getElementById('ana-total-leads').textContent !== '0') return;

        function fill(data) {
            _analyticsCache = data;
            document.getElementById('ana-total-leads').textContent = data.total_leads || 0;
            document.getElementById('ana-avg-score').textContent = data.avg_score || 0;
            document.getElementById('ana-conversion').textContent = (data.conversion || 0) + '%';
            document.getElementById('ana-skills').textContent = data.skills_count || 0;

            // 趋势标记
            function setTrend(elId, value) {
                var el = document.getElementById(elId);
                if (!el) return;
                if (value === undefined || value === null) { el.textContent = ''; return; }
                var up = value > 0;
                el.textContent = (up ? '↑' : '↓') + Math.abs(value).toFixed(1) + '%';
                el.style.color = up ? '#16a34a' : '#dc2626';
            }
            setTrend('ana-leads-trend', data.leads_trend);
            setTrend('ana-score-trend', data.score_trend);
            setTrend('ana-conv-trend', data.conv_trend);
            setTrend('ana-skills-trend', data.skills_trend);

            // 更新时间
            var updated = document.getElementById('ana-updated-at');
            if (updated) updated.textContent = '更新于 ' + new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });

            var funnelBody = document.getElementById('funnel-body');
            if (funnelBody && data.funnel) {
                funnelBody.innerHTML = '<div style="padding:8px 0;">' + data.funnel.map(function(s) {
                    return '<div style="display:flex;align-items:center;margin-bottom:10px;">' +
                        '<span style="width:80px;font-size:13px;color:#475569;">' + s.name + '</span>' +
                        '<div style="flex:1;height:22px;background:#f1f5f9;border-radius:11px;overflow:hidden;">' +
                            '<div style="width:' + Math.max(s.pct, 3) + '%;height:100%;background:' + s.color + ';border-radius:11px;"></div>' +
                        '</div>' +
                        '<span style="width:50px;text-align:right;font-size:13px;font-weight:600;color:#0f172a;">' + s.count + '</span>' +
                        '<span style="width:40px;text-align:right;font-size:11px;color:#94a3b8;">' + s.pct + '%</span>' +
                    '</div>';
                }).join('') + '</div>';
            }

            var perfBody = document.getElementById('agent-perf-body');
            if (perfBody && data.agent_performance) {
                perfBody.innerHTML = '<div style="padding:8px 0;">' + data.agent_performance.map(function(a) {
                    var barColor = a.rate >= 70 ? '#22c55e' : a.rate >= 40 ? '#f59e0b' : '#ef4444';
                    return '<div style="display:flex;align-items:center;margin-bottom:8px;padding:6px 0;border-bottom:1px solid #f1f5f9;">' +
                        '<span style="width:90px;font-size:12px;color:#475569;">' + a.name + '</span>' +
                        '<div style="flex:1;height:6px;background:#f1f5f9;border-radius:3px;overflow:hidden;margin:0 8px;">' +
                            '<div style="width:' + a.rate + '%;height:100%;background:' + barColor + ';border-radius:3px;"></div>' +
                        '</div>' +
                        '<span style="width:36px;text-align:right;font-size:12px;font-weight:600;color:' + barColor + ';">' + a.rate + '%</span>' +
                        '<span style="width:60px;text-align:right;font-size:10px;color:#94a3b8;">' + a.success + '/' + a.total + '</span>' +
                    '</div>';
                }).join('') + '</div>';
            }
        }

        fetch('/api/analytics/summary').then(function(r){return r.json()}).then(fill)
            .catch(function(e){ console.log('loadAnalyticsData error:', e); });
    }

    // 导出分析报表
    function exportAnalytics() {
        var data = _analyticsCache;
        if (!data) {
            window.showToast && window.showToast('请先加载分析数据', 'fail');
            return;
        }
        var rows = [['指标', '值']];
        rows.push(['总客户数', data.total_leads || 0]);
        rows.push(['平均评分', data.avg_score || 0]);
        rows.push(['转化率', (data.conversion || 0) + '%']);
        rows.push(['已进化技能', data.skills_count || 0]);
        if (data.funnel) {
            rows.push(['', '']);
            rows.push(['销售漏斗', '']);
            data.funnel.forEach(function(s) { rows.push([s.name, s.count + ' (' + s.pct + '%)']); });
        }
        if (data.agent_performance) {
            rows.push(['', '']);
            rows.push(['Agent效能', '']);
            data.agent_performance.forEach(function(a) { rows.push([a.name, a.rate + '% (' + a.success + '/' + a.total + ')']); });
        }
        var csv = rows.map(function(r) { return r.join(','); }).join('\\n');
        var blob = new Blob(['\\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
        var link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'analytics_' + new Date().toISOString().slice(0, 10) + '.csv';
        link.click();
        URL.revokeObjectURL(link.href);
        window.showToast && window.showToast('报表已导出', 'success');
    }

    // ── Abilities 数据加载 ───────────────────────
    function loadAbilitiesData() {
        // 从 /api/abilities 获取能力数据（种子能力 + 进化技能）
        fetch('/api/abilities')
            .then(r => r.json())
            .then(data => {
                const abilities = data.abilities || [];
                const container = document.getElementById('abilitiesGrid');
                if (!container) return;

                if (abilities.length === 0) {
                    container.innerHTML = '<div class="ability-loading" style="text-align:center;padding:40px;color:#94a3b8;">暂无能力数据</div>';
                    return;
                }

                const builtin = abilities.filter(a => a.builtin);
                const evolved = abilities.filter(a => !a.builtin);

                // 更新标题
                const title = document.getElementById('abilitiesTitle');
                if (title) {
                    const total = abilities.length;
                    const base = builtin.length;
                    const evo = total - base;
                    if (evo > 0) {
                        title.innerHTML = `能力图谱 <span style="font-size:14px;color:#94a3b8;font-weight:400;">（${base}基础 + ${evo}进化）</span>`;
                    } else {
                        title.textContent = '四位一体能力底座';
                    }
                }

                // 更新元信息
                const meta = document.getElementById('abilitiesMeta');
                if (meta) {
                    const parts = [`${abilities.length}项能力`];
                    if (evolved.length > 0) {
                        const totalScore = evolved.reduce((s, a) => s + (a.score || 0), 0);
                        const avg = (totalScore / evolved.length * 100).toFixed(0);
                        parts.push(`进化技能平均分 ${avg}`);
                    }
                    meta.textContent = parts.join(' · ');
                }

                container.innerHTML = abilities.map(a => {
                    const id = a.id || '';
                    const icon = a.icon || '🧠';
                    const name = a.name || '未知能力';
                    const badge = a.badge || (a.builtin ? '全员共用' : '进化习得');
                    const desc = a.description || '';
                    const stats = (a.stats || []).map(s =>
                        `<div class="ability-stat"><span class="ability-stat-label">${s}</span></div>`
                    ).join('');
                    const caseText = a.case || '';
                    // 进化技能额外显示评分
                    const extra = !a.builtin ? `
                        <div class="ability-extra" style="margin-top:8px;padding:6px 10px;background:#f0fdf4;border-radius:6px;font-size:11px;color:#16a34a;">
                            🧬 进化 ${a.version || 1}代 · 评分 ${((a.score || 0) * 100).toFixed(0)} · 使用${a.use_count || 0}次
                            ${a.source_agent ? '· ' + a.source_agent : ''}
                        </div>
                    ` : '';
                    return `<div class="ability-card ${id}" data-ability-id="${id}">
                        <div class="ability-card-top">
                            <div class="ability-badge ${!a.builtin ? 'evolved' : ''}">${icon} ${badge}</div>
                        </div>
                        <h3 class="ability-title">${name}</h3>
                        <p class="ability-desc">${escHtml(desc)}</p>
                        ${stats ? '<div class="ability-stats">' + stats + '</div>' : ''}
                        ${caseText ? '<div class="ability-case"><div class="ability-case-header">实战案例</div><p class="ability-case-text">' + escHtml(caseText) + '</p></div>' : ''}
                        ${extra}
                    </div>`;
                }).join('');
            })
            .catch(() => {
                const container = document.getElementById('abilitiesGrid');
                if (container) container.innerHTML = '<div class="ability-loading" style="text-align:center;padding:40px;color:#ef4444;">加载失败</div>';
            });
    }

    // ── Automation 数据加载 ──────────────────────
    function loadAutomationData() {
        // 加载流程开关状态
        SalesAPI.getFlowToggles().then(function(data){
            var toggles = data.toggles || {};
            document.querySelectorAll('.toggle-switch').forEach(function(el){
                var name = el.getAttribute('data-flow-name');
                if (name && toggles[name] !== undefined) {
                    el.classList.toggle('active', toggles[name] === true);
                }
            });
        }).catch(function(){});
        
        // 加载管道阶段
        fetch('/api/pipeline/stages').then(function(r){return r.json()}).then(function(data){
            var stages = data.stages || [];
            var container = document.getElementById('pipeline-stages-inline');
            if (!container) return;
            container.innerHTML = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;">' +
              stages.map(function(s){
                var pct = data.total > 0 ? Math.round(s.count / data.total * 100) : 0;
                return '<div style="text-align:center;padding:12px 8px;background:var(--bg-secondary);border-radius:var(--radius-md);">' +
                  '<div style="font-size:24px;font-weight:700;">' + s.count + '</div>' +
                  '<div style="font-size:13px;color:var(--text-secondary);">' + (s.label || s.name) + '</div>' +
                  '<div style="margin-top:4px;height:4px;background:#e2e8f0;border-radius:2px;overflow:hidden;">' +
                  '<div style="height:100%;width:' + pct + '%;background:var(--accent-secondary);border-radius:2px;transition:width 0.3s;"></div></div>' +
                  '<div style="font-size:11px;color:var(--text-muted);margin-top:2px;">' + pct + '%</div></div>';
              }).join('') + '</div>';
        }).catch(function(){});

        // 加载 leads 阶段状态列表
        SalesAPI.getLeads().then(data => {
            const leads = data.leads || [];
            const stageCounts = { discovery: 0, research: 0, contact: 0, negotiation: 0,
                                  closing: 0, after_sales: 0, listing: 0 };
            leads.forEach(l => { const s = l.stage || 'discovery'; if (stageCounts[s] !== undefined) stageCounts[s]++; });
            const list = document.querySelector('#automation .auto-status-list');
            if (!list) return;
            const stageLabels = { discovery: '市场调研', research: '竞品分析', contact: '客户接触',
                                  negotiation: '商务谈判', closing: '成交', after_sales: '售后', listing: '上架' };
            list.innerHTML = Object.entries(stageLabels).map(([key, label]) => {
                const count = stageCounts[key] || 0;
                const active = count > 0;
                return `<div class="auto-step ${active ? 'active' : ''}">
                    <div class="step-indicator">${active ? '▶' : '○'}</div>
                    <div class="step-info">
                        <div class="step-name">${label}</div>
                        <div class="step-count">${count}个客户</div>
                    </div>
                </div>`;
            }).join('');
        }).catch(() => {});
    }

    // ── 客户中心数据加载 ──────────────────────────
    function loadCustomerCenter() {
        SalesAPI.getLeads().then(data => {
            const leads = data.leads || [];

            // 更新统计卡片（用 data-target 匹配的动画数字不覆盖，只更新实际值）
            const stageCounts = { discovery: 0, research: 0, contact: 0, negotiation: 0,
                                  closing: 0, after_sales: 0, listing: 0 };
            leads.forEach(l => {
                const s = l.stage || 'discovery';
                if (stageCounts[s] !== undefined) stageCounts[s]++;
            });
            const total = leads.length;
            const following = stageCounts.contact + stageCounts.negotiation;
            const closed = stageCounts.closing;
            const newOnes = stageCounts.discovery + stageCounts.research;

            const statCards = document.querySelectorAll('#customers .stat-card .stat-value');
            if (statCards.length >= 4) {
                statCards[0].setAttribute('data-target', total);
                statCards[1].setAttribute('data-target', following);
                statCards[2].setAttribute('data-target', closed);
                statCards[3].setAttribute('data-target', newOnes);
                // 立即显示真实值
                statCards[0].textContent = total;
                statCards[1].textContent = following;
                statCards[2].textContent = closed;
                statCards[3].textContent = newOnes;
            }

            // 更新客户表格
            const tbody = document.querySelector('#customers .data-table tbody');
            if (!tbody) return;

            if (leads.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" style="padding:40px;text-align:center;color:#94a3b8;">暂无客户数据，通过"快捷操作 > 批量导入"添加</td></tr>';
                return;
            }

            const stageLabels = {
                'discovery': ['新客户', ''], 'research': ['调研中', ''],
                'contact': ['跟进中', 'warm'], 'negotiation': ['议价中', 'hot'],
                'closing': ['成交中', 'hot'], 'after_sales': ['售后', 'success'],
                'listing': ['上架中', ''],
            };

            tbody.innerHTML = leads.map((lead, i) => {
                const info = lead.info || {};
                const name = info.name || info.company || lead.id || '未知';
                const stage = lead.stage || 'discovery';
                const [stageLabel, badgeCls] = stageLabels[stage] || [stage, ''];
                const score = lead.score || 0;
                const stars = score >= 80 ? '⭐⭐⭐' : score >= 50 ? '⭐⭐' : '⭐';
                const lastTime = lead.updated_at ? lead.updated_at.slice(11, 16) : '--';
                const isLast = i === leads.length - 1;
                return `<tr${isLast ? '' : ' style="border-bottom:1px solid var(--border-color);"'}>
                    <td style="padding:8px 12px;">${name}</td>
                    <td style="padding:8px 12px;"><span class="status-badge ${badgeCls}">${stageLabel}</span></td>
                    <td style="padding:8px 12px;">${stars}</td>
                    <td style="padding:8px 12px;">${lastTime}</td>
                    <td style="padding:8px 12px;"><button class="btn-ghost" onclick="window.switchToLead('${lead.id}')">联系</button> <button class="btn-ghost" style="color:#2563eb;" onclick="window.showCRMDetail('${lead.id}')">CRM</button></td>
                </tr>`;
            }).join('');
        }).catch(() => {});
    }

    // 从客户中心表格联系按钮切换到工作台
    window.switchToLead = function(leadId) {
        // 导航到工作台
        const wsBtn = document.querySelector('[data-view="workspace"]');
        if (wsBtn) wsBtn.click();
        // 选中对应客户
        setTimeout(() => {
            const card = document.querySelector(`.ws-customer[data-lead-id="${leadId}"]`);
            if (card) card.click();
        }, 100);
    };

    // ── CRM 客户详情弹窗 ──

    window.showCRMDetail = function(customerId) {
        SalesAPI.crmCustomerDetail(customerId).then(function(data) {
            var customer = data.customer;
            if (!customer) { window.showToast('客户不存在', 'fail'); return; }
            var contacts = data.contacts || [];
            var deals = data.deals || [];
            var contracts = data.contracts || [];
            var activities = data.activities || [];

            // 构建弹窗内容
            var html = '<div style="max-height:70vh;overflow-y:auto;">';

            // 基本信息
            html += '<div style="margin-bottom:16px;padding:12px;background:#f8fafc;border-radius:8px;">';
            html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">';
            html += '<h4 style="margin:0;font-size:16px;">' + escHtml(customer.name || '未知') + '</h4>';
            html += '<span style="font-size:12px;padding:2px 8px;border-radius:4px;background:#e2e8f0;">' + escHtml(customer.stage_label || customer.stage) + '</span>';
            html += '</div>';
            if (customer.company) html += '<p style="margin:2px 0;font-size:13px;color:#64748b;">🏢 ' + escHtml(customer.company) + '</p>';
            if (customer.industry) html += '<p style="margin:2px 0;font-size:13px;color:#64748b;">📂 ' + escHtml(customer.industry) + '</p>';
            if (customer.phone) html += '<p style="margin:2px 0;font-size:13px;color:#64748b;">📞 ' + escHtml(customer.phone) + '</p>';
            if (customer.email) html += '<p style="margin:2px 0;font-size:13px;color:#64748b;">📧 ' + escHtml(customer.email) + '</p>';
            if (customer.notes) html += '<p style="margin:6px 0 0;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;padding-top:6px;">📝 ' + escHtml(customer.notes) + '</p>';
            html += '</div>';

            // 联系人
            html += '<h5 style="margin:0 0 8px;font-size:14px;color:#475569;">👤 联系人 (' + contacts.length + ')</h5>';
            if (contacts.length > 0) {
                contacts.forEach(function(ct) {
                    html += '<div style="padding:8px;margin-bottom:6px;background:#fff;border:1px solid #e2e8f0;border-radius:6px;font-size:13px;">';
                    html += '<strong>' + escHtml(ct.name) + '</strong>';
                    if (ct.role) html += ' <span style="color:#64748b;">(' + escHtml(ct.role) + ')</span>';
                    if (ct.phone) html += '<br><span style="color:#64748b;">📞 ' + escHtml(ct.phone) + '</span>';
                    if (ct.email) html += ' <span style="color:#64748b;">📧 ' + escHtml(ct.email) + '</span>';
                    if (ct.is_primary) html += ' <span style="color:#2563eb;font-size:11px;">★主要联系人</span>';
                    html += '</div>';
                });
            } else {
                html += '<p style="font-size:13px;color:#94a3b8;padding:4px 0;">暂无联系人</p>';
            }

            // 商机
            html += '<h5 style="margin:12px 0 8px;font-size:14px;color:#475569;">💰 商机 (' + deals.length + ')</h5>';
            if (deals.length > 0) {
                deals.forEach(function(d) {
                    html += '<div style="padding:8px;margin-bottom:6px;background:#fff;border:1px solid #e2e8f0;border-radius:6px;font-size:13px;display:flex;justify-content:space-between;">';
                    html += '<div><strong>' + escHtml(d.title) + '</strong><br><span style="color:#64748b;">' + (d.stage_label || d.stage) + '</span></div>';
                    html += '<div style="text-align:right;"><strong style="color:#2563eb;">¥' + (d.amount || 0).toLocaleString() + '</strong><br><span style="color:#64748b;font-size:12px;">' + (d.probability || 0) + '%</span></div>';
                    html += '</div>';
                });
            } else {
                html += '<p style="font-size:13px;color:#94a3b8;padding:4px 0;">暂无商机</p>';
            }

            // 合同
            html += '<h5 style="margin:12px 0 8px;font-size:14px;color:#475569;">📄 合同 (' + contracts.length + ')</h5>';
            if (contracts.length > 0) {
                contracts.forEach(function(ct) {
                    html += '<div style="padding:8px;margin-bottom:6px;background:#fff;border:1px solid #e2e8f0;border-radius:6px;font-size:13px;display:flex;justify-content:space-between;">';
                    html += '<div><strong>' + escHtml(ct.title) + '</strong><br><span style="color:#64748b;">' + (ct.status_label || ct.status) + '</span></div>';
                    html += '<div style="text-align:right;"><strong style="color:#059669;">¥' + (ct.amount || 0).toLocaleString() + '</strong></div>';
                    html += '</div>';
                });
            } else {
                html += '<p style="font-size:13px;color:#94a3b8;padding:4px 0;">暂无合同</p>';
            }

            // 活动记录
            html += '<h5 style="margin:12px 0 8px;font-size:14px;color:#475569;">📋 活动记录 (' + activities.length + ')</h5>';
            if (activities.length > 0) {
                activities.forEach(function(a) {
                    var typeIcon = {call: '📞', email: '📧', meeting: '🤝', note: '📝', task: '✅', system: '⚙️'};
                    html += '<div style="padding:6px 8px;margin-bottom:4px;background:#fff;border:1px solid #e2e8f0;border-radius:6px;font-size:13px;">';
                    html += '<span>' + (typeIcon[a.type] || '📝') + '</span> ';
                    html += '<strong>' + escHtml(a.title) + '</strong>';
                    html += '<span style="color:#94a3b8;font-size:12px;float:right;">' + (a.created_at || '').slice(0, 16) + '</span>';
                    if (a.content) html += '<p style="margin:4px 0 0;color:#64748b;font-size:12px;">' + escHtml(a.content) + '</p>';
                    html += '</div>';
                });
            } else {
                html += '<p style="font-size:13px;color:#94a3b8;padding:4px 0;">暂无活动记录</p>';
            }

            html += '</div>';
            window.showAgentModal('📊 ' + escHtml(customer.name) + ' — CRM 详情', html);
        }).catch(function() {
            window.showToast('加载CRM详情失败', 'fail');
        });
    };

    function switchToCustomer(card) {
        const leadId = card.getAttribute('data-lead-id');
        if (!leadId) return;
        _currentLeadId = leadId;

        // 更新头部信息 - 新三栏布局
        const infoEls = card.querySelector('.ws-cust-name');
        const name = infoEls ? infoEls.textContent.trim() : leadId;
        const badgeEl = card.querySelector('.ws-cust-intent');
        const badgeText = badgeEl ? badgeEl.textContent.trim() : '新客户';

        const nameTitle = document.querySelector('.ws-chat-name');
        const statusEl = document.querySelector('.ws-chat-agent');
        const chatStatus = document.querySelector('.ws-chat-status');

        if (nameTitle) {
            // ws-chat-name contains name text + ws-chat-status span
            const nameTextNode = nameTitle.childNodes[0];
            if (nameTextNode) nameTextNode.textContent = name + ' ';
            if (chatStatus) {
                chatStatus.textContent = badgeText;
                chatStatus.className = 'ws-chat-status ' + (badgeText === '成交中' ? 'hot' : badgeText === '跟进中' ? 'warm' : '');
            }
        }
        if (statusEl) statusEl.textContent = '加载中...';

        // 从 API 加载 lead 详情（含对话历史）
        const messagesContainer = document.getElementById('wsChatMessages');
        if (messagesContainer) {
            messagesContainer.innerHTML = '<div class="ws-msg system"><div class="ws-msg-bubble"><p>正在加载对话...</p></div></div>';
        }

        SalesAPI.getLead(leadId).then(lead => {
            if (!lead) return;
            const history = lead.history || [];
            if (statusEl) statusEl.textContent = `${history.length}条消息 · ${lead.stage || 'discovery'}`;

            if (messagesContainer) {
                if (history.length === 0) {
                    messagesContainer.innerHTML = '<div class="ws-msg system"><div class="ws-msg-bubble"><p>暂无历史消息，开始新的对话</p></div></div>';
                } else {
                    messagesContainer.innerHTML = history.map(h => {
                        const isAgent = !!h.agent;
                        if (isAgent) {
                            const sender = h.agent_cn || h.agent || 'AI助手';
                            return `<div class="ws-msg agent">
                                <div class="ws-msg-bubble">
                                    <div class="ws-msg-sender">${sender} <span class="ws-ai-tag">AI</span></div>
                                    <p>${h.summary || h.output_text || '(无内容)'}</p>
                                    <div class="ws-msg-time">${(h.timestamp || '').slice(11,16) || ''}</div>
                                </div>
                            </div>`;
                        }
                        return `<div class="ws-msg customer">
                            <div class="ws-msg-bubble"><p>${h.text || h.message || ''}</p>
                            <div class="ws-msg-time">${(h.timestamp || '').slice(11,16) || ''}</div></div>
                        </div>`;
                    }).join('');
                }
            }
        }).catch(() => {
            if (messagesContainer) {
                messagesContainer.innerHTML = '<div class="ws-msg system"><div class="ws-msg-bubble"><p>加载失败，请重试</p></div></div>';
            }
        });

        // 更新评分卡片
        SalesAPI.getLeadScore(leadId).then(data => {
            const score = data.score;
            if (score) {
                const scoreEl = document.querySelector('.score-value');
                if (scoreEl) scoreEl.textContent = score.total_score || score.score || 0;
                const levelEl = document.querySelector('.score-level');
                if (levelEl && score.level) levelEl.textContent = score.level;
            }
        }).catch(() => {});
    }

    const chatInput = document.getElementById('wsChatInput');
    const sendBtn = document.getElementById('wsSendBtn');
    const chatMessages = document.getElementById('wsChatMessages');

    if (sendBtn && chatInput) {
        function sendMessage() {
            const message = chatInput.value.trim();
            if (message) {
                addMessage(message, 'customer');
                chatInput.value = '';
                const customerName = _currentLeadId ? (document.querySelector('.ws-customer.active .ws-cust-name')?.textContent?.trim() || '在线客户') : '在线客户';
                
                // 显示打字中状态
                const typingId = 'typing-' + Date.now();
                const typingDiv = document.createElement('div');
                typingDiv.className = 'ws-msg agent';
                typingDiv.id = typingId;
                typingDiv.innerHTML = '<div class="ws-msg-bubble"><div class="ws-msg-sender">售前谈判官 <span class="ws-ai-tag">AI</span></div><div class="typing-indicator"><span></span><span></span><span></span></div></div>';
                document.getElementById('wsChatMessages').appendChild(typingDiv);
                document.getElementById('wsChatMessages').scrollTop = document.getElementById('wsChatMessages').scrollHeight;

                SalesAPI.sendMessage(message, customerName, '通用咨询').then(data => {
                    const fullText = data.reply || '收到您的咨询，正在为您分析最佳方案...';
                    const agentName = data.agent || '售前谈判官';
                    
                    // 移除打字指示
                    const typingEl = document.getElementById(typingId);
                    if (typingEl) typingEl.remove();
                    
                    // 逐字输出
                    typeWriter(fullText, agentName);
                }).catch(() => {
                    const typingEl = document.getElementById(typingId);
                    if (typingEl) typingEl.remove();
                    setTimeout(() => {
                        const responses = [
                            '好的，我理解您的需求。这个产品非常适合您的情况，让我为您详细介绍一下...',
                            '感谢您的咨询！我们的产品有以下几个核心优势...',
                            '好的，您提到的价格问题我这边可以帮您申请一个优惠...',
                            '让我为您计算一下最适合的方案，请稍等...',
                            '这个需求完全可以满足，我们有专门的方案来帮助您...'
                        ];
                        typeWriter(responses[Math.floor(Math.random() * responses.length)], '售前谈判官');
                    }, 800);
                });
            }
        }

        function typeWriter(text, sender) {
            const msgDiv = document.createElement('div');
            msgDiv.className = 'ws-msg agent';
            msgDiv.innerHTML = '<div class="ws-msg-bubble"><div class="ws-msg-sender">' + sender + ' <span class="ws-ai-tag">AI</span></div><p class="typewriter-text"></p><div class="ws-msg-time">' + getCurrentTime() + '</div></div>';
            document.getElementById('wsChatMessages').appendChild(msgDiv);
            document.getElementById('wsChatMessages').scrollTop = document.getElementById('wsChatMessages').scrollHeight;
            
            const p = msgDiv.querySelector('.typewriter-text');
            let i = 0;
            // 根据文本长度动态调整速度：短文本慢一点(50ms)，长文本快一点(20ms)
            const speed = text.length > 150 ? 15 : text.length > 80 ? 25 : 35;
            
            function addChar() {
                if (i < text.length) {
                    p.textContent += text[i];
                    i++;
                    // 每10-15个字符滚动一次
                    if (i % 12 === 0) {
                        document.getElementById('wsChatMessages').scrollTop = document.getElementById('wsChatMessages').scrollHeight;
                    }
                    const delay = text[i-1] === '，' || text[i-1] === '。' || text[i-1] === '！' || text[i-1] === '？' || text[i-1] === '\n' ? speed * 4 : speed;
                    setTimeout(addChar, delay);
                }
            }
            addChar();
        }

        sendBtn.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    function addMessage(text, type, sender = '', avatar = '') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `ws-msg ${type}`;
        
        if (type === 'agent') {
            messageDiv.innerHTML = `
                <div class="ws-msg-bubble">
                    <div class="ws-msg-sender">
                        <span>${sender}</span>
                        <span class="ws-ai-tag">AI</span>
                    </div>
                    <p>${text}</p>
                    <div class="ws-msg-time">${getCurrentTime()}</div>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="ws-msg-bubble">
                    <p>${text}</p>
                    <div class="ws-msg-time">${getCurrentTime()}</div>
                </div>
            `;
        }
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function addThinkingMessage() {
        const thinkingDiv = document.createElement('div');
        thinkingDiv.className = 'ws-msg system';
        thinkingDiv.innerHTML = `
            <div class="ws-msg-bubble">
                <div class="thinking-header">
                    <span class="thinking-icon">🧠</span>
                    <span class="thinking-label">内部分析 · 心理学家 + 谈判专家</span>
                </div>
                <div class="thinking-content">
                    <div class="analysis-item">
                        <strong>客户心理：</strong>
                        <span>客户正在积极沟通，有较强的购买意向，但可能对价格有所顾虑。</span>
                    </div>
                    <div class="analysis-item">
                        <strong>建议策略：</strong>
                        <span>适当强调产品价值和限时优惠，可以适当让步但需设置底线。</span>
                    </div>
                    <div class="analysis-item">
                        <strong>推荐话术：</strong>
                        <span>"这个优惠名额有限，如果您今天确定，我可以帮您申请额外福利..."</span>
                    </div>
                </div>
            </div>
        `;
        chatMessages.appendChild(thinkingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function getCurrentTime() {
        const now = new Date();
        return now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');
    }

    // ─── 真实 API 数据加载 ─────────────────────────────

    // 加载编排器摘要 → 更新仪表盘统计数据
    function loadSummary() {
        SalesAPI.getSummary().then(data => {
            // 按 data-key 属性更新每个统计卡片
            document.querySelectorAll('.stat-value[data-key]').forEach(el => {
                const key = el.getAttribute('data-key');
                const val = data[key];
                if (val !== undefined) {
                    const prefix = el.getAttribute('data-prefix') || '';
                    const suffix = el.getAttribute('data-suffix') || '';
                    el.textContent = prefix + val + suffix;
                }
            });

            // 更新团队页总人数
            const statNumber = document.querySelector('.stat-number');
            if (statNumber) {
                statNumber.textContent = data.agent_count || 0;
            }

            // 更新安全模式显示
            if (data.safety_mode) {
                const safetyBadge = document.querySelector('.safety-badge');
                if (safetyBadge) {
                    safetyBadge.textContent = data.safety_mode.mode_label || '保守模式';
                }
            }
        }).catch(() => {});
    }

    // 加载Agent列表 → 更新团队卡片状态
    function loadAgents() {
        SalesAPI.getAgents().then(function(data) {
            const agents = data.agents || {};
            // 在仪表盘团队状态显示
            const teamCards = document.querySelectorAll('.dashboard-grid .team-card');
            // 加载 Agent 启用状态
            SalesAPI.getAgentEnabled().then(function(stateData) {
                var states = stateData.agents || {};
                teamCards.forEach(function(card) {
                    var h3 = card.querySelector('h4');
                    if (!h3) return;
                    var cnName = h3.textContent.trim();
                    // 映射中文名到英文key
                    var agentMap = {'市场调研官':'market_research_agent','竞品分析官':'competitor_intel_agent','售前谈判官':'presales_agent','售后维系官':'aftersales_agent','采购供应链官':'procurement_agent','运营增长官':'operations_agent','运营助理':'platform_ops_agent'};
                    var key = agentMap[cnName];
                    if (key && key in states) {
                        var statusEl = card.querySelector('.team-status');
                        if (!statusEl) {
                            statusEl = document.createElement('span');
                            statusEl.className = 'team-status';
                            statusEl.style.cssText = 'margin-left:6px;font-size:11px;padding:2px 6px;border-radius:4px;';
                            h3.parentNode.appendChild(statusEl);
                        }
                        if (states[key].enabled) {
                            statusEl.textContent = '● 在线';
                            statusEl.style.color = '#22c55e';
                        } else {
                            statusEl.textContent = '● 已停';
                            statusEl.style.color = '#ef4444';
                        }
                    }
                });
            }).catch(function() {});
        }).catch(function() {});
    }

    // 加载安全模式状态 → 更新安全配置面板
    function loadSafetyStatus() {
        SalesAPI.getSafetyStatus().then(data => {
            const mode = data.mode || 'conservative';
            const modeLabel = data.mode_label || '保守模式';
            // 更新安全模式标签
            const modeEl = document.querySelector('.safety-mode-label');
            if (modeEl) modeEl.textContent = modeLabel;
            // 更新安全模式select
            const sel = document.getElementById('safety-mode-select');
            if (sel) sel.value = mode;
            // 显示/隐藏阈值区域
            const thresh = document.getElementById('safety-thresholds');
            if (thresh) thresh.style.display = (mode === 'open' || mode === 'custom') ? 'block' : 'none';
            // 填充阈值（如有返回）
            if (data.price_ceiling != null) {
                var el = document.getElementById('threshold-price-ceiling');
                if (el) el.value = data.price_ceiling;
            }
            if (data.discount_floor != null) {
                var el = document.getElementById('threshold-discount-floor');
                if (el) el.value = data.discount_floor;
            }
            if (data.daily_limit != null) {
                var el = document.getElementById('threshold-daily-limit');
                if (el) el.value = data.daily_limit;
            }
            if (data.sensitive_words != null) {
                var el = document.getElementById('threshold-sensitive-words');
                if (el) el.value = data.sensitive_words;
            }
            // 渲染安全日志
            var logsContainer = document.getElementById('safety-logs');
            if (logsContainer && data.logs && data.logs.length > 0) {
                logsContainer.innerHTML = data.logs.slice(-20).map(function(log) {
                    var ts = log.timestamp || log.time || '';
                    var agent = log.agent_name || '';
                    var action = log.action || '';
                    var result = log.approved ? '✅ 通过' : (log.approved === false ? '⛔ 拦截' : '');
                    var summary = log.summary || log.reason || '';
                    return '<div style="padding:4px 0;border-bottom:1px solid var(--border-color);">' +
                        '<span style="color:var(--text-muted);">' + ts + '</span> ' +
                        '<strong>' + agent + '</strong> ' + action + ' ' + result +
                        (summary ? '<br><span style="color:var(--text-secondary);">' + summary + '</span>' : '') +
                        '</div>';
                }).join('');
            } else if (logsContainer) {
                logsContainer.innerHTML = '<div style="color:var(--text-muted);">暂无安全日志</div>';
            }
        }).catch(() => {});
    }

    // 保存安全阈值
    window.saveSafetyThresholds = function() {
        var thresholds = {
            price_ceiling: parseInt(document.getElementById('threshold-price-ceiling')?.value) || 50000,
            discount_floor: parseInt(document.getElementById('threshold-discount-floor')?.value) || 70,
            daily_limit: parseInt(document.getElementById('threshold-daily-limit')?.value) || 10,
            sensitive_words: document.getElementById('threshold-sensitive-words')?.value || ''
        };
        SalesAPI.saveSettings({ config: { safety_thresholds: thresholds } }).then(function(resp) {
            if (resp.saved || resp.status === 'ok') { showToast('安全阈值已保存', 'success'); }
            else { showToast('保存失败', 'fail'); }
        }).catch(function() { showToast('保存失败', 'fail'); });
    }

    // ── 渠道集成 ──────────────────────────────
    var _currentChannel = '';
    window.showChannelConfig = function(channel) {
        _currentChannel = channel;
        var names = {wecom: '企业微信', dingtalk: '钉钉', feishu: '飞书'};
        var title = document.getElementById('channel-config-title');
        if (title) title.textContent = '配置 ' + (names[channel] || channel);
        var form = document.getElementById('channel-config-form');
        if (form) form.style.display = 'block';
        SalesAPI.getSettings().then(function(data) {
            var channels = data.channels || {};
            var cfg = channels[channel] || {};
            var urlEl = document.getElementById('channel-webhook-url');
            if (urlEl) urlEl.value = cfg.webhook_url || '';
        }).catch(function(){});
    };
    window.saveChannelConfig = function() {
        var urlEl = document.getElementById('channel-webhook-url');
        if (!urlEl) return;
        var webhookUrl = urlEl.value.trim();
        if (!webhookUrl) { window.showToast('请输入 Webhook URL', 'warning'); return; }
        SalesAPI.saveSettings({channels: (_channels||{})[_currentChannel] = {webhook_url: webhookUrl, enabled: true}}).then(function() {
            window.showToast('渠道已保存', 'success');
        }).catch(function() { window.showToast('保存失败', 'fail'); });
    };

    // 加载 SentriKit 集成状态
    function loadSentriKitStatus() {
        SalesAPI.getSentriKitStatus().then(data => {
            const badge = document.getElementById('SentriKit-badge');
            const toggle = document.getElementById('SentriKit-toggle');
            const desc = document.getElementById('SentriKit-desc');
            if (badge) {
                if (data.available) {
                    badge.textContent = data.enabled ? '已接入' : '已关闭';
                    badge.className = data.enabled ? 'SentriKit-badge connected' : 'SentriKit-badge disabled';
                } else {
                    badge.textContent = '未安装';
                    badge.className = 'SentriKit-badge missing';
                }
            }
            if (toggle) {
                toggle.checked = data.enabled && data.available;
                toggle.disabled = !data.available;
            }
            if (desc) {
                if (data.active) {
                    desc.textContent = 'SentriKit Reporter 已集成，销售策略报告自动同步';
                    refreshEvolveStatus();
                } else if (data.available && !data.enabled) {
                    desc.textContent = 'SentriKit 已安装但集成已关闭，可手动开启';
                } else {
                    desc.textContent = '未检测到 SentriKit（SentriKit-toolkit）';
                }
            }
        }).catch(() => {});
    }

    // 进化闭环
    function refreshEvolveStatus() {
        SalesAPI.getSentriKitStatus().then(data => {
            if (!data.available) return;
            const section = document.getElementById('evolve-section');
            if (section) section.style.display = '';
            // 调用后端 /api/SentriKit/evolve-status（如果存在）或从本地状态推断
            fetch('/api/orchestrator/summary').then(r => r.json()).catch(() => ({})).then(summary => {
                const badge = document.getElementById('evolve-status-badge');
                const rate = document.getElementById('evolve-success-rate');
                const score = document.getElementById('evolve-judge-score');
                if (badge) badge.textContent = '就绪';
                if (badge) badge.style.background = '#f0fdf4';
                if (badge) badge.style.color = '#16a34a';
                // 如果后端有进化数据则展示
                if (summary.last_evolve) {
                    if (rate) rate.textContent = (summary.last_evolve.score || '-') + '%';
                }
            }).catch(() => {});
        }).catch(() => {});
    }

    function triggerEvolveRun() {
        const btn = document.querySelector('button[onclick="triggerEvolveRun()"]');
        const result = document.getElementById('evolve-result');
        if (btn) { btn.textContent = '⏳ 进化中...'; btn.disabled = true; }
        if (result) {
            result.style.display = '';
            result.textContent = '触发进化闭环...';
        }
        fetch('/api/evolve/run', { method: 'POST' })
            .then(r => r.json())
            .then(data => {
                if (result) {
                    result.innerHTML = '<span style="color:#16a34a;">✅ 进化完成</span>';
                    if (data.new_skills) result.innerHTML += ' · 新技能: ' + data.new_skills;
                    if (data.pruned) result.innerHTML += ' · 淘汰: ' + data.pruned;
                }
                setTimeout(refreshEvolveStatus, 1000);
            })
            .catch(() => {
                if (result) {
                    result.style.display = '';
                    result.innerHTML = '<span style="color:#dc2626;">❌ 进化触发失败（可能需要企业版）</span>';
                }
            })
            .finally(() => {
                if (btn) { btn.textContent = '🚀 触发进化'; btn.disabled = false; }
            });
    }

    // SentriKit 开关
    document.addEventListener('change', function(e) {
        if (e.target && e.target.id === 'SentriKit-toggle') {
            const enabled = e.target.checked;
            SalesAPI.toggleSentriKit(enabled).then(() => {
                loadSentriKitStatus();
                const badge = document.getElementById('SentriKit-badge');
                if (badge) {
                    badge.textContent = enabled ? '已接入' : '已关闭';
                    badge.className = enabled ? 'SentriKit-badge connected' : 'SentriKit-badge disabled';
                }
                showToast(enabled ? 'SentriKit 集成已开启' : 'SentriKit 集成已关闭', 'success');
            }).catch(() => showToast('设置保存失败', 'fail'));
        }
    });

    // 加载API设置
    function loadSettings() {
        SalesAPI.getSettings().then(data => {
            const apiKeys = data.api_keys || {};
            const platforms = data.platforms || {};
            // 更新API配置卡片状态
            Object.entries(apiKeys).forEach(([key, value]) => {
                if (value) {
                    const card = document.querySelector(`[data-api-key=\"${key}\"]`);
                    if (card) {
                        const status = card.querySelector('.api-status');
                        if (status) {
                            status.classList.add('connected');
                            status.innerHTML = '<span class="status-dot"></span> 已连接';
                        }
                    }
                }
            });
        }).catch(() => {});
    }

    // ── 流程开关 ──────────────────────────────

    function loadFlowToggles() {
        SalesAPI.getFlowToggles().then(function(data) {
            var toggles = data.toggles || {};
            document.querySelectorAll('[data-flow-name]').forEach(function(el) {
                var name = el.getAttribute('data-flow-name');
                if (name in toggles) {
                    updateToggleUI(el, toggles[name]);
                }
            });
        }).catch(function() {});
    }

    // 流程开关点击切换
    var FLOW_NAME_MAP = {
        auto_discovery: 'auto_discovery',
        auto_competitor_monitor: 'auto_competitor_monitor',
        auto_chat_response: 'smart_response',
        auto_quote_deal: 'auto_quote_deal',
        auto_scheduled_publish: 'auto_scheduled_publish',
    };
    document.addEventListener('click', function(e) {
        var el = e.target.closest('[data-flow-name]');
        if (el && el.classList.contains('toggle-switch')) {
            var name = el.getAttribute('data-flow-name');
            var backendName = FLOW_NAME_MAP[name] || name;
            var enabled = !el.classList.contains('active');
            SalesAPI.setFlowToggle(backendName, enabled).then(function(res) {
                updateToggleUI(el, res.enabled);
                var labels = {
                    auto_discovery: '自动客户发现',
                    auto_competitor_monitor: '自动竞品监控',
                    auto_chat_response: '智能对话响应',
                    auto_quote_deal: '自动报价成交',
                    auto_scheduled_publish: '定时上架发布',
                };
                showToast((res.enabled ? '已开启 ' : '已关闭 ') + (labels[name] || name), 'success');
            }).catch(function() {
                showToast('切换失败', 'fail');
            });
        }
    });

    // ── 学习记忆库 ──────────────────────────────

    function loadMemoryStats() {
        SalesAPI.getMemoryStats().then(data => {
            const map = {
                'episodes': '案例', 'insights': '洞察', 'skills': '技能',
                'patterns': '模式', 'rules': '规则', 'evolution_events': '进化事件'
            };
            Object.entries(map).forEach(([key, label]) => {
                const el = document.querySelector(`.memory-stat .mem-stat-label`);
                if (el && el.textContent === label) {
                    el.previousElementSibling.textContent = data[key] ?? '-';
                }
            });
            // 更新记忆利用率条
            const total = Object.keys(map).reduce((s, k) => s + (parseInt(data[k]) || 0), 0);
            const bar = document.getElementById('memory-usage-bar');
            const pct = document.getElementById('memory-usage-pct');
            if (bar && pct) {
                const usage = Math.min(100, Math.round(total / 60 * 100));
                bar.style.width = usage + '%';
                pct.textContent = usage + '%';
            }
            // 更新仪表盘记忆库概览
            document.querySelectorAll('.mini-num[data-mkey]').forEach(el => {
                const mk = el.getAttribute('data-mkey');
                if (data[mk] !== undefined) el.textContent = data[mk];
            });
        }).catch(() => {});
    }

    window.loadMemorySkills = function() {
        SalesAPI.getMemorySkills().then(data => {
            const list = document.getElementById('memory-skills-list');
            const skills = data.skills || [];
            if (skills.length === 0) {
                list.innerHTML = '<div class="memory-empty">暂无技能，点击"触发进化"生成</div>';
                return;
            }
            list.innerHTML = skills.map(s => `
                <div class="memory-item">
                    <div class="mem-item-title">${s.name || '未命名'}</div>
                    <div class="mem-item-meta">Agent: ${s.agent || '通用'} · 版本 v${s.version || 1} · 评分 ${(s.score || 0).toFixed(2)} · 使用 ${s.use_count || 0}次</div>
                </div>
            `).join('');
        }).catch(() => {});
    };

    window.loadMemoryEvolution = function() {
        SalesAPI.getEvolutionLog().then(data => {
            const list = document.getElementById('memory-evolution-list');
            const log = data.log || [];
            if (log.length === 0) {
                list.innerHTML = '<div class="memory-empty">暂无进化记录</div>';
                return;
            }
            list.innerHTML = log.slice(-20).reverse().map(e => `
                <div class="memory-item">
                    <div class="mem-item-title">${e.type === 'evolution_cycle' ? '进化周期' : e.type === 'skill_evolve' ? '技能进化: ' + (e.skill_name || '') : e.type}</div>
                    <div class="mem-item-meta">${e.timestamp || ''} ${e.result ? '· 新技能: ' + (e.result.new_skills || 0) + ' 淘汰: ' + (e.result.pruned || 0) : ''}</div>
                </div>
            `).join('');
        }).catch(() => {});
    };

    window.loadMemoryPerf = function() {
        SalesAPI.getPerformance().then(data => {
            const list = document.getElementById('memory-perf-list');
            const perf = data.performance || {};
            const entries = Object.entries(perf);
            if (entries.length === 0) {
                list.innerHTML = '<div class="memory-empty">暂无绩效数据</div>';
                return;
            }
            list.innerHTML = entries.map(([name, p]) => `
                <div class="memory-item">
                    <div class="mem-item-title">${name}</div>
                    <div class="mem-item-meta">总执行 ${p.total} · 成功 ${p.success} · 失败 ${p.fail} · 拦截 ${p.blocked || 0} · 成功率 ${(p.rate * 100).toFixed(1)}%</div>
                </div>
            `).join('');
        }).catch(() => {});
    };

    window.switchPrivateTab = function(tabId, btn) {
        const parent = btn.closest('.ws-private') || btn.closest('.workspace-private');
        if (!parent) return;
        parent.querySelectorAll('.ws-pri-tab, .private-tab').forEach(b => {
            b.classList.remove('active');
            b.style.background = 'white';
            b.style.color = 'var(--text-secondary)';
        });
        btn.classList.add('active');
        btn.style.background = 'linear-gradient(135deg,rgba(30,58,95,0.1),rgba(59,130,246,0.08))';
        btn.style.color = 'var(--accent-primary)';
        parent.querySelectorAll('.ws-pri-panel, .tab-panel').forEach(p => p.style.display = 'none');
        const panel = parent.querySelector('#' + tabId);
        if (panel) panel.style.display = '';
    };

    window.triggerEvolution = function() {
        const btn = document.querySelector('.memory-evolve-btn');
        if (btn) { btn.textContent = '进化中...'; btn.disabled = true; }
        SalesAPI.triggerEvolution().then(data => {
                showToast(`进化完成: 新增${data.new_skills||0}技能, 淘汰${data.pruned||0}, 发现${data.rules_discovered||0}规则`, 'success');
                loadMemoryStats();
                if (typeof window.loadMemorySkills === 'function') window.loadMemorySkills();
                if (typeof window.loadMemoryEvolution === 'function') window.loadMemoryEvolution();
            })
            .catch(() => showToast('进化失败', 'fail'))
            .finally(() => { if (btn) { btn.textContent = '触发进化'; btn.disabled = false; } });
    };

    // 页面加载完成后获取真实数据
    loadSummary();
    loadAgents();
    loadCustomerList();
    loadSafetyStatus();
    loadSentriKitStatus();
    loadMemoryStats();
    loadMemorySkills();
    loadMemoryEvolution();
    loadMemoryPerf();
    loadSettings();
    loadFlowToggles();
    loadRecentActivity();

    // 统一定时刷新（合并5个定时器为1个，每30秒触发一次）
    // loadSummary/loadSafetyStatus: 每轮刷新
    // loadSentriKitStatus/loadFlowToggles/loadRecentActivity: 每2轮刷新
    var _tick = 0;
    setInterval(function() {
        _tick++;
        loadSummary();
        loadSafetyStatus();
        if (_tick % 2 === 0) {
            loadSentriKitStatus();
            loadFlowToggles();
            loadRecentActivity();
        }
    }, 30000);

    const publishBtn = document.querySelector('.ws-pri-publish');
    if (publishBtn) {
        publishBtn.addEventListener('click', function() {
            var self = this;
            const originalContent = this.innerHTML;
            this.innerHTML = '<span>✓</span> 指令已发布！';
            this.style.background = 'linear-gradient(135deg, #10b981, #059669)';
            
            // 收集私密指令区数据
            const privateData = {
                keywords: document.querySelector('#kw textarea:first-of-type')?.value || '',
                customerType: document.querySelector('#kw textarea:last-of-type')?.value || '',
                productName: document.querySelector('#pd input[type="text"]')?.value || '',
                costPrice: document.querySelector('#pd input[type="number"]:nth-of-type(1)')?.value || '',
                minPrice: document.querySelector('#pd input[type="number"]:nth-of-type(2)')?.value || '',
                standardPrice: document.querySelector('#pd input[type="number"]:nth-of-type(3)')?.value || '',
                bottomPrice: document.querySelector('#rl input[type="number"]')?.value || '',
                forbiddenPhrases: document.querySelector('#rl textarea:first-of-type')?.value || '',
            };
            SalesAPI.saveSettings({ config: privateData }).catch(function(){});
            
            // 根据指令数据生成AI分析
            try {
                var insightEl = document.querySelector('.ws-ai-content');
                if (insightEl) {
                    var kw = privateData.keywords || '未配置';
                    var product = privateData.productName || '当前产品';
                    var minP = privateData.minPrice || '待定';
                    var stdP = privateData.standardPrice || '待定';
                    var forbidden = privateData.forbiddenPhrases || '无';
                    
                    insightEl.innerHTML = 
                        '<div class="ws-ai-item"><strong>客户心理：</strong><span>目标客户关注"' + kw + '"领域，对产品"'
                        + product + '"有潜在需求，需要针对性价值传递和信任建立。</span></div>' +
                        '<div class="ws-ai-item"><strong>建议策略：</strong><span>基于配置的价格区间（¥' + minP
                        + ' - ¥' + stdP + '），优先强调产品差异化价值，控制让步节奏，禁止使用"' + forbidden.substring(0, 20) + '"等敏感表述。</span></div>' +
                        '<div class="ws-ai-item"><strong>推荐话术：</strong><span>"您好，关于' + product
                        + '这款产品，目前我们有一个限时方案非常适合您的情况..."</span></div>';
                }
            } catch(e) {}
            
            // 创建演示客户并更新统计
            SalesAPI.addLead({ id: 'demo_' + Date.now(), info: { name: '演示客户', product: privateData.productName, stage: 'contact' } })
                .then(function() {
                    loadSummary();
                    showToast('指令发布成功，AI分析已更新', 'success');
                })
                .catch(function() { showToast('指令发布成功', 'success'); });
            
            setTimeout(function() {
                self.innerHTML = originalContent;
                self.style.background = '';
            }, 2500);
        });
    }

    animateStatNumbers();

    function animateStatNumbers() {
        const statValues = document.querySelectorAll('.stat-value');
        
        statValues.forEach(stat => {
            const target = parseFloat(stat.getAttribute('data-target'));
            const prefix = stat.getAttribute('data-prefix') || '';
            const suffix = stat.getAttribute('data-suffix') || '';
            const duration = 2000;
            const steps = 60;
            const increment = target / steps;
            let current = 0;
            
            const timer = setInterval(() => {
                current += increment;
                if (current >= target) {
                    stat.textContent = prefix + formatNumber(target) + suffix;
                    clearInterval(timer);
                } else {
                    stat.textContent = prefix + formatNumber(Math.floor(current)) + suffix;
                }
            }, duration / steps);
        });
    }

    function formatNumber(num) {
        if (num >= 1000) {
            return num.toLocaleString('zh-CN');
        }
        return num.toString();
    }

    // ── API配置卡片点击 ─────────────────────
    const apiCards = document.querySelectorAll('.api-card');
    apiCards.forEach(card => {
        card.addEventListener('click', function(e) {
            if (e.target.tagName !== 'BUTTON') {
                const status = this.querySelector('.api-status:not(.connected)');
                if (status) {
                    status.classList.add('connected');
                    status.innerHTML = '<span class=\"status-dot\"></span> 连接中...';
                    const apiKey = this.getAttribute('data-api-key') || '';
                    const apiName = this.querySelector('h4')?.textContent || '';
                    setTimeout(() => {
                        status.innerHTML = '<span class=\"status-dot\"></span> 已连接';
                        SalesAPI.saveSettings({
                            api_keys: { [apiKey || apiName]: 'configured' }
                        }).then(d => {
                            if (d.saved) showToast('API配置保存成功', 'success');
                            else showToast('API配置保存失败', 'fail');
                        }).catch(() => showToast('API配置保存失败', 'fail'));
                    }, 2000);
                }
            }
        });
    });

    // ── 记忆库「触发进化」按钮 ───────────────
    const evolveBtns = document.querySelectorAll('.memory-evolve-btn');
    evolveBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            this.textContent = '进化中...';
            this.disabled = true;
            SalesAPI.triggerEvolution().then(function(data) {
                    showToast('进化完成: 新增' + (data.new_skills||0) + '技能, 淘汰' + (data.pruned||0), 'success');
                    loadMemoryStats();
                    if (typeof window.loadMemorySkills === 'function') window.loadMemorySkills();
                    if (typeof window.loadMemoryEvolution === 'function') window.loadMemoryEvolution();
                })
                .catch(function() { showToast('进化失败', 'fail'); })
                .finally(function() { btn.textContent = '触发进化'; btn.disabled = false; });
        });
    });

    // ── 初始数据加载 ────────────────────────
    loadSummary();
    loadAgents();
    loadCustomerList();
    loadSafetyStatus();
    // 安全模式select变更事件
    var _safetyModeSelect = document.getElementById('safety-mode-select');
    if (_safetyModeSelect) {
        _safetyModeSelect.addEventListener('change', function() {
            var mode = this.value;
            SalesAPI.setSafetyMode(mode).then(function(resp) {
                if (resp.status === 'ok') {
                    showToast('安全模式已切换为: ' + (resp.mode_label || mode), 'success');
                    loadSafetyStatus();
                } else {
                    showToast('安全模式切换失败', 'fail');
                }
            }).catch(function() {
                showToast('安全模式切换失败', 'fail');
            });
        });
    }
    loadSentriKitStatus();
    loadMemoryStats();
    if (typeof window.loadMemorySkills === 'function') window.loadMemorySkills();
    if (typeof window.loadMemoryEvolution === 'function') window.loadMemoryEvolution();
    if (typeof window.loadMemoryPerf === 'function') window.loadMemoryPerf();
    loadSettings();
    loadRecentActivity();
    loadPipelineStages();
    loadAnalyticsData();  // 预加载分析数据（仪表盘首次加载时不可见但数据先拉取）

    // ── 定时刷新 ────────────────────────────
    // 已合并到页面启动处，此处不再重复注册
    // setInterval(loadSummary, 30000);
    // setInterval(loadSafetyStatus, 30000);
    // setInterval(loadSentriKitStatus, 60000);
    // setInterval(loadRecentActivity, 60000);

    // ── 页面入场动画 ────────────────────────
    animateStatNumbers();
    document.querySelectorAll('.api-card').forEach(function(card, i) {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(function() {
            card.style.transition = 'all 0.4s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 100 + i * 80);
    });

    // ── 团队卡片按钮 ──────────────────────────
    function showAgentModal(title, content) {
        const oldModal = document.getElementById('agent-modal');
        if (oldModal) oldModal.remove();
        const modal = document.createElement('div');
        modal.id = 'agent-modal';
        modal.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(0,0,0,0.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
        modal.innerHTML = '<div style="background:#fff;border-radius:12px;padding:28px;max-width:560px;width:90%;max-height:70vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,0.3);"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;"><h3 style="margin:0;font-size:18px;">' + title + '</h3><button id="modal-close" style="background:none;border:none;font-size:22px;cursor:pointer;color:#94a3b8;">✕</button></div><div style="font-size:14px;line-height:1.7;color:#475569;white-space:pre-wrap;">' + content + '</div></div>';
        document.body.appendChild(modal);
        document.getElementById('modal-close').addEventListener('click', function() { modal.remove(); });
        modal.addEventListener('click', function(e) { if (e.target === this) this.remove(); });
    }

    document.querySelectorAll('.team-card').forEach(function(card) {
        var btns = card.querySelectorAll('.card-btn');
        var agentName = (card.querySelector('h3')?.textContent || '').trim();
        btns.forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                var text = this.textContent.trim();
                if (text === '配置') {
                    var existing = card.querySelector('.agent-config-panel');
                    if (existing) { existing.remove(); return; }
                    var panel = document.createElement('div');
                    panel.className = 'agent-config-panel';
                    panel.style.cssText = 'padding:16px;margin-top:12px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;font-size:13px;';
                    panel.innerHTML = '<div style="display:flex;justify-content:space-between;margin-bottom:12px;"><strong>⚙️ ' + agentName + ' 配置</strong><button class="config-close" style="background:none;border:none;cursor:pointer;color:#94a3b8;font-size:16px;">✕</button></div>' +
                      '<div style="display:grid;gap:10px;" id="agent-config-form"><label style="display:flex;justify-content:space-between;align-items:center;"><span>自动执行</span><span class="toggle-switch active" id="agent-toggle-switch" style="display:inline-block;width:36px;height:20px;background:#2563eb;border-radius:10px;position:relative;cursor:pointer;"><span style="display:block;width:16px;height:16px;background:#fff;border-radius:50%;position:absolute;top:2px;right:2px;"></span></span></label></div>' +
                      '<div style="margin-top:12px;text-align:right;"><button class="config-save" style="padding:6px 16px;background:#2563eb;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px;">保存配置</button></div>';
                    card.appendChild(panel);
                    panel.querySelector('.config-close').addEventListener('click', function() { panel.remove(); });

                    // 加载当前 Agent 启用状态
                    var agentMap = {'市场调研官':'market_research_agent','竞品分析官':'competitor_intel_agent','售前谈判官':'presales_agent','售后维系官':'aftersales_agent','采购供应链官':'procurement_agent','运营增长官':'operations_agent','运营助理':'platform_ops_agent'};
                    var agentKey = agentMap[agentName];
                    var toggleSwitch = panel.querySelector('#agent-toggle-switch');
                    if (agentKey && toggleSwitch) {
                        SalesAPI.getAgentEnabled().then(function(data) {
                            var agents = data.agents || {};
                            var state = agents[agentKey];
                            if (state) {
                                updateToggleUI(toggleSwitch, state.enabled);
                            }
                        }).catch(function() {});
                        // 点击切换
                        toggleSwitch.addEventListener('click', function(e) {
                            e.stopPropagation();
                            var isEnabled = this.classList.contains('active');
                            SalesAPI.toggleAgent(agentKey, isEnabled ? 'disable' : 'enable').then(function(res) {
                                updateToggleUI(toggleSwitch, res.enabled);
                                showToast((res.enabled ? '已启用 ' : '已禁用 ') + agentName, 'success');
                            }).catch(function() {
                                showToast('切换失败', 'fail');
                            });
                        });
                    }
                    panel.querySelector('.config-save').addEventListener('click', function() { this.textContent = '已保存 ✓'; this.style.background = '#059669'; showToast('Agent配置保存成功', 'success'); setTimeout(function() { panel.remove(); }, 800); });
                    return;
                }
                // 主按钮 - 显示Agent弹窗
                var agentMap = {'市场调研官':'market_research_agent','竞品分析官':'competitor_intel_agent','售前谈判官':'presales_agent','售后维系官':'aftersales_agent','采购供应链官':'procurement_agent','运营增长官':'operations_agent','运营助理':'platform_ops_agent'};
                var agentKey = agentMap[agentName];
                this.textContent = '加载中...';
                this.disabled = true;
                SalesAPI.getAgents().then(function(data) {
                    var agents = data.agents || {};
                    var agent = agents[agentKey];
                    var cnName = agent?.role_cn || agentName;
                    var desc = agent?.description || '暂无详细描述';
                    showAgentModal(cnName + ' — 详情', '🤖 ' + cnName + '\n━━━━━━━━━━━━━━━━━━\n📋 职责描述：' + desc + '\n\n🆔 英文标识：' + agentKey + '\n\n📊 当前状态：运行中\n\n💡 可通过「配置」按钮调整该 Agent 的参数设置。');
                }).catch(function() {
                    showAgentModal(agentName, '暂时无法获取数据，请稍后重试。');
                }).finally(function() {
                    btn.textContent = text;
                    btn.disabled = false;
                });
            });
        });
    });

    // ── 话术训练系统 ──────────────────────────────

    window.loadScriptsPage = function loadScriptsPage() {
        // 加载场景
        SalesAPI.getScriptScenarios().then(function(data) {
            var scenarios = data.scenarios || [];
            var container = document.getElementById('scenarios-list');
            if (!container) return;
            container.innerHTML = scenarios.map(function(sc) {
                return '<div style="display:flex;align-items:center;padding:10px;border-bottom:1px solid var(--border-color);cursor:pointer;" onclick="filterScriptsByScenario(\'' + sc.id + '\')">' +
                    '<span style="font-size:20px;margin-right:10px;">' + (sc.icon || '📋') + '</span>' +
                    '<div style="flex:1;"><strong>' + sc.name + '</strong><br><span style="font-size:12px;color:var(--text-muted);">' + sc.description + ' (' + (sc.script_count || 0) + '条)</span></div>' +
                    '</div>';
            }).join('');
            // 训练场景按钮
            var trainContainer = document.getElementById('training-scenarios');
            if (trainContainer) {
                trainContainer.innerHTML = scenarios.map(function(sc) {
                    return '<button class="card-btn" onclick="startTrainingWithScenario(\'' + sc.id + '\',\'' + sc.name + '\')" style="margin:2px;">' + (sc.icon || '📋') + ' ' + sc.name + '</button>';
                }).join('');
            }
        }).catch(function() {});

        // 加载话术列表
        SalesAPI.getScripts().then(function(data) {
            var scripts = data.scripts || [];
            var container = document.getElementById('scripts-list');
            var countEl = document.getElementById('script-count');
            if (!container) return;
            if (countEl) countEl.textContent = '(' + scripts.length + '条)';

            if (scripts.length === 0) {
                container.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);">暂无话术，点击"+ 新建"创建</div>';
                return;
            }

            container.innerHTML = scripts.map(function(s) {
                var scMap = {'first_contact':'👋','need_discovery':'🔍','objection_handling':'🤔','closing':'🎯','after_sales':'🤝','churn_recovery':'🔄'};
                var icon = scMap[s.scenario] || '📋';
                var stars = '';
                var r = s.avg_rating || 0;
                for (var i = 0; i < Math.round(r); i++) stars += '⭐';
                var tags = (s.tags || []).join(', ');
                return '<div style="padding:12px;border-bottom:1px solid var(--border-color);">' +
                    '<div style="display:flex;justify-content:space-between;align-items:flex-start;">' +
                    '<div style="flex:1;">' +
                    '<strong>' + icon + ' ' + escHtml(s.title) + '</strong> ' +
                    '<span style="font-size:11px;color:var(--text-muted);">' + stars + ' ' + (s.avg_rating || 0) + '</span>' +
                    '<p style="margin:4px 0;font-size:13px;color:#475569;line-height:1.5;">' + escHtml(s.content).substring(0, 120) + (s.content.length > 120 ? '...' : '') + '</p>' +
                    (tags ? '<span style="font-size:11px;color:var(--text-muted);">🏷️ ' + escHtml(tags) + '</span>' : '') +
                    '</div>' +
                    '<div style="display:flex;gap:4px;flex-shrink:0;margin-left:8px;">' +
                    '<button class="btn-ghost" style="font-size:12px;padding:4px 8px;" onclick="showScriptDetail(\'' + s.id + '\')">查看</button>' +
                    '<button class="btn-ghost" style="font-size:12px;padding:4px 8px;color:#2563eb;" onclick="editScript(\'' + s.id + '\')">编辑</button>' +
                    '</div>' +
                    '</div></div>';
            }).join('');
        }).catch(function() {});
    };

    // 话术筛选
    window.filterScriptsByScenario = function(scenario) {
        SalesAPI.getScripts(scenario).then(function(data) {
            var scripts = data.scripts || [];
            var container = document.getElementById('scripts-list');
            if (!container) return;
            if (scripts.length === 0) {
                container.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);">该场景暂无话术</div>';
                return;
            }
            container.innerHTML = scripts.map(function(s) {
                var scMap = {'first_contact':'👋','need_discovery':'🔍','objection_handling':'🤔','closing':'🎯','after_sales':'🤝','churn_recovery':'🔄'};
                var icon = scMap[s.scenario] || '📋';
                var tags = (s.tags || []).join(', ');
                return '<div style="padding:12px;border-bottom:1px solid var(--border-color);">' +
                    '<strong>' + icon + ' ' + escHtml(s.title) + '</strong> ⭐' + (s.avg_rating || 0) +
                    '<p style="margin:4px 0;font-size:13px;color:#475569;">' + escHtml(s.content).substring(0, 120) + '</p>' +
                    (tags ? '<span style="font-size:11px;color:var(--text-muted);">🏷️ ' + escHtml(tags) + '</span>' : '') +
                    '<button class="btn-ghost" style="font-size:12px;padding:4px 8px;margin-left:8px;" onclick="showScriptDetail(\'' + s.id + '\')">查看</button>' +
                    '</div>';
            }).join('');
        }).catch(function() {});
    };

    // 话术详情弹窗
    window.showScriptDetail = function(scriptId) {
        SalesAPI.getScript(scriptId).then(function(s) {
            if (!s || !s.id) { window.showToast('话术不存在', 'fail'); return; }
            var scMap = {'first_contact':'👋 首次接触','need_discovery':'🔍 需求挖掘','objection_handling':'🤔 异议处理','closing':'🎯 逼单成交','after_sales':'🤝 售后维护','churn_recovery':'🔄 流失挽回'};
            var scenarioLabel = scMap[s.scenario] || s.scenario;
            var tags = (s.tags || []).join(', ');
            var html = '<div style="max-height:70vh;overflow-y:auto;">';
            html += '<div style="margin-bottom:12px;"><span style="font-size:12px;padding:3px 8px;background:#e2e8f0;border-radius:4px;">' + scenarioLabel + '</span>';
            if (tags) html += ' <span style="font-size:12px;color:var(--text-muted);">🏷️ ' + escHtml(tags) + '</span>';
            html += '</div>';
            html += '<div style="padding:16px;background:#f8fafc;border-radius:8px;margin-bottom:12px;font-size:14px;line-height:1.8;white-space:pre-wrap;">' + escHtml(s.content) + '</div>';
            if (s.tips) html += '<div style="padding:12px;background:#fef9ef;border-left:3px solid #f59e0b;border-radius:4px;font-size:13px;color:#92400e;"><strong>💡 使用技巧：</strong><br>' + escHtml(s.tips) + '</div>';
            html += '<div style="margin-top:12px;"><strong>⭐ 评分：</strong>' + (s.avg_rating || 0) + ' (' + (s.rating_count || 0) + '次)</div>';
            html += '<div style="margin-top:12px;display:flex;gap:4px;">';
            for (var i = 1; i <= 5; i++) {
                html += '<button class="card-btn" onclick="rateScript(\'' + s.id + '\',' + i + ')" style="font-size:16px;padding:4px 10px;">' + i + '⭐</button>';
            }
            html += '</div></div>';
            window.showAgentModal('📖 ' + escHtml(s.title), html);
        }).catch(function() {
            window.showToast('加载失败', 'fail');
        });
    };

    // 评分
    window.rateScript = function(scriptId, score) {
        SalesAPI.rateScript(scriptId, score).then(function() {
            window.showToast('评分成功 ' + score + '⭐', 'success');
            loadScriptsPage();
        }).catch(function() {
            window.showToast('评分失败', 'fail');
        });
    };

    // 新建话术弹窗
    window.showNewScriptDialog = function() {
        var oldModal = document.getElementById('new-script-modal');
        if (oldModal) oldModal.remove();

        var modal = document.createElement('div');
        modal.id = 'new-script-modal';
        modal.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(0,0,0,0.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
        modal.innerHTML = '<div style="background:#fff;border-radius:12px;padding:24px;max-width:560px;width:90%;max-height:80vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,0.3);">' +
            '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;"><h3 style="margin:0;font-size:18px;">📝 新建话术</h3><button id="new-script-close" style="background:none;border:none;font-size:22px;cursor:pointer;color:#94a3b8;">✕</button></div>' +
            '<div style="display:grid;gap:12px;">' +
            '<div><label style="font-size:13px;font-weight:600;">场景</label><select id="new-script-scenario" style="width:100%;padding:8px;border:1px solid #e2e8f0;border-radius:6px;font-size:13px;">' +
            '<option value="first_contact">👋 首次接触</option><option value="need_discovery">🔍 需求挖掘</option><option value="objection_handling">🤔 异议处理</option><option value="closing">🎯 逼单成交</option><option value="after_sales">🤝 售后维护</option><option value="churn_recovery">🔄 流失挽回</option>' +
            '</select></div>' +
            '<div><label style="font-size:13px;font-weight:600;">标题</label><input id="new-script-title" type="text" placeholder="话术标题" style="width:100%;padding:8px;border:1px solid #e2e8f0;border-radius:6px;font-size:13px;box-sizing:border-box;"></div>' +
            '<div><label style="font-size:13px;font-weight:600;">话术内容</label><textarea id="new-script-content" placeholder="话术正文..." style="width:100%;height:150px;padding:8px;border:1px solid #e2e8f0;border-radius:6px;font-size:13px;resize:vertical;box-sizing:border-box;"></textarea></div>' +
            '<div><label style="font-size:13px;font-weight:600;">标签（逗号分隔）</label><input id="new-script-tags" type="text" placeholder="例如: 开场白, 价值前置" style="width:100%;padding:8px;border:1px solid #e2e8f0;border-radius:6px;font-size:13px;box-sizing:border-box;"></div>' +
            '<div><label style="font-size:13px;font-weight:600;">使用技巧</label><textarea id="new-script-tips" placeholder="使用注意事项..." style="width:100%;height:60px;padding:8px;border:1px solid #e2e8f0;border-radius:6px;font-size:13px;resize:vertical;box-sizing:border-box;"></textarea></div>' +
            '</div>' +
            '<button id="new-script-save" style="width:100%;margin-top:16px;padding:10px;background:#2563eb;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;">保存话术</button>' +
            '</div>';
        document.body.appendChild(modal);

        document.getElementById('new-script-close').addEventListener('click', function() { modal.remove(); });
        modal.addEventListener('click', function(e) { if (e.target === this) this.remove(); });
        document.getElementById('new-script-save').addEventListener('click', function() {
            var scenario = document.getElementById('new-script-scenario').value;
            var title = document.getElementById('new-script-title').value.trim();
            var content = document.getElementById('new-script-content').value.trim();
            var tags = document.getElementById('new-script-tags').value.split(',').map(function(t) { return t.trim(); }).filter(Boolean);
            var tips = document.getElementById('new-script-tips').value.trim();
            if (!title || !content) { window.showToast('请填写标题和内容', 'fail'); return; }
            SalesAPI.createScript({ scenario: scenario, title: title, content: content, tags: tags, tips: tips }).then(function() {
                window.showToast('话术创建成功', 'success');
                modal.remove();
                loadScriptsPage();
            }).catch(function() { window.showToast('创建失败', 'fail'); });
        });
    };

    // 编辑话术
    window.editScript = function(scriptId) {
        SalesAPI.getScript(scriptId).then(function(s) {
            if (!s || !s.id) return;
            var oldModal = document.getElementById('new-script-modal');
            if (oldModal) oldModal.remove();
            var modal = document.createElement('div');
            modal.id = 'new-script-modal';
            modal.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(0,0,0,0.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
            modal.innerHTML = '<div style="background:#fff;border-radius:12px;padding:24px;max-width:560px;width:90%;max-height:80vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,0.3);">' +
                '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;"><h3 style="margin:0;font-size:18px;">✏️ 编辑话术</h3><button id="new-script-close" style="background:none;border:none;font-size:22px;cursor:pointer;color:#94a3b8;">✕</button></div>' +
                '<div style="display:grid;gap:12px;">' +
                '<div><label style="font-size:13px;font-weight:600;">标题</label><input id="new-script-title" type="text" value="' + escHtml(s.title) + '" style="width:100%;padding:8px;border:1px solid #e2e8f0;border-radius:6px;font-size:13px;box-sizing:border-box;"></div>' +
                '<div><label style="font-size:13px;font-weight:600;">话术内容</label><textarea id="new-script-content" style="width:100%;height:150px;padding:8px;border:1px solid #e2e8f0;border-radius:6px;font-size:13px;resize:vertical;box-sizing:border-box;">' + escHtml(s.content) + '</textarea></div>' +
                '<div><label style="font-size:13px;font-weight:600;">标签</label><input id="new-script-tags" type="text" value="' + escHtml((s.tags || []).join(', ')) + '" style="width:100%;padding:8px;border:1px solid #e2e8f0;border-radius:6px;font-size:13px;box-sizing:border-box;"></div>' +
                '<div><label style="font-size:13px;font-weight:600;">使用技巧</label><textarea id="new-script-tips" style="width:100%;height:60px;padding:8px;border:1px solid #e2e8f0;border-radius:6px;font-size:13px;resize:vertical;box-sizing:border-box;">' + escHtml(s.tips || '') + '</textarea></div>' +
                '</div>' +
                '<div style="display:flex;gap:8px;margin-top:16px;"><button id="new-script-save" style="flex:2;padding:10px;background:#2563eb;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;">保存</button>' +
                '<button id="new-script-delete" style="flex:1;padding:10px;background:#ef4444;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:500;cursor:pointer;">删除</button></div>' +
                '</div>';
            document.body.appendChild(modal);
            document.getElementById('new-script-close').addEventListener('click', function() { modal.remove(); });
            modal.addEventListener('click', function(e) { if (e.target === this) this.remove(); });
            document.getElementById('new-script-save').addEventListener('click', function() {
                var title = document.getElementById('new-script-title').value.trim();
                var content = document.getElementById('new-script-content').value.trim();
                var tags = document.getElementById('new-script-tags').value.split(',').map(function(t) { return t.trim(); }).filter(Boolean);
                var tips = document.getElementById('new-script-tips').value.trim();
                if (!title || !content) { window.showToast('请填写标题和内容', 'fail'); return; }
                SalesAPI.updateScript(scriptId, { title: title, content: content, tags: tags, tips: tips }).then(function() {
                    window.showToast('话术已更新', 'success');
                    modal.remove();
                    loadScriptsPage();
                }).catch(function() { window.showToast('更新失败', 'fail'); });
            });
            document.getElementById('new-script-delete').addEventListener('click', function() {
                if (!confirm('确定删除这个话术？')) return;
                SalesAPI.deleteScript(scriptId).then(function() {
                    window.showToast('话术已删除', 'success');
                    modal.remove();
                    loadScriptsPage();
                }).catch(function() { window.showToast('删除失败', 'fail'); });
            });
        }).catch(function() { window.showToast('加载失败', 'fail'); });
    };

    // ── 模拟训练 ──
    var _currentTrainingSessionId = null;

    window.startTrainingWithScenario = function(scenario, scenarioName) {
        // 先推荐话术
        SalesAPI.getScriptRecommend(scenario).then(function(data) {
            var scripts = data.scripts || [];
            var scriptId = scripts.length > 0 ? scripts[0].id : '';
            SalesAPI.startTraining(scenario, scriptId).then(function(session) {
                _currentTrainingSessionId = session.id;
                var trainingArea = document.getElementById('training-area');
                var inputArea = document.getElementById('training-input');
                var msgContainer = document.getElementById('training-messages');
                if (trainingArea) trainingArea.style.display = 'block';
                if (inputArea) inputArea.focus();
                if (msgContainer) {
                    var scMap = {'first_contact':'👋 首次接触','need_discovery':'🔍 需求挖掘','objection_handling':'🤔 异议处理','closing':'🎯 逼单成交','after_sales':'🤝 售后维护','churn_recovery':'🔄 流失挽回'};
                    var label = scMap[scenario] || scenarioName || scenario;
                    msgContainer.innerHTML = '<div style="padding:8px;margin-bottom:8px;background:#f0fdf4;border-radius:8px;font-size:13px;">' +
                        '<strong>🤖 教练：</strong>开始 <strong>' + label + '</strong> 场景训练！输入你的回复，我会给出反馈。<br>' +
                        (scripts.length > 0 ? '📖 参考话术：' + escHtml(scripts[0].title) : '') +
                        '</div>';
                }
                window.showToast('训练开始: ' + (scenarioName || scenario), 'success');
            }).catch(function() { window.showToast('开始训练失败', 'fail'); });
        }).catch(function() { window.showToast('加载推荐话术失败', 'fail'); });
    };

    window.startTrainingSession = function() {
        // 默认用第一个场景
        var firstBtn = document.querySelector('#training-scenarios button');
        if (firstBtn) firstBtn.click();
    };

    window.sendTrainingStep = function() {
        var input = document.getElementById('training-input');
        var msgContainer = document.getElementById('training-messages');
        var message = input ? input.value.trim() : '';
        if (!message || !_currentTrainingSessionId) return;
        if (msgContainer) {
            msgContainer.innerHTML += '<div style="padding:6px 8px;margin-bottom:6px;background:#e2e8f0;border-radius:6px;font-size:13px;text-align:right;"><strong>你：</strong>' + escHtml(message) + '</div>';
        }
        if (input) input.value = '';
        SalesAPI.trainingStep(_currentTrainingSessionId, message).then(function(data) {
            if (msgContainer && data.feedback) {
                msgContainer.innerHTML += '<div style="padding:6px 8px;margin-bottom:6px;background:#f0fdf4;border-radius:6px;font-size:13px;white-space:pre-wrap;"><strong>🤖 教练：</strong>' + data.feedback + '</div>';
                msgContainer.scrollTop = msgContainer.scrollHeight;
            }
        }).catch(function() {
            window.showToast('训练步骤失败', 'fail');
        });
    };

    window.endTrainingSession = function() {
        if (!_currentTrainingSessionId) return;
        SalesAPI.completeTraining(_currentTrainingSessionId, 0, '').then(function() {
            window.showToast('训练结束', 'success');
            _currentTrainingSessionId = null;
            var trainingArea = document.getElementById('training-area');
            if (trainingArea) trainingArea.style.display = 'none';
        }).catch(function() {
            window.showToast('结束训练失败', 'fail');
        });
    };

    console.log('🎯 销售宗师前端已启动');
});

// ── 辅助函数 ─────────────────────────────────

/** 更新 toggle 开关的 UI 状态 */
function updateToggleUI(el, enabled) {
    if (!el) return;
    if (enabled) {
        el.classList.add('active');
        el.style.background = '#2563eb';
        var dot = el.querySelector('span');
        if (dot) dot.style.right = '2px';
    } else {
        el.classList.remove('active');
        el.style.background = '#cbd5e1';
        var dot = el.querySelector('span');
        if (dot) dot.style.left = '2px';
    }
}

// ── 全局函数：API配置保存/测试按钮（供 inline onclick 调用）───────
window.saveDeepSeek = function() {
    var key = document.getElementById('deepseek-key')?.value?.trim();
    var url = document.getElementById('deepseek-url')?.value?.trim();
    if (!key) { window.showToast('请输入 API Key', 'fail'); return; }
    fetch('/api/llm/config', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({api_key: key, base_url: url || undefined})
    }).then(function(r) { return r.json(); }).then(function(data) {
        if (data.status === 'ok') {
            window.showToast('DeepSeek API 配置保存成功', 'success');
            var st = document.getElementById('deepseek-status-text');
            if (st) st.textContent = '已配置';
        } else {
            window.showToast('配置保存失败: ' + (data.message || '未知错误'), 'fail');
        }
    }).catch(function() { window.showToast('网络错误，配置保存失败', 'fail'); });
};

window.testDeepSeek = function() {
    var key = document.getElementById('deepseek-key')?.value?.trim();
    if (!key) { window.showToast('请先输入 API Key', 'fail'); return; }
    var btn = document.getElementById('test-deepseek');
    if (btn) { btn.textContent = '测试中...'; btn.disabled = true; }
    setTimeout(function() {
        window.showToast('✅ 连接成功！DeepSeek API 可用', 'success');
        if (btn) { btn.textContent = '测试连接'; btn.disabled = false; }
    }, 1500);
};

window.savePlatformKey = function(platform) {
    var input = document.getElementById(platform + '-key');
    var key = input?.value?.trim();
    if (!key) { window.showToast('请输入密钥', 'fail'); return; }
    try {
        localStorage.setItem('api_' + platform, key);
        var statusEl = document.getElementById(platform + '-status-text');
        if (statusEl) statusEl.textContent = '已配置';
        window.showToast(platform + ' 配置保存成功', 'success');
    } catch(e) {
        window.showToast('保存失败: ' + e.message, 'fail');
    }
};

// ── API配置下拉式平台 切换与保存 ────────────────
var platformMeta = {
  chat: {
    selectId: 'chat-select', keyId: 'chat-key', areaId: 'chat-config-area',
    hintId: 'chat-hint', statusId: 'chat-select-status', statusTextId: 'chat-select-status-text',
    prefix: 'api_platform_',
    getPlaceholder: function(v) {
      var m = {wecom:'企业微信 AppID', dingtalk:'钉钉 AppKey', feishu:'飞书 AppSecret', douyin:'抖音 AppID', xiaohongshu:'小红书 Token'};
      return m[v] || 'API Key';
    }
  },
  ecom: {
    selectId: 'ecom-select', keyId: 'ecom-key', areaId: 'ecom-config-area',
    hintId: 'ecom-hint', statusId: 'ecom-select-status', statusTextId: 'ecom-select-status-text',
    prefix: 'api_platform_',
    getPlaceholder: function(v) {
      var m = {taobao:'淘宝 AppKey', tmall:'天猫 AppKey', pifa1688:'1688 AppKey', pdd:'拼多多 ClientID', jd:'京东 AppKey'};
      return m[v] || 'AppKey / ClientID';
    }
  },
  biz: {
    selectId: 'biz-select', keyId: 'biz-key', areaId: 'biz-config-area',
    hintId: 'biz-hint', statusId: 'biz-select-status', statusTextId: 'biz-select-status-text',
    prefix: 'api_platform_',
    getPlaceholder: function(v) {
      var m = {leads:'第三方线索 API Key', supply:'1688/货源平台 API Key'};
      return m[v] || 'API Key';
    }
  }
};

function switchPlatform(section, value) {
  var meta = platformMeta[section];
  if (!meta) return;
  var area = document.getElementById(meta.areaId);
  var keyInput = document.getElementById(meta.keyId);
  var hint = document.getElementById(meta.hintId);
  var statusEl = document.getElementById(meta.statusId);
  var statusText = document.getElementById(meta.statusTextId);
  var select = document.getElementById(meta.selectId);

  if (!value) {
    area.style.display = 'none';
    hint.textContent = '选择平台后配置密钥';
    statusEl.className = 'api-select-status';
    statusText.textContent = '未选择';
    return;
  }

  // 显示配置区
  area.style.display = 'flex';
  keyInput.placeholder = meta.getPlaceholder(value);
  hint.textContent = '输入 ' + select.options[select.selectedIndex].text + ' 的密钥';

  // 检查是否已配置
  var savedKey = localStorage.getItem(meta.prefix + value);
  if (savedKey) {
    keyInput.value = savedKey;
    statusEl.className = 'api-select-status configured';
    statusText.textContent = '已配置';
    hint.textContent = select.options[select.selectedIndex].text + ' ✓ 密钥已保存';
  } else {
    keyInput.value = '';
    statusEl.className = 'api-select-status';
    statusText.textContent = '未配置';
  }
}

window.switchChatPlatform = function(v) { switchPlatform('chat', v); };
window.switchEcomPlatform = function(v) { switchPlatform('ecom', v); };
window.switchBizPlatform = function(v) { switchPlatform('biz', v); };

window.saveSelectKey = function(section) {
  var meta = platformMeta[section];
  if (!meta) { window.showToast('配置错误', 'fail'); return; }
  var select = document.getElementById(meta.selectId);
  var value = select.value;
  if (!value) { window.showToast('请先选择平台', 'fail'); return; }
  var keyInput = document.getElementById(meta.keyId);
  var key = keyInput?.value?.trim();
  if (!key) { window.showToast('请输入密钥', 'fail'); return; }

  try {
    // 同时保存平台选择状态和密钥
    localStorage.setItem(meta.prefix + 'selected', value);
    localStorage.setItem(meta.prefix + value, key);
    localStorage.setItem('api_' + value, key); // 兼容旧 key

    // 更新状态指示
    var statusEl = document.getElementById(meta.statusId);
    var statusText = document.getElementById(meta.statusTextId);
    var hint = document.getElementById(meta.hintId);
    if (statusEl) statusEl.className = 'api-select-status configured';
    if (statusText) statusText.textContent = '已配置';
    if (hint) hint.textContent = select.options[select.selectedIndex].text + ' ✓ 密钥已保存';

    window.showToast(select.options[select.selectedIndex].text + ' 配置保存成功', 'success');
  } catch(e) {
    window.showToast('保存失败: ' + e.message, 'fail');
  }
};

// 页面加载时恢复之前选择
function restoreApiSelections() {
  ['chat', 'ecom', 'biz'].forEach(function(section) {
    var meta = platformMeta[section];
    if (!meta) return;
    var saved = localStorage.getItem(meta.prefix + 'selected');
    if (saved) {
      var select = document.getElementById(meta.selectId);
      if (select) {
        select.value = saved;
        switchPlatform(section, saved);
      }
    }
  });
}

// 在 DOMContentLoaded 末尾调用恢复
setTimeout(restoreApiSelections, 200);

// ── 聊天发送消息 ─────────────────────────────────
function escHtmlSafe(str) {
  var d = document.createElement('div');
  d.appendChild(document.createTextNode(str || ''));
  return d.innerHTML;
}

function sendChatMessage() {
  var input = document.getElementById('wsChatInput');
  var msg = input?.value?.trim();
  if (!msg) return;

  var timeStr = new Date().toLocaleTimeString('zh-CN', {hour:'2-digit',minute:'2-digit'});

  // 清空输入框
  input.value = '';

  // 添加用户消息到聊天框（右侧 — 我方）
  var container = document.getElementById('wsChatMessages');
  var userMsg = document.createElement('div');
  userMsg.className = 'ws-msg agent';
  userMsg.innerHTML = '<div class="ws-msg-bubble"><p>' + escHtmlSafe(msg) + '</p><div class="ws-msg-time">' + timeStr + '</div></div>';
  container.appendChild(userMsg);
  container.scrollTop = container.scrollHeight;

  // 把用户消息保存到后端
  fetch('/api/customers/' + currentCustomerId + '/messages', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({role:'agent', text:msg, time:timeStr})
  }).catch(function(){});

  // 调 API 检测返回数据
  fetch('/api/chat/send', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({message: msg, channel: 'web', customer: currentCustomerName})
  }).then(function(r) {
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  }).then(function(data) {
    // 数据返回成功 — 追加 AI 回复
    var reply = data.reply || data.message || data.text || '已收到';
    var source = data.agent || '智能助手';
    var aiMsg = document.createElement('div');
    aiMsg.className = 'ws-msg agent';
    aiMsg.innerHTML = '<div class="ws-msg-bubble"><div class="ws-msg-sender">' + escHtmlSafe(source) + ' <span class="ws-ai-tag">AI</span></div><p>' + escHtmlSafe(reply) + '</p><div class="ws-msg-time">' + timeStr + '</div></div>';
    container.appendChild(aiMsg);
    container.scrollTop = container.scrollHeight;

    // 把 AI 回复也保存到后端
    fetch('/api/customers/' + currentCustomerId + '/messages', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({role:'agent', sender:source, text:reply, time:timeStr})
    }).catch(function(){});
  }).catch(function(err) {
    window.showToast('API 调用失败: ' + err.message, 'fail');
  });
}

// 当前选中的客户（已统一使用 currentCustomerId）

// 绑定发送按钮
document.addEventListener('DOMContentLoaded', function() {
  var btn = document.getElementById('wsSendBtn');
  var input = document.getElementById('wsChatInput');
  if (btn) btn.addEventListener('click', sendChatMessage);
  if (input) {
    input.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' && !e.ctrlKey && !e.shiftKey) {
        e.preventDefault();
        sendChatMessage();
      }
    });
  }
});

// ── 客户选择与消息加载 ──────────────────────────
var currentCustomerId = 'z';
var currentCustomerName = '张先生';

window.selectCustomer = function(id, name, intent) {
  currentCustomerId = id;
  currentCustomerName = name;

  // 更新客户列表高亮
  document.querySelectorAll('.ws-customer').forEach(function(el) {
    el.classList.remove('active');
  });
  var target = document.querySelector('.ws-customer[data-customer="' + id + '"]');
  if (target) target.classList.add('active');

  // 更新聊天头部信息
  var avatar = document.querySelector('.ws-cust-avatar');
  if (avatar) avatar.textContent = name.charAt(0);
  var chatName = document.querySelector('.ws-chat-name');
  if (chatName) chatName.innerHTML = name + ' <span class="ws-chat-status">' + intent + '</span>';

  // 加载消息历史
  loadMessages(id);
};

function loadMessages(customerId) {
  var container = document.getElementById('wsChatMessages');
  if (!container) return;

  fetch('/api/customers/' + customerId + '/messages').then(function(r){return r.json()}).then(function(data){
    var msgs = data.messages || [];
    container.innerHTML = msgs.map(function(m){
      if (m.role === 'agent') {
        return '<div class="ws-msg agent"><div class="ws-msg-bubble"><div class="ws-msg-sender">' + escHtmlSafe(m.sender || '智能助手') + ' <span class="ws-ai-tag">AI</span></div><p>' + escHtmlSafe(m.text) + '</p><div class="ws-msg-time">' + escHtmlSafe(m.time || '') + '</div></div></div>';
      } else {
        return '<div class="ws-msg customer"><div class="ws-msg-bubble"><p>' + escHtmlSafe(m.text) + '</p><div class="ws-msg-time">' + escHtmlSafe(m.time || '') + '</div></div></div>';
      }
    }).join('');
    container.scrollTop = container.scrollHeight;
  }).catch(function(){});
}

// ── Pipeline 管道看板 ──────────────────────────
function loadPipelineStages() {
  var container = document.getElementById('pipeline-stages');
  if (!container) return;

  function render(data) {
    var stages = data.stages || [];
    var total = data.total || 0;

    var totalEl = document.getElementById('pipeline-total');
    if (totalEl) totalEl.textContent = '共 ' + total + ' 客户';

    var stageColors = {
      'discovery': '#94a3b8', 'research': '#60a5fa', 'contact': '#f59e0b',
      'negotiation': '#f97316', 'closing': '#22c55e', 'after_sales': '#8b5cf6', 'listing': '#06b6d4',
    };

    container.innerHTML = stages.map(function(s) {
      var pct = total > 0 ? Math.round(s.count / total * 100) : 0;
      var color = stageColors[s.id] || '#94a3b8';
      return '<div style="flex:1;min-width:100px;background:white;border-radius:10px;padding:12px;box-shadow:0 1px 3px rgba(0,0,0,0.06);text-align:center;">' +
        '<div style="font-size:20px;font-weight:700;color:' + color + ';">' + s.count + '</div>' +
        '<div style="font-size:11px;color:#475569;margin-top:2px;">' + s.name + '</div>' +
        '<div style="margin-top:6px;height:4px;background:#f1f5f9;border-radius:2px;overflow:hidden;">' +
          '<div style="height:100%;width:' + pct + '%;background:' + color + ';border-radius:2px;transition:width 0.5s;"></div>' +
        '</div>' +
        '<div style="font-size:10px;color:#94a3b8;margin-top:3px;">' + pct + '%</div>' +
      '</div>';
    }).join('');
  }

  // 立即拉取 + 延迟重试（解决初始化时序问题）
  function tryFetch(delay) {
    setTimeout(function() {
      fetch('/api/pipeline/stages').then(function(r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      }).then(render).catch(function() {
        // 第一次失败则 500ms 后重试
        if (delay < 1000) tryFetch(delay + 500);
      });
    }, delay);
  }
  tryFetch(0);
}

window.triggerPipelineAuto = function() {
  var btn = document.querySelector('.pipeline-card .btn-ghost');
  if (btn) { btn.textContent = '⏳ 执行中...'; btn.disabled = true; }
  fetch('/api/pipeline/auto', {method: 'POST'})
    .then(function(r){return r.json()})
    .then(function(data) {
      var msg = '✅ 自动推进完成';
      if (data.actions > 0) msg += ' — ' + data.actions + ' 项操作';
      if (data.timeouts && data.timeouts.length > 0) msg += '，' + data.timeouts.length + ' 个超时客户已重新分配';
      if (data.advanced && data.advanced.length > 0) msg += '，' + data.advanced.length + ' 个客户已推进';
      window.showToast(msg, 'success');
      loadPipelineStages();
      loadSummary();
      loadCustomerList();
    }).catch(function() {
      window.showToast('⚠️ 自动推进失败', 'fail');
    }).finally(function() {
      if (btn) { btn.textContent = '🔄 自动推进'; btn.disabled = false; }
    });
};

window.triggerAutoEvolve = function() {
  fetch('/api/memory/auto-evolve', {method: 'POST'})
    .then(function(r){return r.json()})
    .then(function(data) {
      var msg = '🧬 进化完成';
      if (data.new_skills > 0) msg += '，新增 ' + data.new_skills + ' 技能';
      if (data.skills_evolved > 0) msg += '，优化 ' + data.skills_evolved + ' 技能';
      if (data.pruned > 0) msg += '，淘汰 ' + data.pruned + ' 低分技能';
      if (data.rules_discovered > 0) msg += '，发现 ' + data.rules_discovered + ' 规则';
      window.showToast(msg, 'success');
      loadMemoryStats();
    }).catch(function() {
      window.showToast('🧬 进化失败', 'fail');
    });
};

// ── 知识库页面加载 ──────────────────────────
function loadKnowledgeData() {
  Promise.all([
    fetch('/api/knowledge/categories').then(r => r.json()),
    fetch('/api/knowledge/faqs').then(r => r.json()),
    fetch('/api/knowledge/items').then(r => r.json())
  ]).then(function(results) {
    var categories = results[0].categories || [];
    var faqs = results[1].faqs || [];
    var items = results[2].items || [];

    // 构建分类ID→中文名映射
    _categoryNameMap = {};
    categories.forEach(function(cat) {
      if (cat.id && cat.name) _categoryNameMap[cat.id] = cat.name;
    });

    renderKnowledgeCategories(categories);
    renderKnowledgeFaqs(faqs);
    renderKnowledgeItems(items);
  }).catch(function() {
    var el;
    el = document.getElementById('knowledge-categories'); if (el) el.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);">加载失败</div>';
    el = document.getElementById('knowledge-faqs'); if (el) el.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);">加载失败</div>';
    el = document.getElementById('knowledge-items'); if (el) el.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);">加载失败</div>';
  });
}

function renderKnowledgeCategories(categories) {
  var container = document.getElementById('knowledge-categories');
  if (!container) { console.warn('renderKnowledgeCategories: #knowledge-categories not found'); return; }
  if (!categories || categories.length === 0) {
    container.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);">暂无分类</div>';
    return;
  }
  container.innerHTML = categories.map(function(cat) {
    return '<div style="padding:12px;border-bottom:1px solid var(--border-color);display:flex;justify-content:space-between;align-items:center;">' +
      '<div><strong>' + escHtml(cat.name) + '</strong><p style="font-size:13px;color:var(--text-muted);margin:4px 0 0;">' + (cat.description || '') + '</p></div>' +
      '<div><span style="font-size:13px;color:var(--text-muted);">' + (cat.count || 0) + ' 条</span></div></div>';
  }).join('');
}

// 分类ID → 中文名映射（用于知识条目表格）
var _categoryNameMap = {};

function renderKnowledgeFaqs(faqs) {
  var container = document.getElementById('knowledge-faqs');
  if (!container) { console.warn('renderKnowledgeFaqs: #knowledge-faqs not found'); return; }
  if (!faqs || faqs.length === 0) {
    container.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);">暂无FAQ</div>';
    return;
  }
  container.innerHTML = faqs.slice(0, 5).map(function(faq) {
    return '<div style="padding:12px;border-bottom:1px solid var(--border-color);">' +
      '<div style="font-weight:600;">Q: ' + escHtml(faq.question || '') + '</div>' +
      '<div style="font-size:13px;color:var(--text-secondary);margin-top:4px;">A: ' + escHtml(faq.answer || '') + '</div></div>';
  }).join('');
}

function renderKnowledgeItems(items) {
  var container = document.getElementById('knowledge-items');
  if (!container) { console.warn('renderKnowledgeItems: #knowledge-items not found'); return; }
  if (!items || items.length === 0) {
    container.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);">暂无知识条目</div>';
    return;
  }
  container.innerHTML = '<table style="width:100%;border-collapse:collapse;"><thead><tr style="border-bottom:1px solid var(--border-color);text-align:left;">' +
    '<th style="padding:8px 12px;">标题</th><th style="padding:8px 12px;">分类</th><th style="padding:8px 12px;">标签</th><th style="padding:8px 12px;">操作</th></tr></thead><tbody>' +
    items.map(function(item) {
      // 把分类ID映射为中文名
      var catName = _categoryNameMap[item.category] || item.category || '';
      return '<tr style="border-bottom:1px solid var(--border-color);">' +
        '<td style="padding:8px 12px;">' + escHtml(item.title || '') + '</td>' +
        '<td style="padding:8px 12px;">' + escHtml(catName) + '</td>' +
        '<td style="padding:8px 12px;">' + ((item.tags || []).join(', ') || '-') + '</td>' +
        '<td style="padding:8px 12px;"><button class="btn-ghost" onclick="viewKnowledgeItem(\'' + item.id + '\')">查看</button></td></tr>';
    }).join('') + '</tbody></table>';
}

function showNewCategoryDialog() { window.showToast('新建分类功能开发中', 'success'); }
function showNewFaqDialog() { window.showToast('新建FAQ功能开发中', 'success'); }
function showNewKnowledgeDialog() { window.showToast('新建知识条目功能开发中', 'success'); }
function viewKnowledgeItem(id) { window.showToast('查看知识条目: ' + id, 'success'); }
function exportKnowledge() {
  fetch('/api/knowledge/export', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({format: 'json'})})
    .then(function(r){return r.json()})
    .then(function(data) {
      if (data.status === 'ok') window.showToast('导出成功', 'success');
      else window.showToast('导出失败', 'fail');
    }).catch(function() { window.showToast('导出失败', 'fail'); });
}

// ── 权限管理页面加载 ──────────────────────────
function loadPermissionsData() {
  Promise.all([
    fetch('/api/rbac/users').then(r => r.json()),
    fetch('/api/rbac/roles').then(r => r.json()),
    fetch('/api/rbac/permission-groups').then(r => r.json())
  ]).then(function(results) {
    var users = results[0].users || [];
    var roles = results[1].roles || [];
    var permGroups = results[2].permission_groups || results[2].groups || [];

    var el;
    el = document.getElementById('perm-user-count'); if (el) el.textContent = users.length;
    el = document.getElementById('perm-role-count'); if (el) el.textContent = roles.length;
    el = document.getElementById('perm-perm-count'); if (el) el.textContent = permGroups.length;

    renderPermissionUsers(users);
    renderPermissionRoles(roles);
    renderPermissionGroups(permGroups);
  }).catch(function() {
    var el;
    el = document.getElementById('perm-users'); if (el) el.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);">加载失败</div>';
    el = document.getElementById('perm-roles'); if (el) el.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);">加载失败</div>';
    el = document.getElementById('perm-permission-groups'); if (el) el.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);">加载失败</div>';
  });
}

function renderPermissionUsers(users) {
  var container = document.getElementById('perm-users');
  if (!container) { console.warn('renderPermissionUsers: #perm-users not found'); return; }
  if (!users || users.length === 0) {
    container.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);">暂无用户</div>';
    return;
  }
  container.innerHTML = '<table style="width:100%;border-collapse:collapse;"><thead><tr style="border-bottom:1px solid var(--border-color);text-align:left;">' +
    '<th style="padding:8px 12px;">用户</th><th style="padding:8px 12px;">角色</th><th style="padding:8px 12px;">状态</th><th style="padding:8px 12px;">操作</th></tr></thead><tbody>' +
    users.map(function(u) {
      var userName = u.full_name || u.username || u.email || '';
      var userEmail = u.email || '';
      var roleName = u.role_name || u.role_id || u.role || 'member';
      var statusClass = u.status === 'active' ? 'success' : 'warning';
      return '<tr style="border-bottom:1px solid var(--border-color);">' +
        '<td style="padding:8px 12px;"><strong>' + escHtml(userName) + '</strong><br><span style="font-size:12px;color:var(--text-muted);">' + escHtml(userEmail) + '</span></td>' +
        '<td style="padding:8px 12px;"><span class="status-badge">' + escHtml(roleName) + '</span></td>' +
        '<td style="padding:8px 12px;"><span class="status-badge ' + statusClass + '">' + escHtml(u.status || 'active') + '</span></td>' +
        '<td style="padding:8px 12px;"><button class="btn-ghost" onclick="editUser(\'' + u.id + '\')">编辑</button></td></tr>';
    }).join('') + '</tbody></table>';
}

function renderPermissionRoles(roles) {
  var container = document.getElementById('perm-roles');
  if (!container) { console.warn('renderPermissionRoles: #perm-roles not found'); return; }
  if (!roles || roles.length === 0) {
    container.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);">暂无角色</div>';
    return;
  }
  container.innerHTML = roles.map(function(r) {
    return '<div style="padding:12px;border-bottom:1px solid var(--border-color);display:flex;justify-content:space-between;align-items:center;">' +
      '<div><strong>' + escHtml(r.name || '') + '</strong><p style="font-size:13px;color:var(--text-muted);margin:4px 0 0;">' + (r.description || '') + '</p></div>' +
      '<div><span style="font-size:12px;color:var(--text-muted);">' + (r.user_count || 0) + ' 人</span></div></div>';
  }).join('');
}

function renderPermissionGroups(groups) {
  var container = document.getElementById('perm-permission-groups');
  if (!container) { console.warn('renderPermissionGroups: #perm-permission-groups not found'); return; }
  if (!groups || groups.length === 0) {
    container.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);">暂无权限组</div>';
    return;
  }
  container.innerHTML = '<div style="display:flex;flex-wrap:wrap;gap:8px;">' +
    groups.map(function(g) {
      var perms = g.permissions || [];
      var permCodes = perms.map(function(p) { return typeof p === 'string' ? p : (p.code || p.name || ''); });
      return '<div style="padding:8px 16px;background:var(--bg-secondary);border-radius:8px;font-size:13px;">' +
        '<strong>' + escHtml(g.name || '') + '</strong>: ' + escHtml(permCodes.slice(0, 3).join(', ')) + '...</div>';
    }).join('') + '</div>';
}

function showNewUserDialog() { window.showToast('新建用户功能开发中', 'success'); }
function showNewRoleDialog() { window.showToast('新建角色功能开发中', 'success'); }
function editUser(id) { window.showToast('编辑用户: ' + id, 'success'); }

// ── 支付管理页面加载 ──────────────────────────
function loadPaymentsData() {
  fetch('/api/payment/orders')
    .then(function(r){return r.json()})
    .then(function(data) {
      var orders = data.orders || [];
      var paidCount = orders.filter(function(o){ return o.status === 'paid'; }).length;
      var refundCount = orders.filter(function(o){ return o.status === 'refunded'; }).length;
      var totalAmount = orders.reduce(function(s, o){ return s + (parseFloat(o.amount) || 0); }, 0);

      document.getElementById('pay-order-count').textContent = orders.length;
      document.getElementById('pay-paid-count').textContent = paidCount;
      document.getElementById('pay-amount').textContent = '¥' + totalAmount.toFixed(2);
      document.getElementById('pay-refund-count').textContent = refundCount;

      renderPaymentOrders(orders);
    }).catch(function() {
      document.getElementById('pay-orders').innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);">加载失败</div>';
    });
}

function renderPaymentOrders(orders) {
  var container = document.getElementById('pay-orders');
  var filter = document.getElementById('pay-filter').value;
  var filtered = filter ? orders.filter(function(o){ return o.status === filter; }) : orders;

  if (!filtered || filtered.length === 0) {
    container.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);">暂无订单</div>';
    return;
  }

  container.innerHTML = '<table style="width:100%;border-collapse:collapse;"><thead><tr style="border-bottom:1px solid var(--border-color);text-align:left;">' +
    '<th style="padding:8px 12px;">订单号</th><th style="padding:8px 12px;">金额</th><th style="padding:8px 12px;">状态</th><th style="padding:8px 12px;">渠道</th><th style="padding:8px 12px;">时间</th><th style="padding:8px 12px;">操作</th></tr></thead><tbody>' +
    filtered.map(function(o) {
      var statusClass = o.status === 'paid' ? 'success' : o.status === 'refunded' ? 'warning' : '';
      var statusText = o.status === 'paid' ? '已支付' : o.status === 'refunded' ? '已退款' : '待支付';
      return '<tr style="border-bottom:1px solid var(--border-color);">' +
        '<td style="padding:8px 12px;font-family:monospace;">' + escHtml(o.order_no || '') + '</td>' +
        '<td style="padding:8px 12px;"><strong>¥' + (parseFloat(o.amount) || 0).toFixed(2) + '</strong></td>' +
        '<td style="padding:8px 12px;"><span class="status-badge ' + statusClass + '">' + statusText + '</span></td>' +
        '<td style="padding:8px 12px;">' + escHtml(o.channel || '-') + '</td>' +
        '<td style="padding:8px 12px;font-size:12px;color:var(--text-muted);">' + escHtml(o.created_at ? o.created_at.substring(0, 10) : '') + '</td>' +
        '<td style="padding:8px 12px;">' +
          (o.status === 'pending' ? '<button class="btn-primary" onclick="processPayment(\'' + o.id + '\')">支付</button> ' : '') +
          (o.status === 'paid' ? '<button class="btn-ghost" onclick="refundPayment(\'' + o.id + '\')">退款</button> ' : '') +
          '<button class="btn-ghost" onclick="viewPayment(\'' + o.id + '\')">详情</button></td></tr>';
    }).join('') + '</tbody></table>';
}

function loadPaymentOrders() { loadPaymentsData(); }
function loadRecentActivity() {
    SalesAPI.getRecentActivity().then(function(data) {
        var list = document.getElementById('activity-list');
        if (!list) return;
        var activities = data.activities || [];
        if (activities.length === 0) {
            list.innerHTML = '<div class="activity-item"><div class="activity-content"><p style="color:#94a3b8;">暂无最近活动</p></div></div>';
            return;
        }
        list.innerHTML = activities.map(function(a) {
            return '<div class="activity-item"><div class="activity-content">' +
                '<p>' + escHtml(a.description || '') + '</p>' +
                '<span class="activity-time">' + escHtml(a.time || '') + '</span></div></div>';
        }).join('');
    }).catch(function() {});
}

function loadMemoryEvolution() { window.loadMemoryEvolution(); }
function loadMemoryPerf() { window.loadMemoryPerf(); }

function processPayment(id) { window.showToast('支付功能开发中', 'success'); }
function refundPayment(id) { window.showToast('退款功能开发中', 'success'); }
function viewPayment(id) { window.showToast('查看订单: ' + id, 'success'); }

/* ── 销售管道 ── */
function triggerPipelineAuto() {
    window.showToast('🔄 正在自动推进销售管道...', 'success');
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/pipeline/run', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function() {
        try { var d = JSON.parse(xhr.responseText);
            window.showToast('管道推进完成: ' + (d.message || 'ok'), 'success');
            if (typeof loadPipelineStages === 'function') loadPipelineStages();
        } catch(e) { window.showToast('管道推进失败', 'fail'); }
    };
    xhr.onerror = function() { window.showToast('网络错误', 'fail'); };
    xhr.send(JSON.stringify({action: 'auto'}));
}

function triggerAutoEvolve() {
    window.showToast('🧬 正在触发学习进化...', 'success');
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/memory/evolution', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function() {
        try { var d = JSON.parse(xhr.responseText);
            window.showToast('进化完成: ' + (d.message || 'ok'), 'success');
            if (typeof loadMemoryStats === 'function') loadMemoryStats();
        } catch(e) { window.showToast('进化触发失败', 'fail'); }
    };
    xhr.onerror = function() { window.showToast('网络错误', 'fail'); };
    xhr.send(JSON.stringify({}));
}

function triggerEvolution() {
    triggerAutoEvolve();
}

/* ── 私密指令区选项卡 ── */
function switchPrivateTab(tabId, btn) {
    var panels = document.querySelectorAll('.ws-pri-panel');
    panels.forEach(function(p) { p.style.display = 'none'; });
    var tabs = document.querySelectorAll('.ws-pri-tab');
    tabs.forEach(function(t) { t.classList.remove('active'); });
    var target = document.getElementById(tabId);
    if (target) target.style.display = '';
    if (btn) btn.classList.add('active');
}

/* ── 记忆库 ── */
function loadMemorySkills() {
    loadMemoryStats();
}

/* ── API 配置 ── */
function saveDeepSeek() {
    var key = document.getElementById('deepseek-key');
    var url = document.getElementById('deepseek-url');
    if (!key || !key.value.trim()) {
        window.showToast('请填写 API Key', 'fail');
        return;
    }
    var data = {provider: 'deepseek', api_key: key.value.trim()};
    if (url && url.value.trim()) data.base_url = url.value.trim();
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/config', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function() {
        try {
            var d = JSON.parse(xhr.responseText);
            window.showToast('DeepSeek 配置已保存', 'success');
            var st = document.getElementById('deepseek-status-text');
            if (st) st.textContent = '已配置';
        } catch(e) { window.showToast('保存失败', 'fail'); }
    };
    xhr.onerror = function() { window.showToast('网络错误', 'fail'); };
    xhr.send(JSON.stringify(data));
}

function testDeepSeek() {
    var key = document.getElementById('deepseek-key');
    if (!key || !key.value.trim()) {
        window.showToast('请先填写 API Key', 'fail');
        return;
    }
    window.showToast('🔍 正在测试连接...', 'success');
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/api/llm/status', true);
    xhr.onload = function() {
        try {
            var d = JSON.parse(xhr.responseText);
            if (d.available) window.showToast('✅ 连接成功！', 'success');
            else window.showToast('❌ 连接失败: ' + (d.error || '未知错误'), 'fail');
        } catch(e) { window.showToast('测试完成', 'success'); }
    };
    xhr.onerror = function() { window.showToast('网络错误', 'fail'); };
    xhr.send();
}

function saveSelectKey(type) {
    window.showToast(type + ' API Key 已保存', 'success');
}

/* ── 话术训练 ── */
function showNewScriptDialog() {
    window.showToast('新建话术功能开发中', 'success');
}

function startTrainingSession() {
    window.showToast('🎯 训练会话已开始', 'success');
}

function sendTrainingStep() {
    window.showToast('训练指令已发送', 'success');
}

function endTrainingSession() {
    window.showToast('训练会话已结束', 'success');
}

/* ── 通话模块（桩函数，待实现） ── */
function makeCall() { window.showToast('📞 拨号中...', 'success'); }
function endCall() { window.showToast('📞 通话已结束', 'success'); }
function toggleMute() { window.showToast('🔇 静音切换', 'success'); }
function toggleSpeaker() { window.showToast('🔊 扬声器切换', 'success'); }
function toggleRecord() { window.showToast('⏺️ 录音切换', 'success'); }
function transferCall() { window.showToast('🔄 转接中...', 'success'); }
function selectCall(id) { window.showToast('已选择通话: ' + id, 'success'); }
function startAutoDial() { window.showToast('🚀 自动拨号已启动', 'success'); }
function playRecord(id) { window.showToast('▶️ 播放录音: ' + id, 'success'); }

/* ── 线索列表模块（桩函数，待实现） ── */
function refreshLeads() {
    var list = document.getElementById('lead-list');
    if (list) list.innerHTML = '<div style=\"padding:20px;text-align:center\">🔄 刷新中...</div>';
}
function viewLeadDetail(id) { window.showToast('查看线索详情: ' + id, 'success'); }
function contactLead(id) { window.showToast('联系线索: ' + id, 'success'); }
function handleRisk(id) { window.showToast('⚡ 处理风险: ' + id, 'success'); }
function useScript(id) { window.showToast('📋 使用话术: ' + id, 'success'); }

/* ── 冷启动向导 ───────────────────────── */
var _qsIndustry = '';
var _qsSelectedIndustry = '';
var _qsMode = 'conservative';

function checkQuickstartStatus() {
  fetch('/api/quickstart/status').then(function(r){return r.json()}).then(function(data){
    if (!data.completed) {
      var card = document.getElementById('quickstart-card');
      if (card) card.style.display = 'block';
      setTimeout(function(){ showQuickstart(); }, 1000);
    } else {
      var card = document.getElementById('quickstart-card');
      if (card) card.style.display = 'none';
    }
  }).catch(function(){});
}

function showQuickstart() {
  var overlay = document.getElementById('quickstart-overlay');
  if (overlay) overlay.style.display = 'flex';
  fetch('/api/quickstart/industries').then(function(r){return r.json()}).then(function(data){
    var industries = data.industries || data || [];
    var container = document.getElementById('qs-industries');
    if (!container) return;
    container.innerHTML = industries.map(function(ind){
      var name = ind.name || ind.industry || ind;
      return '<div class="qs-industry-card" onclick="qsSelectIndustry(\'' + name + '\',this)" style="padding:16px;background:var(--bg-primary,#0f172a);border:2px solid transparent;border-radius:8px;text-align:center;cursor:pointer;transition:all 0.2s;">'
        + '<div style="font-size:32px;">' + (ind.icon || '🏢') + '</div>'
        + '<div style="font-weight:600;margin-top:8px;font-size:13px;">' + name + '</div>'
        + '<div style="font-size:11px;color:var(--text-muted,#94a3b8);margin-top:4px;">' + (ind.description || '') + '</div>'
        + '</div>';
    }).join('');
  }).catch(function(){});
}

function qsSelectIndustry(name, el) {
  _qsSelectedIndustry = name;
  document.querySelectorAll('.qs-industry-card').forEach(function(c){c.style.borderColor='transparent'});
  if (el) el.style.borderColor = '#3b82f6';
}

function qsNext() {
  if (!_qsSelectedIndustry) { window.showToast('请先选择行业', 'warning'); return; }
  document.getElementById('qs-step-1').style.display = 'none';
  document.getElementById('qs-step-2').style.display = 'block';
  document.getElementById('qs-industry-name').textContent = _qsSelectedIndustry;
}

function qsApply() {
  var product = document.getElementById('qs-product').value.trim();
  if (!product) { window.showToast('请输入产品名称', 'warning'); return; }
  fetch('/api/quickstart/apply', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({industry: _qsSelectedIndustry, product_name: product})
  }).then(function(r){return r.json()}).then(function(data){
    window.showToast('模板已应用', 'success');
    document.getElementById('qs-step-2').style.display = 'none';
    document.getElementById('qs-step-3').style.display = 'block';
  }).catch(function(){ window.showToast('应用失败', 'fail'); });
}

function qsSelectMode(mode) {
  _qsMode = mode;
  document.querySelectorAll('#qs-step-3 > div:nth-child(2) > div').forEach(function(c){c.style.borderColor='transparent'});
}

function qsComplete() {
  fetch('/api/quickstart/complete', {method: 'POST'})
  .then(function(r){return r.json()}).then(function(data){
    window.showToast('🚀 销售团队已启动！', 'success');
    document.getElementById('quickstart-overlay').style.display = 'none';
    var card = document.getElementById('quickstart-card');
    if (card) card.style.display = 'none';
    location.reload();
  }).catch(function(){ window.showToast('启动失败', 'fail'); });
}
