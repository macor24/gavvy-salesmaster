# 企业版

企业版包含 AI 销售引擎核心，需商业授权。

## 安装

```bash
pip install tianlong-salesmaster[enterprise]
export SALES_ENTERPRISE=1
```

## 授权方式

| 方式 | 命令 |
|------|------|
| 环境变量 | `export SALES_ENTERPRISE=1` |
| License Key | `export SALES_ENTERPRISE_KEY=SALES-XXXX-XXXX-XXXX` |
| License 文件 | 写入 `~/.tianlong/license.key` |

## 功能对比

| 功能 | 社区版 | 企业版 |
|------|:------:|:------:|
| CRM / 支付 / 权限 / 报价 / 电子签 | ✅ | ✅ |
| 知识库 / 话术训练 / 分析报表 | ✅ | ✅ |
| Web 管理后台 / REST API | ✅ | ✅ |
| AI 销售团队（SalesOrchestrator + 7Agent） | ❌ | ✅ |
| 学习记忆库（MemoryStore + Learner） | ❌ | ✅ |
| 技能进化（SkillEvolver） | ❌ | ✅ |
