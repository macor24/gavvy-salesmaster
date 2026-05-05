"""SentriKit_salesmaster.crm_pkg.crm_pkg.calls — 通话与录音系统

完整的通话管理、录音系统、通话分析功能。
"""

from __future__ import annotations

import uuid
import os
import random
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set


# ── 枚举定义 ────────────────────────────────────────

class CallStatus(Enum):
    """通话状态"""
    INITIATED = "initiated"         # 拨打中
    CONNECTED = "connected"          # 已接通
    MISSED = "missed"               # 未接
    BUSY = "busy"                   # 忙线
    FAILED = "failed"               # 呼损
    COMPLETED = "completed"          # 已完成


class CallDirection(Enum):
    """通话方向"""
    OUTBOUND = "outbound"           # 外呼
    INBOUND = "inbound"             # 呼入


class CallResult(Enum):
    """通话结果"""
    SUCCESS = "success"              # 成功（达成意向）
    FOLLOW_UP = "follow_up"         # 需要跟进
    NO_INTEREST = "no_interest"     # 无意向
    PRICE_TOO_HIGH = "price_too_high"  # 价格问题
    COMPETITOR = "competitor"       # 考虑竞品
    NOT_NOW = "not_now"             # 暂不需要
    OTHER = "other"                 # 其他


# ── 数据类型定义 ────────────────────────────────────────

@dataclass
class CallRecord:
    """通话记录"""
    id: str = ""
    customer_id: str = ""
    customer_name: str = ""
    customer_phone: str = ""
    salesperson: str = ""
    direction: str = "outbound"      # outbound / inbound
    status: str = "initiated"        # 通话状态
    result: str = ""                 # 通话结果
    duration: int = 0                # 通话时长（秒）
    started_at: str = ""              # 开始时间
    ended_at: str = ""               # 结束时间
    recording_id: str = ""           # 关联录音ID
    related_lead_id: str = ""        # 关联线索ID
    notes: str = ""                  # 备注
    tags: List[str] = field(default_factory=list)  # 标签
    score: float = 0.0               # AI 评分
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:12]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not self.created_at:
            self.created_at = now
        if not self.started_at:
            self.started_at = now

    @property
    def duration_text(self) -> str:
        """格式化通话时长"""
        if self.duration < 60:
            return f"{self.duration}秒"
        elif self.duration < 3600:
            mins = self.duration // 60
            secs = self.duration % 60
            return f"{mins}分{secs}秒"
        else:
            hours = self.duration // 3600
            mins = (self.duration % 3600) // 60
            return f"{hours}小时{mins}分钟"

    @property
    def is_connected(self) -> bool:
        """是否已接通"""
        return self.status in ("connected", "completed")

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> "CallRecord":
        return CallRecord(**data)


@dataclass
class Recording:
    """录音"""
    id: str = ""
    call_id: str = ""
    filename: str = ""
    filepath: str = ""
    duration: int = 0               # 录音时长（秒）
    format: str = "mp3"             # 录音格式
    size: int = 0                   # 文件大小（字节）
    transcript: str = ""            # 转写文本
    is_analyzed: bool = False        # 是否已分析
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:12]
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @property
    def duration_text(self) -> str:
        """格式化录音时长"""
        if self.duration < 60:
            return f"{self.duration}秒"
        elif self.duration < 3600:
            mins = self.duration // 60
            secs = self.duration % 60
            return f"{mins}分{secs}秒"
        else:
            hours = self.duration // 3600
            mins = (self.duration % 3600) // 60
            return f"{hours}小时{mins}分钟"

    @property
    def size_text(self) -> str:
        """格式化文件大小"""
        if self.size < 1024:
            return f"{self.size}B"
        elif self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f}KB"
        else:
            return f"{self.size / (1024 * 1024):.1f}MB"

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> "Recording":
        return Recording(**data)


@dataclass
class CallScript:
    """话术模板"""
    id: str = ""
    name: str = ""
    type: str = "opening"           # opening/objection/closing
    content: str = ""
    use_count: int = 0
    success_count: int = 0
    is_active: bool = True
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:12]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    @property
    def success_rate(self) -> float:
        """使用成功率"""
        if self.use_count == 0:
            return 0.0
        return (self.success_count / self.use_count) * 100

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> "CallScript":
        return CallScript(**data)


@dataclass
class CallAnalysis:
    """通话分析"""
    id: str = ""
    call_id: str = ""
    sentiment_score: float = 0.0     # 情感得分（-1 到 1）
    talk_ratio: float = 0.0         # 销售员说话占比
    objection_handled: List[str] = field(default_factory=list)  # 处理的异议
    key_points: List[str] = field(default_factory=list)       # 关键要点
    recommendation: str = ""        # 改进建议
    deal_probability: float = 0.0    # 成交概率
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:12]
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> "CallAnalysis":
        return CallAnalysis(**data)


# ── 通话管理器 ────────────────────────────────────────

class CallManager:
    """通话管理器"""

    def __init__(self, storage_dir: Optional[str] = None):
        from .db import get_calls_kernel
        self.db = get_calls_kernel(storage_dir)

    def initiate_call(self, customer_id: str = "",
                    customer_name: str = "",
                    customer_phone: str = "",
                    salesperson: str = "",
                    related_lead_id: str = "",
                    direction: str = "outbound") -> CallRecord:
        """发起通话（创建通话记录）"""
        call = CallRecord(
            customer_id=customer_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            salesperson=salesperson,
            direction=direction,
            status="initiated",
            related_lead_id=related_lead_id
        )

        calls = self.db.get_calls()
        calls.append(call.to_dict())
        self.db.save_calls(calls)
        return call

    def connect_call(self, call_id: str) -> bool:
        """接通电话"""
        call = self.get_call(call_id)
        if not call:
            return False
        call.status = "connected"
        return self._save_call(call)

    def end_call(self, call_id: str, result: str = "",
                notes: str = "", duration: int = 0) -> bool:
        """结束通话"""
        call = self.get_call(call_id)
        if not call:
            return False

        call.status = "completed"
        call.ended_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        call.result = result
        call.notes = notes
        call.duration = duration

        return self._save_call(call)

    def miss_call(self, call_id: str, reason: str = "") -> bool:
        """标记未接"""
        call = self.get_call(call_id)
        if not call:
            return False
        call.status = "missed"
        call.notes = reason
        call.ended_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self._save_call(call)

    def fail_call(self, call_id: str, reason: str = "") -> bool:
        """标记呼损"""
        call = self.get_call(call_id)
        if not call:
            return False
        call.status = "failed"
        call.notes = reason
        call.ended_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self._save_call(call)

    def get_call(self, call_id: str) -> Optional[CallRecord]:
        """获取通话记录"""
        calls = self.db.get_calls()
        for data in calls:
            if data["id"] == call_id:
                return CallRecord.from_dict(data)
        return None

    def get_calls(self, salesperson: Optional[str] = None,
                 customer_id: Optional[str] = None,
                 status: Optional[str] = None,
                 result: Optional[str] = None,
                 direction: Optional[str] = None) -> List[CallRecord]:
        """获取通话记录列表"""
        calls = [CallRecord.from_dict(c) for c in self.db.get_calls()]

        if salesperson:
            calls = [c for c in calls if c.salesperson == salesperson]
        if customer_id:
            calls = [c for c in calls if c.customer_id == customer_id]
        if status:
            calls = [c for c in calls if c.status == status]
        if result:
            calls = [c for c in calls if c.result == result]
        if direction:
            calls = [c for c in calls if c.direction == direction]

        # 按时间降序
        calls.sort(key=lambda x: x.created_at, reverse=True)
        return calls

    def update_call_score(self, call_id: str, score: float) -> bool:
        """更新通话评分"""
        call = self.get_call(call_id)
        if not call:
            return False
        call.score = score
        return self._save_call(call)

    def link_recording(self, call_id: str, recording_id: str) -> bool:
        """关联录音"""
        call = self.get_call(call_id)
        if not call:
            return False
        call.recording_id = recording_id
        return self._save_call(call)

    def delete_call(self, call_id: str) -> bool:
        """删除通话记录"""
        calls = self.db.get_calls()
        for i, data in enumerate(calls):
            if data["id"] == call_id:
                del calls[i]
                self.db.save_calls(calls)
                return True
        return False

    def _save_call(self, call: CallRecord) -> bool:
        """保存通话记录"""
        calls = self.db.get_calls()
        for i, data in enumerate(calls):
            if data["id"] == call.id:
                calls[i] = call.to_dict()
                self.db.save_calls(calls)
                return True
        return False

    def get_stats(self, salesperson: Optional[str] = None) -> Dict:
        """获取通话统计"""
        calls = self.get_calls(salesperson=salesperson)

        total = len(calls)
        connected = len([c for c in calls if c.is_connected])
        missed = len([c for c in calls if c.status == "missed"])
        failed = len([c for c in calls if c.status == "failed"])

        total_duration = sum(c.duration for c in calls)
        avg_duration = total_duration / connected if connected > 0 else 0

        connect_rate = (connected / total * 100) if total > 0 else 0

        by_result = {}
        for c in calls:
            if c.result:
                by_result[c.result] = by_result.get(c.result, 0) + 1

        by_direction = {
            "outbound": len([c for c in calls if c.direction == "outbound"]),
            "inbound": len([c for c in calls if c.direction == "inbound"])
        }

        return {
            "total": total,
            "connected": connected,
            "missed": missed,
            "failed": failed,
            "connect_rate": round(connect_rate, 2),
            "total_duration": total_duration,
            "avg_duration": round(avg_duration, 2),
            "avg_score": round(sum(c.score for c in calls if c.score > 0) /
                              len([c for c in calls if c.score > 0]), 2)
                              if any(c.score > 0 for c in calls) else 0,
            "by_result": by_result,
            "by_direction": by_direction,
        }


# ── 录音管理器 ────────────────────────────────────────

class RecordingManager:
    """录音管理器"""

    def __init__(self, storage_dir: Optional[str] = None):
        from .db import get_calls_kernel
        self.db = get_calls_kernel(storage_dir)

    def create_recording(self, call_id: str,
                        duration: int = 0,
                        format: str = "mp3") -> Recording:
        """创建录音记录"""
        recording = Recording(
            call_id=call_id,
            filename=f"recording_{call_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{format}",
            filepath=f"recordings/{call_id}/",
            duration=duration,
            format=format,
            size=random.randint(100000, 500000)  # 模拟文件大小
        )

        recordings = self.db.get_recordings()
        recordings.append(recording.to_dict())
        self.db.save_recordings(recordings)
        return recording

    def get_recording(self, recording_id: str) -> Optional[Recording]:
        """获取录音"""
        recordings = self.db.get_recordings()
        for data in recordings:
            if data["id"] == recording_id:
                return Recording.from_dict(data)
        return None

    def get_recordings(self, call_id: Optional[str] = None) -> List[Recording]:
        """获取录音列表"""
        recordings = [Recording.from_dict(r) for r in self.db.get_recordings()]

        if call_id:
            recordings = [r for r in recordings if r.call_id == call_id]

        recordings.sort(key=lambda x: x.created_at, reverse=True)
        return recordings

    def update_transcript(self, recording_id: str, transcript: str) -> bool:
        """更新转写文本"""
        recording = self.get_recording(recording_id)
        if not recording:
            return False
        recording.transcript = transcript
        return self._save_recording(recording)

    def mark_analyzed(self, recording_id: str) -> bool:
        """标记为已分析"""
        recording = self.get_recording(recording_id)
        if not recording:
            return False
        recording.is_analyzed = True
        return self._save_recording(recording)

    def delete_recording(self, recording_id: str) -> bool:
        """删除录音"""
        recordings = self.db.get_recordings()
        for i, data in enumerate(recordings):
            if data["id"] == recording_id:
                del recordings[i]
                self.db.save_recordings(recordings)
                return True
        return False

    def _save_recording(self, recording: Recording) -> bool:
        """保存录音"""
        recordings = self.db.get_recordings()
        for i, data in enumerate(recordings):
            if data["id"] == recording.id:
                recordings[i] = recording.to_dict()
                self.db.save_recordings(recordings)
                return True
        return False

    def get_stats(self) -> Dict:
        """获取录音统计"""
        recordings = [Recording.from_dict(r) for r in self.db.get_recordings()]

        total = len(recordings)
        total_duration = sum(r.duration for r in recordings)
        total_size = sum(r.size for r in recordings)
        analyzed = len([r for r in recordings if r.is_analyzed])

        return {
            "total": total,
            "total_duration": total_duration,
            "total_size": total_size,
            "analyzed": analyzed,
            "analyze_rate": round(analyzed / total * 100, 2) if total > 0 else 0,
        }


# ── 话术模板管理器 ────────────────────────────────────────

class ScriptManager:
    """话术模板管理器"""

    def __init__(self, storage_dir: Optional[str] = None):
        from .db import get_calls_kernel
        self.db = get_calls_kernel(storage_dir)
        self._init_default_scripts()

    def _init_default_scripts(self) -> None:
        """初始化默认话术模板"""
        scripts = self.db.get_scripts()
        if not scripts:
            default_scripts = [
                CallScript(
                    name="标准开场白",
                    type="opening",
                    content="您好，我是{销售员}，来自{公司}。请问您是{客户姓名}先生/女士吗？我了解到您对我们的产品感兴趣，今天想和您简单交流一下..."
                ),
                CallScript(
                    name="处理价格异议",
                    type="objection",
                    content="我理解您的顾虑。很多客户一开始也有同样的想法。但考虑到我们产品的质量和售后服务，实际上是非常划算的..."
                ),
                CallScript(
                    name="处理无需求",
                    type="objection",
                    content="我理解您目前可能不需要。不过我们的产品也在不断更新，如果您以后有任何需要，欢迎随时联系我..."
                ),
                CallScript(
                    name="促成成交",
                    type="closing",
                    content="好的，那我们就先这样定了。我会发送一份详细的方案到您的邮箱，您看可以吗？"
                ),
            ]
            for script in default_scripts:
                self.add_script(script)

    def add_script(self, script: CallScript) -> CallScript:
        """添加话术模板"""
        scripts = self.db.get_scripts()
        scripts.append(script.to_dict())
        self.db.save_scripts(scripts)
        return script

    def get_script(self, script_id: str) -> Optional[CallScript]:
        """获取话术模板"""
        scripts = self.db.get_scripts()
        for data in scripts:
            if data["id"] == script_id:
                return CallScript.from_dict(data)
        return None

    def get_scripts(self, script_type: Optional[str] = None) -> List[CallScript]:
        """获取话术模板列表"""
        scripts = [CallScript.from_dict(s) for s in self.db.get_scripts()]

        if script_type:
            scripts = [s for s in scripts if s.type == script_type]

        return scripts

    def update_script(self, script: CallScript) -> bool:
        """更新话术模板"""
        script.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        scripts = self.db.get_scripts()
        for i, data in enumerate(scripts):
            if data["id"] == script.id:
                scripts[i] = script.to_dict()
                self.db.save_scripts(scripts)
                return True
        return False

    def use_script(self, script_id: str, success: bool = True) -> bool:
        """使用话术模板"""
        script = self.get_script(script_id)
        if not script:
            return False
        script.use_count += 1
        if success:
            script.success_count += 1
        return self.update_script(script)

    def delete_script(self, script_id: str) -> bool:
        """删除话术模板"""
        scripts = self.db.get_scripts()
        for i, data in enumerate(scripts):
            if data["id"] == script_id:
                del scripts[i]
                self.db.save_scripts(scripts)
                return True
        return False


# ── 通话分析管理器 ────────────────────────────────────────

class AnalysisManager:
    """通话分析管理器"""

    def __init__(self, storage_dir: Optional[str] = None):
        from .db import get_calls_kernel
        self.db = get_calls_kernel(storage_dir)

    def analyze_call(self, call_id: str,
                   sentiment_score: float = 0.0,
                   talk_ratio: float = 0.0,
                   objection_handled: Optional[List[str]] = None,
                   key_points: Optional[List[str]] = None,
                   recommendation: str = "",
                   deal_probability: float = 0.0) -> CallAnalysis:
        """创建通话分析"""
        analysis = CallAnalysis(
            call_id=call_id,
            sentiment_score=sentiment_score,
            talk_ratio=talk_ratio,
            objection_handled=objection_handled or [],
            key_points=key_points or [],
            recommendation=recommendation,
            deal_probability=deal_probability
        )

        analyses = self.db.get_analyses()
        analyses.append(analysis.to_dict())
        self.db.save_analyses(analyses)
        return analysis

    def get_analysis(self, call_id: str) -> Optional[CallAnalysis]:
        """获取通话分析"""
        analyses = self.db.get_analyses()
        for data in analyses:
            if data["call_id"] == call_id:
                return CallAnalysis.from_dict(data)
        return None

    def get_analyses(self, min_probability: float = 0.0) -> List[CallAnalysis]:
        """获取分析列表"""
        analyses = [CallAnalysis.from_dict(a) for a in self.db.get_analyses()]

        if min_probability > 0:
            analyses = [a for a in analyses if a.deal_probability >= min_probability]

        return analyses

    def simulate_ai_analysis(self, call_id: str,
                            recording_id: str = "") -> CallAnalysis:
        """模拟 AI 通话分析"""
        # 模拟 AI 分析结果
        sentiment = random.uniform(-0.3, 1.0)
        talk_ratio = random.uniform(0.3, 0.7)
        deal_prob = random.uniform(0.1, 0.9)

        objections = ["价格太高", "需要考虑", "在对比竞品"]
        handled = random.sample(objections, random.randint(0, len(objections)))

        key_points = [
            "客户对产品功能表示认可",
            "价格是主要顾虑",
            "客户希望有更多优惠",
            "表示会考虑后回复"
        ]

        recommendation = "建议跟进，保持联系，可在下次沟通时提供限时优惠"

        analysis = self.analyze_call(
            call_id=call_id,
            sentiment_score=sentiment,
            talk_ratio=talk_ratio,
            objection_handled=handled,
            key_points=key_points,
            recommendation=recommendation,
            deal_probability=deal_prob
        )

        # 更新相关录音为已分析
        if recording_id:
            from .db import get_calls_kernel
            db = get_calls_kernel()
            recordings = db.get_recordings()
            for i, r in enumerate(recordings):
                if r["id"] == recording_id:
                    recordings[i]["is_analyzed"] = True
                    db.save_recordings(recordings)
                    break

        return analysis


# ── 工厂函数 ────────────────────────────────────────

def get_call_manager(storage_dir: Optional[str] = None) -> CallManager:
    """获取通话管理器"""
    return CallManager(storage_dir)

def get_recording_manager(storage_dir: Optional[str] = None) -> RecordingManager:
    """获取录音管理器"""
    return RecordingManager(storage_dir)

def get_script_manager(storage_dir: Optional[str] = None) -> ScriptManager:
    """获取话术管理器"""
    return ScriptManager(storage_dir)

def get_analysis_manager(storage_dir: Optional[str] = None) -> AnalysisManager:
    """获取分析管理器"""
    return AnalysisManager(storage_dir)
