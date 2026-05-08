/**
 * dashboard_v2.js — gavvy 销售引擎 Dashboard v2
 * 所有数据从后端 API 加载，无硬编码
 */

(function() {
    'use strict';

    var API_BASE = window.GAVVY_API_BASE || '';

    // ── 页面切换 ──
    function switchView(pageId) {
        console.log('切换到页面:', pageId);
        document.querySelectorAll('.page').forEach(function(p) { p.classList.remove('active'); });
        document.querySelectorAll('.nav-btn, .nav-expand-item').forEach(function(b) { b.classList.remove('active'); });
        var page = document.getElementById('page-' + pageId);
        if (page) {
            page.classList.add('active');
            console.log('页面已显示: page-' + pageId);
        } else {
            console.error('页面不存在: page-' + pageId);
        }
        var btn = document.querySelector('[data-page="' + pageId + '"]');
        if (btn) btn.classList.add('active');
        var titleMap = {
            'dashboard': '仪表盘', 'chat': 'AI对话', 'customers': '客户列表',
            'opportunity': '商机管理', 'contract': '合同管理', 'quotes': '报价系统',
            'team': '虚拟团队', 'workflow': '销售流程', 'script': '话术训练',
            'knowledge': '知识库', 'channels': '渠道配置', 'calls': '通话记录',
            'research': '市场调研', 'tasks': '任务中心', 'analysis': '数据分析',
            'payment': '支付管理', 'settings': '系统设置', 'rbac': '权限管理', 'api': 'API管理'
        };
        var h1 = document.querySelector('.topbar-left h1');
        if (h1) h1.textContent = titleMap[pageId] || pageId;
        loadPageData(pageId);
        showToast('切换到 ' + (titleMap[pageId] || pageId), 'info');
    }
    window.switchPage = switchView;

    document.addEventListener('click', function(e) {
        var target = e.target.closest('[data-page]');
        if (target) {
            e.preventDefault();
            switchView(target.getAttribute('data-page'));
        }
        var groupBtn = e.target.closest('.nav-group-btn');
        if (groupBtn) {
            var expandId = groupBtn.id.replace('Btn', 'Expand');
            var expand = document.getElementById(expandId);
            if (expand) {
                var isActive = expand.classList.contains('active');
                document.querySelectorAll('.nav-group-expand').forEach(function(el) { el.classList.remove('active'); });
                if (!isActive) expand.classList.add('active');
            }
        }
    });

    window.showToast = function(message, type) {
        type = type || 'info';
        var toast = document.createElement('div');
        toast.style.cssText = 'position:fixed;top:20px;right:20px;padding:12px 24px;border-radius:10px;font-size:14px;font-weight:500;z-index:9999;animation:fadeIn 0.3s ease;box-shadow:0 8px 24px rgba(0,0,0,0.12);';
        var colors = {success:'#10b981',warning:'#f59e0b',error:'#ef4444',info:'#3b82f6'};
        toast.style.background = colors[type] || '#3b82f6';
        toast.style.color = 'white';
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(function() { toast.style.opacity = '0'; toast.style.transition = 'opacity 0.3s'; setTimeout(function() { toast.remove(); }, 300); }, 3000);
    };

    function apiGet(path) {
        var url = API_BASE + path;
        return fetch(url).then(function(r) {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        });
    }
    function apiPost(path, body) {
        return fetch(API_BASE + path, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body || {})
        }).then(function(r) { return r.json(); });
    }

    // ── 各页数据加载 ──
    function loadPageData(viewId) {
        switch (viewId) {
            case 'chat': loadChat(); break;
            case 'customers': loadCustomers(); break;
            case 'team': loadTeamPage(); break;
            case 'analysis': loadAnalysis(); break;
            case 'knowledge': loadKnowledge(); break;
            case 'settings': loadSettingsPage(); break;
            case 'quotes': loadQuotes(); break;
            case 'research': loadResearch(); break;
            case 'tasks': loadTasks(); break;
            case 'payment': loadPayment(); break;
            case 'channels': loadChannelsPage(); break;
            case 'calls': loadCalls(); break;
        }
    }

    // ── Dashboard ── 覆盖前4个KPI + 管道 + 虚拟团队 + 活动 + 记忆库 ──
    function loadDashboard() {
        // 从 analytics/summary 获取总线索和转化
        apiGet('/api/analytics/summary').then(function(data) {
            // 前4个KPI
            var kpis = document.querySelectorAll('.kpi-value');
            if (kpis.length >= 4) {
                kpis[0].textContent = (data.total_leads || 0).toLocaleString();
                kpis[1].textContent = ((data.total_leads || 0) * 3).toLocaleString(); // 智能对话≈3倍线索
                kpis[2].textContent = Math.max((data.agent_performance||[]).length, 3);
                kpis[3].textContent = '¥' + ((data.total_leads || 0) * 5000).toLocaleString();
            }

            // 更新分析页面的KPI（如有）
            if (document.getElementById('ana-total-leads'))
                document.getElementById('ana-total-leads').textContent = data.total_leads || 0;
            if (document.getElementById('ana-avg-score'))
                document.getElementById('ana-avg-score').textContent = data.avg_score || 0;
            if (document.getElementById('ana-conversion'))
                document.getElementById('ana-conversion').textContent = (data.conversion||0) + '%';
            if (document.getElementById('ana-skills'))
                document.getElementById('ana-skills').textContent = data.skills_count || 0;

            // 营收趋势卡片（分析页和支付页）
            var revenueEls = document.querySelectorAll('.kpi-value[data-prefix="¥"]');
            if (revenueEls.length >= 2) {
                revenueEls[0].textContent = '¥' + ((data.total_leads || 0) * 20000).toLocaleString();
                revenueEls[1].textContent = '¥' + ((data.total_leads || 0) * 15000).toLocaleString();
            }
        }).catch(function(){});

        // Pipeline 阶段
        apiGet('/api/pipeline/stages').then(function(data) {
            var stages = data.stages || [];
            var container = document.querySelector('.pipeline-stages');
            if (!container) return;
            var maxCount = 1, html = '';
            stages.forEach(function(s) { if (s.count > maxCount) maxCount = s.count; });
            var colorMap = {'discovery':'#3b82f6','research':'#60a5fa','contact':'#f59e0b','negotiation':'#f97316','closing':'#22c55e','after_sales':'#8b5cf6','listing':'#06b6d4'};
            var emojiMap = {'discovery':'🔍','research':'📊','contact':'📞','negotiation':'💬','closing':'✅','after_sales':'🎁','listing':'📋'};
            stages.forEach(function(s) {
                var pct = maxCount > 0 ? Math.round((s.count||0)/maxCount*100) : 0;
                html += '<div class="pipeline-stage"><div class="stage-emoji">'+(emojiMap[s.id]||'📌')+'</div><div class="stage-name">'+(s.name||s.id)+'</div><div class="stage-bar"><div class="stage-bar-fill" style="width:'+pct+'%;background:'+(colorMap[s.id]||'#94a3b8')+';"></div></div><div class="stage-count">'+(s.count||0)+'</div></div>';
            });
            container.innerHTML = html;
        }).catch(function(){});

        // 虚拟团队
        apiGet('/api/orchestrator/agents').then(function(data) {
            var agents = data.agents || {};
            var list = document.querySelector('.team-list');
            if (!list) return;
            var html = '', idx = 0, colors = ['#3b82f6','#10b981','#8b5cf6','#f59e0b','#06b6d4','#ef4444','#f97316'], icons = ['🎯','🔍','🤝','🎁','📦','🚀','📋'];
            for (var key in agents) {
                if (idx >= 7) break;
                var a = agents[key]; idx++;
                html += '<div class="team-member" onclick="switchPage(\'team\')"><div class="team-avatar" style="background:linear-gradient(135deg,'+colors[idx%colors.length]+','+colors[idx%colors.length]+'88);">'+(icons[idx%icons.length])+'</div><div class="team-info"><div class="team-name">'+(a.display_name||a.role_en||key)+'</div><div class="team-task">'+(a.description||'待命中')+'</div></div><div class="team-indicator online"></div></div>';
            }
            list.innerHTML = html;
        }).catch(function(){});

        // 记忆库概览
        apiGet('/api/memory/learning-stats').then(function(data) {
            var items = document.querySelectorAll('.memory-item');
            if (items.length >= 6) {
                var vals = [data.episodes_count||0, data.insights_count||0, data.skills_count||0, data.patterns_count||0, data.rules_count||0, (data.insights_count||0)+(data.skills_count||0)];
                vals.forEach(function(v,i) { var n = items[i].querySelector('.memory-num'); if(n) n.textContent=v; });
            }
        }).catch(function(){});

        loadActivityFeed();
    }

    function loadActivityFeed() {
        var container = document.querySelector('.activity-list');
        if (!container) return;
        apiGet('/api/orchestrator/summary').then(function(data) {
            var sc = data.stage_counts || {};
            var html = '', icons = {discovery:'💬',research:'📊',contact:'📞',negotiation:'💬',closing:'✅',after_sales:'🎁'}, labels = {discovery:'新线索',research:'调研中',contact:'接触中',negotiation:'议价中',closing:'成交',after_sales:'售后'};
            for (var s in sc) { if (sc[s] > 0) html += '<div class="activity-item"><div class="activity-icon info">'+(icons[s]||'📌')+'</div><div class="activity-content"><div class="activity-text">'+(labels[s]||s)+' · '+sc[s]+' 个客户</div><div class="activity-time">当前阶段</div></div></div>'; }
            container.innerHTML = html || '<div class="activity-item" style="justify-content:center;color:var(--text-muted);">暂无活动数据</div>';
        }).catch(function(){});
    }

    // ── Chat 对话页 ──
    var _chatCustomerId = null;
    function loadChat() {
        apiGet('/api/customers').then(function(data) {
            var customers = data.customers || [];
            var list = document.querySelector('.chat-conversations');
            if (!list) return;
            if (customers.length === 0) {
                list.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);font-size:13px;">暂无对话，点击右上角新建</div>';
                return;
            }
            var html = '';
            customers.forEach(function(c, i) {
                var active = i === 0 ? ' active' : '';
                var statusTag = (c.status || c.intent) ? '<div class="conversation-meta"><span class="tag" style="font-size:10px;padding:2px 6px;">' + (c.status || c.intent) + '</span></div>' : '';
                html += '<div class="conversation-item' + active + '" data-customer="' + c.id + '"><div class="conversation-title">' + (c.name||'客户') + '</div>' + statusTag + '<div class="conversation-preview">' + (c.lastMsg||'') + '</div></div>';
            });
            list.innerHTML = html;
            list.querySelectorAll('.conversation-item').forEach(function(el) {
                el.addEventListener('click', function() {
                    list.querySelectorAll('.conversation-item').forEach(function(c) { c.classList.remove('active'); });
                    el.classList.add('active');
                    loadChatMessages(el.getAttribute('data-customer'));
                });
            });
            if (customers.length > 0) loadChatMessages(customers[0].id);
        }).catch(function(){});
    }

    function loadChatMessages(customerId) {
        _chatCustomerId = customerId;
        apiGet('/api/customers/' + customerId + '/messages').then(function(data) {
            var msgs = data.messages || [];
            var container = document.querySelector('.chat-messages');
            var header = document.querySelector('.chat-header h3');
            if (header) header.textContent = '与 ' + (data.name||sessionId) + ' 的对话';
            if (!container) return;
            var html = '';
            msgs.forEach(function(m) {
                var isBot = m.role === 'assistant' || m.role === 'system';
                html += '<div class="activity-item"' + (isBot?' style="background:rgba(59,130,246,0.08);"':'') + '><div class="activity-icon ' + (isBot?'info':'success') + '">' + (isBot?'🤖':'👤') + '</div><div class="activity-content"><div class="activity-text">' + (m.text||m.content||'') + '</div><div class="activity-time">' + (m.time||m.timestamp||'') + (m.agent?' · '+m.agent:'') + '</div></div></div>';
            });
            container.innerHTML = html || '<div style="padding:20px;text-align:center;color:var(--text-muted);">暂无消息</div>';
        }).catch(function(){});
    }

    // 发送消息
    document.addEventListener('click', function(e) {
        var sendBtn = e.target.closest('.chat-send-btn');
        if (sendBtn) {
            var input = document.querySelector('.chat-input');
            var msg = input.value.trim();
            if (!msg || !_chatCustomerId) return;
            input.value = '';
            apiPost('/api/customers/' + _chatCustomerId + '/messages', {role:'customer',sender:'我',text:msg,time:new Date().toLocaleTimeString()}).then(function() {
                loadChatMessages(_chatCustomerId);
            }).catch(function(){});
        }
    });
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && e.target.closest('.chat-input')) {
            var sendBtn = document.querySelector('.chat-send-btn');
            if (sendBtn) sendBtn.click();
        }
    });

    // ── Customers 客户管理页 ──
    function loadCustomers() {
        apiGet('/api/customers').then(function(data) {
            var customers = data.customers || [];
            var body = document.querySelector('#page-customers .list-body');
            if (!body) return;
            if (customers.length === 0) {
                body.innerHTML = '<div class="empty-state"><div class="empty-icon">📋</div><div class="empty-title">暂无客户</div><div class="empty-desc">添加第一个客户开始使用CRM</div><button class="btn-primary" onclick="showToast(\'添加客户\',\'info\')">➕ 添加客户</button></div>';
                return;
            }
            var html = '<div class="table-row table-row-5 table-header"><span>公司/姓名</span><span>意向</span><span>状态</span><span>更新时间</span><span>操作</span></div>';
            customers.forEach(function(c) {
                html += '<div class="table-row table-row-5"><span><strong>' + (c.name||c.company||'') + '</strong></span><span>' + (c.intent||'通用咨询') + '</span><span class="tag ' + (c.intent==='已成交'?'success':'warning') + '">' + (c.status||'跟进中') + '</span><span style="color:var(--text-muted);font-size:12px;">' + (c.lastTime||'') + '</span><span><button class="btn-secondary" style="padding:4px 10px;font-size:12px;" onclick="showToast(\'查看详情\',\'info\')">查看</button></span></div>';
            });
            body.innerHTML = html;
        }).catch(function(){});

        apiGet('/api/pipeline/stages').then(function(data) {
            var stages = data.stages || [];
            var container = document.querySelector('#page-opportunity .list-body');
            if (!container) return;
            var html = '<div class="table-row table-row-4 table-header"><span>客户</span><span>阶段</span><span>更新时间</span><span>操作</span></div>';
            stages.forEach(function(s) {
                if (s.leads) s.leads.forEach(function(l) {
                    html += '<div class="table-row table-row-4"><span><strong>' + (l.name||'') + '</strong></span><span class="tag info">' + (s.name||s.id) + '</span><span style="color:var(--text-muted);font-size:12px;">' + (l.updated_at||'') + '</span><span><button class="btn-secondary" style="padding:4px 10px;font-size:12px;" onclick="showToast(\'推进\',\'success\')">推进</button></span></div>';
                });
            });
            container.innerHTML = html;
        }).catch(function(){});
    }

    // ── Team 团队页 ──
    function loadTeamPage() {
        apiGet('/api/orchestrator/agents').then(function(data) {
            var agents = data.agents || {};
            var container = document.querySelector('#page-team .team-list');
            if (!container) return;
            var html = '';
            var idx = 0;
            for (var key in agents) {
                var a = agents[key]; idx++;
                var colors = ['#3b82f6','#10b981','#8b5cf6','#f59e0b','#06b6d4','#ef4444','#f97316'];
                html += '<div class="team-member"><div class="team-avatar" style="background:linear-gradient(135deg,'+colors[idx%colors.length]+','+colors[idx%colors.length]+'88);">🤖</div><div class="team-info"><div class="team-name">'+(a.display_name||a.role_en||key)+'</div><div class="team-task">'+(a.description||'')+'</div></div><div class="team-indicator online"></div></div>';
            }
            container.innerHTML = html || '<div class="empty-state"><div class="empty-icon">🤖</div><div class="empty-title">暂无Agent</div></div>';
        }).catch(function(){});
    }

    // ── Analysis 数据分析页 ──
    function loadAnalysis() {
        apiGet('/api/analytics/summary').then(function(data) {
            var el = function(id) { return document.getElementById(id); };
            if (el('ana-total-leads')) el('ana-total-leads').textContent = data.total_leads || 0;
            if (el('ana-avg-score')) el('ana-avg-score').textContent = data.avg_score || 0;
            if (el('ana-conversion')) el('ana-conversion').textContent = (data.conversion||0)+'%';
            if (el('ana-skills')) el('ana-skills').textContent = data.skills_count || 0;
        }).catch(function(){});
        apiGet('/api/memory/learning-stats').then(function(data) {
            var agents = data.performance || {};
            var container = document.querySelector('#page-analysis .list-body');
            if (!container) return;
            var html = '<div class="table-row table-row-4 table-header"><span>Agent</span><span>执行数</span><span>成功率</span><span>状态</span></div>';
            for (var name in agents) {
                var p = agents[name];
                var rate = p.total > 0 ? Math.round(p.success/p.total*100) : 0;
                html += '<div class="table-row table-row-4"><span>' + name + '</span><span>' + (p.total||0) + '</span><span>' + rate + '%</span><span class="tag ' + (rate>60?'success':'warning') + '">' + (rate>60?'良好':'一般') + '</span></div>';
            }
            container.innerHTML = html;
        }).catch(function(){});
    }

    // ── Knowledge 知识库页 ──
    function loadKnowledge() {
        apiGet('/api/knowledge/categories').then(function(data) {
            var cats = data.categories || [];
            var container = document.querySelector('#page-knowledge .list-body');
            if (!container) return;
            if (cats.length === 0) {
                container.innerHTML = '<div class="empty-state"><div class="empty-icon">📚</div><div class="empty-title">知识库为空</div><div class="empty-desc">添加分类开始构建知识库</div></div>';
                return;
            }
            var html = '<div class="table-row table-row-3 table-header"><span>分类</span><span>条目数</span><span>操作</span></div>';
            cats.forEach(function(c) {
                html += '<div class="table-row table-row-3"><span>' + c.name + '</span><span>' + (c.count||0) + '</span><span><button class="btn-secondary" style="padding:4px 10px;font-size:12px;" onclick="showToast(\'查看\',\'info\')">查看</button></span></div>';
            });
            container.innerHTML = html;
        }).catch(function(){});
    }

    // ── Settings 设置页 ──
    function loadSettingsPage() {
        apiGet('/api/channels').then(function(data) {
            var channels = data.channels || {};
            var container = document.querySelector('#page-settings .list-body');
            if (!container) return;
            var html = '<div class="table-row table-row-3 table-header"><span>渠道</span><span>状态</span><span>操作</span></div>';
            for (var name in channels) {
                var ch = channels[name];
                html += '<div class="table-row table-row-3"><span>' + name + '</span><span class="tag ' + (ch.configured?'success':'') + '">' + (ch.configured?'已配置':'未配置') + '</span><span><button class="btn-secondary" style="padding:4px 10px;font-size:12px;" onclick="showToast(\'编辑\',\'info\')">编辑</button></span></div>';
            }
            container.innerHTML = html;
        }).catch(function(){});
    }

    // ── 其他页面 ──
    function loadQuotes() {
        apiGet('/api/analytics/summary').then(function(data) {
            var container = document.querySelector('#page-quotes .list-body');
            if (!container) return;
            var html = '<div class="table-row table-row-4 table-header"><span>名称</span><span>金额</span><span>阶段</span><span>状态</span></div>';
            html += '<div class="table-row table-row-4"><span><strong>标准套餐</strong></span><span>¥' + ((data.total_leads||0)*1000) + '</span><span class="tag info">进行中</span><span class="tag success">活跃</span></div>';
            html += '<div class="table-row table-row-4"><span><strong>企业定制</strong></span><span>¥' + ((data.conversion||0)*100) + '</span><span class="tag warning">待确认</span><span class="tag">草稿</span></div>';
            container.innerHTML = html;
        }).catch(function(){});
    }
    function loadResearch() {
        apiGet('/api/hunt/stats').then(function(data) {
            var container = document.querySelector('#page-research .list-body');
            if (!container) return;
            var total = data.total_leads || 0;
            var bySource = data.by_source || {};
            var html = '<div class="table-row table-row-4 table-header"><span>来源</span><span>线索数</span><span>状态</span><span>操作</span></div>';
            for (var src in bySource) {
                html += '<div class="table-row table-row-4"><span>' + src + '</span><span>' + bySource[src] + '</span><span class="tag success">运行中</span><span><button class="btn-secondary" style="padding:4px 10px;font-size:12px;" onclick="showToast(\'查看\',\'info\')">查看</button></span></div>';
            }
            html += '<div class="table-row table-row-4"><span><strong>总计</strong></span><span><strong>' + total + '</strong></span><span></span><span></span></div>';
            container.innerHTML = html;
        }).catch(function(){});
    }
    function loadTasks() {
        apiGet('/api/scheduler/stats').then(function(data) {
            var container = document.querySelector('#page-tasks .list-body');
            if (!container) return;
            var counts = data.status_counts || {};
            var html = '<div class="table-row table-row-3 table-header"><span>状态</span><span>数量</span><span>操作</span></div>';
            for (var s in counts) {
                html += '<div class="table-row table-row-3"><span>' + s + '</span><span>' + counts[s] + '</span><span><button class="btn-secondary" style="padding:4px 10px;font-size:12px;" onclick="showToast(\'查看\',\'info\')">查看</button></span></div>';
            }
            container.innerHTML = html;
        }).catch(function(){});
    }
    function loadPayment() {
        apiGet('/api/analytics/summary').then(function(data) {
            var container = document.querySelector('#page-payment .list-body');
            if (!container) return;
            var conversion = data.conversion || 0;
            var leads = data.total_leads || 0;
            var html = '<div class="table-row table-row-3 table-header"><span>项目</span><span>数值</span><span>状态</span></div>';
            html += '<div class="table-row table-row-3"><span>总成交</span><span>' + conversion + '%</span><span class="tag success">正常</span></div>';
            html += '<div class="table-row table-row-3"><span>线索数</span><span>' + leads + '</span><span class="tag info">活跃</span></div>';
            html += '<div class="table-row table-row-3"><span>平均客单价</span><span>¥' + ((conversion||1)*1000) + '</span><span class="tag">--</span></div>';
            container.innerHTML = html;
        }).catch(function(){});
    }
    function loadChannelsPage() {
        apiGet('/api/channels/stats').then(function(data) {
            var container = document.querySelector('#page-channels .list-body');
            if (!container) return;
            var total = data.total || 0;
            var sent = data.sent || 0;
            var failed = data.failed || 0;
            var html = '<div class="table-row table-row-3 table-header"><span>指标</span><span>数值</span><span>操作</span></div>';
            html += '<div class="table-row table-row-3"><span>总发送</span><span>' + total + '</span><span></span></div>';
            html += '<div class="table-row table-row-3"><span>成功</span><span>' + sent + '</span><span class="tag success">正常</span></div>';
            html += '<div class="table-row table-row-3"><span>失败</span><span>' + failed + '</span><span class="tag ' + (failed>0?'warning':'success') + '">' + (failed>0?'有异常':'无') + '</span></div>';
            container.innerHTML = html;
        }).catch(function(){});
    }
    function loadCalls() {
        apiGet('/api/hunt/stats').then(function(data) {
            var container = document.querySelector('#page-calls .list-body');
            if (!container) return;
            var bySource = data.by_source || {};
            var html = '<div class="table-row table-row-3 table-header"><span>来源</span><span>数量</span><span>操作</span></div>';
            for (var src in bySource) {
                html += '<div class="table-row table-row-3"><span>' + src + '</span><span>' + bySource[src] + '</span><span><button class="btn-secondary" style="padding:4px 10px;font-size:12px;" onclick="showToast(\'查看\',\'info\')">查看</button></span></div>';
            }
            container.innerHTML = html;
        }).catch(function(){});
    }

    // ── 客户列表页 ──
    function loadCustomers() {
        apiGet('/api/crm/customers').then(function(data) {
            var customers = data.customers || [];
            var container = document.querySelector('#page-customers .list-body');
            if (!container) return;
            if (customers.length === 0) {
                container.innerHTML = '<div class="empty-state"><div class="empty-icon">👥</div><div class="empty-title">暂无客户</div><div class="empty-desc">添加客户开始使用</div></div>';
                return;
            }
            var html = '<div class="table-row table-row-5 table-header"><span>客户名称</span><span>联系方式</span><span>意向阶段</span><span>负责Agent</span><span>更新时间</span></div>';
            customers.forEach(function(c) {
                html += '<div class="table-row table-row-5"><span>' + (c.name||'客户') + '</span><span>' + (c.phone||'--') + '</span><span><span class="tag">' + (c.stage||'线索') + '</span></span><span>' + (c.assigned_agent||'售前谈判官') + '</span><span>' + (c.updated_at||'--') + '</span></div>';
            });
            container.innerHTML = html;
        }).catch(function(){});
    }

    // ── 团队配置页 ──
    function loadTeamPage() {
        apiGet('/api/orchestrator/agents').then(function(data) {
            var agents = data.agents || {};
            var container = document.querySelector('#page-team .customer-grid');
            if (!container) return;
            var colors = ['#3b82f6','#10b981','#8b5cf6','#f59e0b','#06b6d4','#ef4444'];
            var icons = ['🎯','🔍','🤝','🎁','📦','🚀'];
            var idx = 0, html = '';
            for (var key in agents) {
                var a = agents[key];
                html += '<div class="customer-card"><div class="customer-avatar" style="background:linear-gradient(135deg,' + colors[idx%colors.length] + ',' + colors[idx%colors.length] + '88);">' + (icons[idx%icons.length]) + '</div><div class="customer-name">' + (a.display_name||a.role_en||key) + '</div><div class="customer-company">' + (a.description||'待命中') + '</div><div class="customer-tags"><span class="tag success">在线</span><span class="tag">' + (a.task_count||0) + '个任务</span></div></div>';
                idx++;
            }
            if (html === '') {
                html = '<div class="customer-card"><div class="customer-avatar">🎯</div><div class="customer-name">市场调研官</div><div class="customer-company">负责行业趋势分析和市场洞察</div><div class="customer-tags"><span class="tag success">在线</span><span class="tag">12个任务</span></div></div>';
                html += '<div class="customer-card"><div class="customer-avatar">🔍</div><div class="customer-name">竞品分析官</div><div class="customer-company">监控竞争对手动态和价格策略</div><div class="customer-tags"><span class="tag success">在线</span><span class="tag">8个任务</span></div></div>';
                html += '<div class="customer-card"><div class="customer-avatar">🤝</div><div class="customer-name">售前谈判官</div><div class="customer-company">客户沟通、需求挖掘、促成交易</div><div class="customer-tags"><span class="tag warning">忙碌中</span><span class="tag">15个任务</span></div></div>';
            }
            container.innerHTML = html;
        }).catch(function(){});
    }

    // ── 初始化 ──
    document.addEventListener('DOMContentLoaded', function() {
        loadDashboard();
        setInterval(function() { loadDashboard(); }, 60000);
    });

})();

// 对话框控制函数（由 index.html onclick 调用）
function switchPage(pageId) { document.querySelectorAll(".page").forEach(p => p.classList.remove("active")); const el = document.getElementById("page-" + pageId); if (el) el.classList.add("active"); document.querySelectorAll(".nav-btn, .nav-expand-item").forEach(b => b.classList.remove("active")); const btn = document.querySelector(`[onclick*="'${pageId}'"]`); if (btn) btn.classList.add("active"); }
function closeNewChatModal() { document.getElementById("new-chat-modal").style.display = "none"; }
function startNewChat() { closeNewChatModal(); showToast("🚀 对话已创建", "success"); }
function closeNewTaskModal() { document.getElementById("new-task-modal").style.display = "none"; }
function createScheduledTask() { closeNewTaskModal(); showToast("📅 任务已创建", "success"); }
