# 📞 通话与录音系统使用文档

## 简介

通话与录音系统是销售宗师（SalesMaster）的核心通信模块，提供完整的通话管理、录音系统、通话分析和话术模板功能。

## 功能架构

```
通话与录音系统
├── 通话管理（CallManager）
│   ├── 发起通话
│   ├── 通话状态跟踪
│   ├── 通话结果记录
│   ├── 通话时长统计
│   └── 通话评分
├── 录音管理（RecordingManager）
│   ├── 录音记录
│   ├── 录音文件管理
│   ├── 转写文本
│   └── 录音分析标记
├── 话术模板（ScriptManager）
│   ├── 开场白模板
│   ├── 异议处理模板
│   ├── 成交话术模板
│   └── 模板效果追踪
└── 通话分析（AnalysisManager）
    ├── AI 情感分析
    ├── 说话占比分析
    ├── 异议处理追踪
    └── 成交概率预测
```

## 快速开始

### 基础使用

```python
from SentriKit_salesmaster.calls import (
    CallManager,
    RecordingManager,
    ScriptManager,
    AnalysisManager,
)

# 创建管理器
cm = CallManager()
rm = RecordingManager()
sm = ScriptManager()
am = AnalysisManager()
```

## 通话管理

### 发起通话

```python
call = cm.initiate_call(
    customer_id="CUST-001",
    customer_name="张三",
    customer_phone="13800138001",
    salesperson="销售员A",
    related_lead_id="lead-001"
)
print(f"发起通话: {call.id}")
```

### 通话状态管理

```python
# 接通电话
cm.connect_call(call.id)

# 结束通话
cm.end_call(
    call.id,
    result="follow_up",
    notes="客户有兴趣，需要进一步跟进",
    duration=300  # 通话时长（秒）
)

# 标记未接
cm.miss_call(call.id, reason="无人接听")

# 标记呼损
cm.fail_call(call.id, reason="线路故障")
```

### 通话结果

通话结果（result）可选值：
- `success` - 成功（达成意向）
- `follow_up` - 需要跟进
- `no_interest` - 无意向
- `price_too_high` - 价格问题
- `competitor` - 考虑竞品
- `not_now` - 暂不需要
- `other` - 其他

### 查询通话

```python
# 获取所有通话
all_calls = cm.get_calls()

# 按销售员筛选
my_calls = cm.get_calls(salesperson="销售员A")

# 按状态筛选
connected = cm.get_calls(status="connected")

# 按结果筛选
successful = cm.get_calls(result="success")

# 按方向筛选
outbound = cm.get_calls(direction="outbound")
```

### 通话统计

```python
stats = cm.get_stats()
print(f"总通话: {stats['total']}")
print(f"已接通: {stats['connected']}")
print(f"未接: {stats['missed']}")
print(f"呼损: {stats['failed']}")
print(f"接通率: {stats['connect_rate']}%")
print(f"平均时长: {stats['avg_duration']}秒")
print(f"平均评分: {stats['avg_score']}")
print(f"按结果统计: {stats['by_result']}")
```

## 录音管理

### 创建录音

```python
recording = rm.create_recording(
    call_id=call.id,
    duration=300,  # 录音时长（秒）
    format="mp3"
)
print(f"录音: {recording.filename}")
```

### 录音操作

```python
# 获取录音
recording = rm.get_recording("recording-id")

# 获取通话的所有录音
recordings = rm.get_recordings(call_id=call.id)

# 更新转写文本
rm.update_transcript(recording.id, "这是通话转写文本...")

# 标记为已分析
rm.mark_analyzed(recording.id)
```

### 录音属性

```python
print(f"文件名: {recording.filename}")
print(f"时长: {recording.duration_text}")   # 格式化：5分0秒
print(f"大小: {recording.size_text}")      # 格式化：1.5MB
print(f"格式: {recording.format}")
print(f"转写: {recording.transcript[:50]}...")
print(f"已分析: {recording.is_analyzed}")
```

### 录音统计

```python
stats = rm.get_stats()
print(f"总录音: {stats['total']}")
print(f"总时长: {stats['total_duration']}秒")
print(f"已分析: {stats['analyzed']}")
print(f"分析率: {stats['analyze_rate']}%")
```

## 话术模板

### 获取默认模板

系统初始化时自动创建标准话术模板：

```python
scripts = sm.get_scripts()
for s in scripts:
    print(f"[{s.type}] {s.name}")
    print(f"  使用: {s.use_count}次, 成功: {s.success_count}次")
    print(f"  成功率: {s.success_rate:.1f}%")
```

### 话术类型

| 类型 | 说明 |
|------|------|
| `opening` | 开场白 |
| `objection` | 异议处理 |
| `closing` | 促成成交 |

### 添加自定义话术

```python
from SentriKit_salesmaster.calls import CallScript

custom = sm.add_script(CallScript(
    name="预约面谈",
    type="closing",
    content="好的，那我们约这周见面详谈吧。您周三还是周四方便？"
))
```

### 使用话术

```python
# 使用话术并标记为成功
sm.use_script(script.id, success=True)

# 使用话术并标记为失败
sm.use_script(script.id, success=False)
```

### 使用话术模板

```python
# 根据类型获取话术
openings = sm.get_scripts(script_type="opening")
objections = sm.get_scripts(script_type="objection")
closings = sm.get_scripts(script_type="closing")

# 使用话术（替换变量）
script = openings[0]
content = script.content.format(
    销售员="销售员A",
    公司="XX公司",
    客户姓名="张三"
)
print(content)
```

## 通话分析

### 创建分析

```python
analysis = am.analyze_call(
    call_id=call.id,
    sentiment_score=0.8,           # 情感得分（-1 到 1）
    talk_ratio=0.65,              # 销售员说话占比
    objection_handled=["价格太高", "需要考虑"],
    key_points=["客户认可产品功能", "价格是主要顾虑"],
    recommendation="建议提供限时优惠",
    deal_probability=0.75          # 成交概率
)
```

### AI 分析模拟

```python
# 模拟 AI 自动分析（基于录音）
analysis = am.simulate_ai_analysis(call.id, recording.id)
print(f"情感得分: {analysis.sentiment_score:.2f}")
print(f"说话占比: {analysis.talk_ratio:.1%}")
print(f"成交概率: {analysis.deal_probability:.1%}")
print(f"处理异议: {', '.join(analysis.objection_handled)}")
print(f"关键要点: {', '.join(analysis.key_points)}")
print(f"改进建议: {analysis.recommendation}")
```

### 获取分析

```python
# 获取单个通话的分析
analysis = am.get_analysis(call.id)

# 获取高成交概率的通话分析
high_prob = am.get_analyses(min_probability=0.7)
```

### 更新通话评分

```python
# 将 AI 分析的成交概率更新到通话记录
cm.update_call_score(call.id, analysis.deal_probability * 100)
```

## 完整示例

```python
from SentriKit_salesmaster.calls import (
    CallManager,
    RecordingManager,
    ScriptManager,
    AnalysisManager,
)

# 创建管理器
cm = CallManager()
rm = RecordingManager()
sm = ScriptManager()
am = AnalysisManager()

# 1. 发起通话
call = cm.initiate_call(
    customer_id="CUST-001",
    customer_name="张三",
    customer_phone="13800138001",
    salesperson="销售员A"
)

# 2. 接通并通话
cm.connect_call(call.id)

# 模拟通话...
duration = 300  # 5分钟

cm.end_call(
    call.id,
    result="follow_up",
    notes="客户对产品有兴趣",
    duration=duration
)

# 3. 创建录音
recording = rm.create_recording(call.id, duration=duration)

# 4. AI 分析通话
analysis = am.simulate_ai_analysis(call.id, recording.id)

# 5. 更新评分
cm.update_call_score(call.id, analysis.deal_probability * 100)

# 6. 使用话术
scripts = sm.get_scripts(script_type="closing")
if scripts:
    sm.use_script(scripts[0].id, success=True)

# 7. 查看统计
print(f"通话统计: {cm.get_stats()}")
print(f"录音统计: {rm.get_stats()}")
```

## 数据类型

### CallStatus（通话状态）
| 状态 | 值 | 说明 |
|------|------|------|
| 拨打中 | initiated | 正在拨打 |
| 已接通 | connected | 已接通 |
| 未接 | missed | 无人接听 |
| 忙线 | busy | 忙线 |
| 呼损 | failed | 拨打失败 |
| 已完成 | completed | 通话结束 |

### CallDirection（通话方向）
| 方向 | 值 | 说明 |
|------|------|------|
| 外呼 | outbound | 主动拨打 |
| 呼入 | inbound | 客户来电 |

### CallResult（通话结果）
| 结果 | 值 | 说明 |
|------|------|------|
| 成功 | success | 达成意向 |
| 跟进 | follow_up | 需要进一步跟进 |
| 无意向 | no_interest | 明确拒绝 |
| 价格问题 | price_too_high | 价格太高 |
| 竞品 | competitor | 在考虑竞品 |
| 暂不需要 | not_now | 暂时不需要 |
| 其他 | other | 其他原因 |

## 最佳实践

### 1. 通话记录
- 每次通话都要记录，便于跟踪客户
- 详细填写备注，方便后续跟进
- 及时标记通话结果

### 2. 录音管理
- 重要通话及时录音
- 定期整理录音文件
- 及时更新转写文本

### 3. 话术优化
- 定期分析话术成功率
- 根据实际效果调整话术
- 复用成功话术

### 4. AI 分析
- 定期查看 AI 分析结果
- 关注成交概率预测
- 根据建议改进销售策略

## 下一步

- 查看完整测试案例：`tests/test_calls.py`
- 学习报价与合同管理：`docs/QUOTES_AND_CONTRACTS.md`

---

**祝您使用愉快！🎉**
