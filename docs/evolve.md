# 进化闭环

销售宗师可通过 SentriKit（SentriKit-toolkit）获得完整的自进化能力。

## 前提

```bash
# 启动 SentriKit API 服务
SentriKit-api --port 8899

# 设置环境变量
export SentriKit_API_URL=http://127.0.0.1:8899
```

## API 端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/evolve/run` | POST | 触发完整进化闭环 |
| `/api/evolve/status` | GET | 进化状态 |
| `/api/evolve/metacog` | POST | 退化检测 |
| `/api/evolve/judge` | POST | 提案评分 |
| `/api/evolve/auto-check` | POST | 自动检查+触发 |

## 标准闭环

```
学习 → 分析 → 判断(Judge) → 进化 → 验证(Verify) → 反射(Reflect) → 清理(Cleanup)
```

## 前端

在 Settings 页面可查看进化状态、触发进化和查看结果。
