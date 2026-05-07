#!/usr/bin/env python3
"""
种子数据脚本 - 向CRM灌入22家真实中国企业客户数据
直接读写JSON文件，不依赖项目import
"""

import json
import os
import random
from datetime import datetime, timedelta

DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "src", "gavvy_salesmaster", "core", "storage", "_data"
)

def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_json(filename, data):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✓ 已写入 {path} ({len(data)} 条)")

def generate_id(prefix):
    """生成类似项目原有风格的ID"""
    import hashlib, time
    raw = f"{prefix}_{time.time_ns()}_{random.randint(1000,9999)}"
    h = hashlib.md5(raw.encode()).hexdigest()[:10]
    return f"{prefix}_{h}"

def make_ts(days_ago=None):
    """生成ISO格式时间戳"""
    if days_ago is None:
        days_ago = random.randint(1, 60)
    dt = datetime.now() - timedelta(days=days_ago, hours=random.randint(0,23), minutes=random.randint(0,59))
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")

def make_ts_range(min_days, max_days):
    dt = datetime.now() - timedelta(days=random.randint(min_days, max_days),
                                     hours=random.randint(0,23),
                                     minutes=random.randint(0,59))
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")

# ========== 22家真实中国企业数据 ==========

CUSTOMERS = [
    # --- lead (8) ---
    {
        "company": "北京智言科技有限公司",
        "industry": "AI",
        "stage": "lead",
        "name": "林志远",
        "phone": "13811668899",
        "email": "lin.zhiyuan@zhiyan-tech.cn",
        "contact_name": "林志远",
        "contact_role": "技术VP",
        "contact_phone2": "13601234567",
        "contact_email2": "lin.zhiyuan@zhiyan-tech.cn",
        "deal_title": "AI智能客服平台标准版",
        "deal_amount": 88000,
        "deal_stage": "discovery",
        "act_type": "call",
        "act_title": "初次电话沟通",
        "act_content": "客户对AI智能客服平台感兴趣，约下周产品演示"
    },
    {
        "company": "上海云创信息技术有限公司",
        "industry": "云计算",
        "stage": "lead",
        "name": "陈思远",
        "phone": "13917654321",
        "email": "chensiyuan@cloudcreate.cn",
        "contact_name": "陈思远",
        "contact_role": "IT总监",
        "contact_phone2": "13811223344",
        "contact_email2": "chensiyuan@cloudcreate.cn",
        "deal_title": "云原生基础设施咨询",
        "deal_amount": 150000,
        "deal_stage": "discovery",
        "act_type": "email",
        "act_title": "发送产品资料",
        "act_content": "已发送云原生解决方案白皮书，客户表示会内部讨论"
    },
    {
        "company": "深圳前海数据智能有限公司",
        "industry": "大数据",
        "stage": "lead",
        "name": "黄婉婷",
        "phone": "15818654321",
        "email": "huangwt@qianhaidata.com",
        "contact_name": "黄婉婷",
        "contact_role": "数据部门负责人",
        "contact_phone2": "15987654321",
        "contact_email2": "huangwt@qianhaidata.com",
        "deal_title": "大数据分析平台企业版",
        "deal_amount": 280000,
        "deal_stage": "discovery",
        "act_type": "meeting",
        "act_title": "需求初步沟通会",
        "act_content": "客户正在做数据平台选型，我司入围前三候选"
    },
    {
        "company": "杭州领航电子商务有限公司",
        "industry": "电商",
        "stage": "lead",
        "name": "张明辉",
        "phone": "13605718899",
        "email": "zhangmh@linghang-ec.com",
        "contact_name": "张明辉",
        "contact_role": "运营总监",
        "contact_phone2": "13757110022",
        "contact_email2": "zhangmh@linghang-ec.com",
        "deal_title": "电商智能运营系统",
        "deal_amount": 120000,
        "deal_stage": "discovery",
        "act_type": "call",
        "act_title": "电话回访",
        "act_content": "客户双11前急需上线智能运营工具，时间紧迫"
    },
    {
        "company": "广州物联智造科技有限公司",
        "industry": "物联网",
        "stage": "lead",
        "name": "赵建国",
        "phone": "13711223344",
        "email": "zhaojg@wulianzhizao.cn",
        "contact_name": "赵建国",
        "contact_role": "智能制造事业部总经理",
        "contact_phone2": "13600001111",
        "contact_email2": "zhaojg@wulianzhizao.cn",
        "deal_title": "工业物联网数据采集平台",
        "deal_amount": 350000,
        "deal_stage": "discovery",
        "act_type": "email",
        "act_title": "发送方案建议书",
        "act_content": "客户已确认收到方案，下周安排技术交流"
    },
    {
        "company": "北京金融云科技有限公司",
        "industry": "金融科技",
        "stage": "lead",
        "name": "王思涵",
        "phone": "15810556677",
        "email": "wangsh@fincloud.cn",
        "contact_name": "王思涵",
        "contact_role": "风控技术负责人",
        "contact_phone2": "13910203040",
        "contact_email2": "wangsh@fincloud.cn",
        "deal_title": "智能风控系统基础版",
        "deal_amount": 200000,
        "deal_stage": "discovery",
        "act_type": "call",
        "act_title": "初次电话沟通",
        "act_content": "客户希望替换现有风控系统，预算约20万"
    },
    {
        "company": "上海数字营销策划有限公司",
        "industry": "数字营销",
        "stage": "lead",
        "name": "周雅文",
        "phone": "13621668899",
        "email": "zhouyw@digitalmkt.cn",
        "contact_name": "周雅文",
        "contact_role": "创始人兼CEO",
        "contact_phone2": "13917660088",
        "contact_email2": "zhouyw@digitalmkt.cn",
        "deal_title": "全渠道营销自动化平台",
        "deal_amount": 95000,
        "deal_stage": "discovery",
        "act_type": "meeting",
        "act_title": "产品演示",
        "act_content": "CEO亲自参会，对自动化营销模块非常认可"
    },
    {
        "company": "成都天府软件技术有限公司",
        "industry": "AI",
        "stage": "lead",
        "name": "刘浩然",
        "phone": "13608089977",
        "email": "liuhr@tianfu-soft.cn",
        "contact_name": "刘浩然",
        "contact_role": "CTO",
        "contact_phone2": "13880006666",
        "contact_email2": "liuhr@tianfu-soft.cn",
        "deal_title": "企业级AI应用开发框架",
        "deal_amount": 180000,
        "deal_stage": "discovery",
        "act_type": "email",
        "act_title": "发送技术白皮书",
        "act_content": "CTO要求发送详细技术文档后再约时间"
    },

    # --- prospect (6) ---
    {
        "company": "武汉长江大数据研究院",
        "industry": "大数据",
        "stage": "prospect",
        "name": "李秋实",
        "phone": "13807138899",
        "email": "liqs@changjiang-bd.com",
        "contact_name": "李秋实",
        "contact_role": "副院长",
        "contact_phone2": "15927110011",
        "contact_email2": "liqs@changjiang-bd.com",
        "deal_title": "大数据分析与可视化平台",
        "deal_amount": 420000,
        "deal_stage": "proposal",
        "act_type": "meeting",
        "act_title": "技术方案汇报",
        "act_content": "副院长带队参会，对技术方案提出了一些改进意见"
    },
    {
        "company": "苏州工业园区智能科技有限公司",
        "industry": "物联网",
        "stage": "prospect",
        "name": "孙伟",
        "phone": "13862118899",
        "email": "sunwei@szpark-ai.cn",
        "contact_name": "孙伟",
        "contact_role": "技术总监",
        "contact_phone2": "13776001122",
        "contact_email2": "sunwei@szpark-ai.cn",
        "deal_title": "园区智能化管理平台",
        "deal_amount": 500000,
        "deal_stage": "proposal",
        "act_type": "meeting",
        "act_title": "园区智能化方案评审",
        "act_content": "客户对方案整体满意，需要调整报价结构"
    },
    {
        "company": "北京新零售科技有限公司",
        "industry": "电商",
        "stage": "prospect",
        "name": "杨晓芸",
        "phone": "13810998877",
        "email": "yangxy@newretail.cn",
        "contact_name": "杨晓芸",
        "contact_role": "商品总监",
        "contact_phone2": "13621110099",
        "contact_email2": "yangxy@newretail.cn",
        "deal_title": "新零售全渠道管理系统",
        "deal_amount": 260000,
        "deal_stage": "proposal",
        "act_type": "call",
        "act_title": "商务条件沟通",
        "act_content": "客户有竞品也在接触，需要加快推动"
    },
    {
        "company": "深圳星辰云计算有限公司",
        "industry": "云计算",
        "stage": "prospect",
        "name": "何星辰",
        "phone": "13632668899",
        "email": "hexc@starcloud.cn",
        "contact_name": "何星辰",
        "contact_role": "CEO",
        "contact_phone2": "13823231100",
        "contact_email2": "hexc@starcloud.cn",
        "deal_title": "混合云管理平台",
        "deal_amount": 380000,
        "deal_stage": "proposal",
        "act_type": "meeting",
        "act_title": "CEO级别商务会谈",
        "act_content": "CEO意向明确，要求出具正式报价"
    },
    {
        "company": "杭州趣链科技有限公司",
        "industry": "金融科技",
        "stage": "prospect",
        "name": "顾云飞",
        "phone": "13606818899",
        "email": "guyf@qulian-tech.cn",
        "contact_name": "顾云飞",
        "contact_role": "区块链技术VP",
        "contact_phone2": "15958110022",
        "contact_email2": "guyf@qulian-tech.cn",
        "deal_title": "供应链金融区块链平台",
        "deal_amount": 450000,
        "deal_stage": "proposal",
        "act_type": "email",
        "act_title": "发送技术方案V2",
        "act_content": "根据客户反馈已修改方案，等待内部评审"
    },
    {
        "company": "北京智汇数字营销有限公司",
        "industry": "数字营销",
        "stage": "prospect",
        "name": "唐诗涵",
        "phone": "13910229988",
        "email": "tsh@zhihui-digital.cn",
        "contact_name": "唐诗涵",
        "contact_role": "市场总监",
        "contact_phone2": "13810007766",
        "contact_email2": "tsh@zhihui-digital.cn",
        "deal_title": "智能营销数据分析平台",
        "deal_amount": 160000,
        "deal_stage": "proposal",
        "act_type": "call",
        "act_title": "方案细节确认",
        "act_content": "客户对数据看板功能有定制需求"
    },

    # --- qualified (4) ---
    {
        "company": "南京紫金山人工智能研究院",
        "industry": "AI",
        "stage": "qualified",
        "name": "徐明远",
        "phone": "13851889977",
        "email": "xumy@zjs-ai.cn",
        "contact_name": "徐明远",
        "contact_role": "副院长",
        "contact_phone2": "13913886600",
        "contact_email2": "xumy@zjs-ai.cn",
        "deal_title": "NLP自然语言处理平台",
        "deal_amount": 320000,
        "deal_stage": "negotiation",
        "act_type": "meeting",
        "act_title": "商务谈判会议",
        "act_content": "已进入合同条款谈判阶段，预计2周内签约"
    },
    {
        "company": "上海智慧医疗科技有限公司",
        "industry": "AI",
        "stage": "qualified",
        "name": "陈晓峰",
        "phone": "13621778899",
        "email": "chenxf@smartmed.cn",
        "contact_name": "陈晓峰",
        "contact_role": "首席医学信息官",
        "contact_phone2": "13918002233",
        "contact_email2": "chenxf@smartmed.cn",
        "deal_title": "AI辅助诊断系统",
        "deal_amount": 480000,
        "deal_stage": "negotiation",
        "act_type": "meeting",
        "act_title": "产品POC验收",
        "act_content": "POC验证通过，进入商务谈判阶段"
    },
    {
        "company": "北京云链科技有限公司",
        "industry": "云计算",
        "stage": "qualified",
        "name": "唐浩",
        "phone": "13810887799",
        "email": "tanghao@yunlian.cn",
        "contact_name": "唐浩",
        "contact_role": "技术VP",
        "contact_phone2": "13621009988",
        "contact_email2": "tanghao@yunlian.cn",
        "deal_title": "云原生DevOps平台",
        "deal_amount": 220000,
        "deal_stage": "negotiation",
        "act_type": "email",
        "act_title": "发送最终报价",
        "act_content": "技术评审通过，等待客户预算审批"
    },
    {
        "company": "深圳数字经济研究院",
        "industry": "大数据",
        "stage": "qualified",
        "name": "邓明辉",
        "phone": "13632889977",
        "email": "dengmh@sz-digital.cn",
        "contact_name": "邓明辉",
        "contact_role": "数据科学部主任",
        "contact_phone2": "13823236688",
        "contact_email2": "dengmh@sz-digital.cn",
        "deal_title": "数据治理与隐私计算平台",
        "deal_amount": 390000,
        "deal_stage": "negotiation",
        "act_type": "meeting",
        "act_title": "技术方案终审",
        "act_content": "客户已内部立项，准备签约材料"
    },

    # --- customer (2) ---
    {
        "company": "北京字节方舟科技有限公司",
        "industry": "AI",
        "stage": "customer",
        "name": "邓凯文",
        "phone": "13810556688",
        "email": "denghk@byteark.cn",
        "contact_name": "邓凯文",
        "contact_role": "工程VP",
        "contact_phone2": "13601008899",
        "contact_email2": "denghk@byteark.cn",
        "deal_title": "AI内容生成平台企业版",
        "deal_amount": 460000,
        "deal_stage": "closed_won",
        "act_type": "meeting",
        "act_title": "签约庆祝会议",
        "act_content": "已签约并完成首期交付，客户满意度高"
    },
    {
        "company": "上海自贸区数字贸易有限公司",
        "industry": "电商",
        "stage": "customer",
        "name": "吴思敏",
        "phone": "13817556699",
        "email": "wusm@ftz-dt.cn",
        "contact_name": "吴思敏",
        "contact_role": "数字贸易部总经理",
        "contact_phone2": "13916008877",
        "contact_email2": "wusm@ftz-dt.cn",
        "deal_title": "跨境电商综合服务平台",
        "deal_amount": 500000,
        "deal_stage": "closed_won",
        "act_type": "meeting",
        "act_title": "项目启动会",
        "act_content": "已签约，首期款已到账，项目正式启动"
    },
    # 额外2个凑够22个
    {
        "company": "深圳华云数据技术有限公司",
        "industry": "云计算",
        "stage": "qualified",
        "name": "许青山",
        "phone": "13612998877",
        "email": "xuqs@huayun-data.cn",
        "contact_name": "许青山",
        "contact_role": "基础设施总监",
        "contact_phone2": "13823232211",
        "contact_email2": "xuqs@huayun-data.cn",
        "deal_title": "多云管理平台标准版",
        "deal_amount": 130000,
        "deal_stage": "negotiation",
        "act_type": "meeting",
        "act_title": "商务谈判",
        "act_content": "客户对方案基本满意，进入商务条款谈判阶段"
    },
    {
        "company": "广州天擎数字营销有限公司",
        "industry": "数字营销",
        "stage": "prospect",
        "name": "方文静",
        "phone": "13660228899",
        "email": "fangwj@tianqing-digital.cn",
        "contact_name": "方文静",
        "contact_role": "营销技术总监",
        "contact_phone2": "13822223300",
        "contact_email2": "fangwj@tianqing-digital.cn",
        "deal_title": "Martech全链路营销平台",
        "deal_amount": 210000,
        "deal_stage": "proposal",
        "act_type": "meeting",
        "act_title": "营销技术方案汇报",
        "act_content": "客户对CDP和MA模块感兴趣，要求提供定制报价"
    },
]

# ========== 额外联系人数据（每个客户多1-2个联系人） ==========

EXTRA_CONTACTS = [
    # 北京智言科技
    {"company": "北京智言科技有限公司", "name": "苏晓", "role": "产品经理", "phone": "15811443322", "is_primary": False},
    # 上海云创信息
    {"company": "上海云创信息技术有限公司", "name": "周磊", "role": "运维主管", "phone": "13764220011", "is_primary": False},
    # 深圳前海数据智能
    {"company": "深圳前海数据智能有限公司", "name": "郑杰", "role": "数据工程师", "phone": "13632556677", "is_primary": False},
    # 杭州领航电商
    {"company": "杭州领航电子商务有限公司", "name": "何薇", "role": "电商运营经理", "phone": "15957118822", "is_primary": False},
    # 广州物联智造
    {"company": "广州物联智造科技有限公司", "name": "高翔", "role": "设备部经理", "phone": "13711112233", "is_primary": False},
    # 北京金融云
    {"company": "北京金融云科技有限公司", "name": "钱进", "role": "风控总监", "phone": "13810223344", "is_primary": False},
    # 上海数字营销
    {"company": "上海数字营销策划有限公司", "name": "沈悦", "role": "运营总监", "phone": "13651667788", "is_primary": False},
    # 成都天府软件
    {"company": "成都天府软件技术有限公司", "name": "曾骏", "role": "架构师", "phone": "13608009911", "is_primary": False},
    # 武汉长江大数据
    {"company": "武汉长江大数据研究院", "name": "吴敏", "role": "数据分析主管", "phone": "15927112233", "is_primary": False},
    # 苏州工业园区智能科技
    {"company": "苏州工业园区智能科技有限公司", "name": "蒋丽", "role": "行政总监", "phone": "13862110033", "is_primary": False},
    # 北京新零售科技
    {"company": "北京新零售科技有限公司", "name": "刘洋", "role": "IT经理", "phone": "13810009966", "is_primary": False},
    # 深圳星辰云计算
    {"company": "深圳星辰云计算有限公司", "name": "韩冰", "role": "技术总监", "phone": "15816889900", "is_primary": False},
    # 南京紫金山人工智能研究院
    {"company": "南京紫金山人工智能研究院", "name": "胡炜", "role": "研究员", "phone": "13913881122", "is_primary": False},
    # 上海智慧医疗科技
    {"company": "上海智慧医疗科技有限公司", "name": "黄蕾", "role": "临床信息主管", "phone": "13621660077", "is_primary": False},
    # 北京字节方舟科技
    {"company": "北京字节方舟科技有限公司", "name": "韩宇", "role": "采购经理", "phone": "13810008855", "is_primary": False},
    {"company": "北京字节方舟科技有限公司", "name": "顾婷婷", "role": "项目经理", "phone": "13621009911", "is_primary": False},
    # 上海自贸区数字贸易
    {"company": "上海自贸区数字贸易有限公司", "name": "陈立", "role": "IT总监", "phone": "13817992288", "is_primary": False},
    {"company": "上海自贸区数字贸易有限公司", "name": "朱虹", "role": "进出口业务经理", "phone": "13601668855", "is_primary": False},
    # 北京云链科技
    {"company": "北京云链科技有限公司", "name": "彭飞", "role": "运维总监", "phone": "13621008833", "is_primary": False},
    # 深圳数字经济研究院
    {"company": "深圳数字经济研究院", "name": "罗伟", "role": "研究员", "phone": "13632885544", "is_primary": False},
    # 杭州趣链科技
    {"company": "杭州趣链科技有限公司", "name": "赵敏", "role": "供应链总监", "phone": "13606810033", "is_primary": False},
    # 北京智汇数字营销
    {"company": "北京智汇数字营销有限公司", "name": "李想", "role": "数据分析师", "phone": "13910880066", "is_primary": False},
    # 深圳华云数据
    {"company": "深圳华云数据技术有限公司", "name": "梁启航", "role": "运维经理", "phone": "13612991100", "is_primary": False},
    # 广州天擎数字营销
    {"company": "广州天擎数字营销有限公司", "name": "程霜", "role": "品牌经理", "phone": "13660220011", "is_primary": False},
]

# ========== 额外activity记录（每个客户额外2-3条） ==========

EXTRA_ACTIVITIES_TEMPLATE = [
    {"type": "email", "title": "跟进邮件", "content": "发送产品更新说明和案例分享"},
    {"type": "call", "title": "进度跟进电话", "content": "了解客户最新需求变化和决策进展"},
    {"type": "meeting", "title": "线上会议", "content": "与客户团队进行产品功能详细讲解"},
    {"type": "task", "title": "内部评审", "content": "团队内部讨论客户定制需求可行性"},
    {"type": "email", "title": "发送合同草案", "content": "根据双方沟通结果发送合同初稿"},
]


def main():
    print("=" * 60)
    print("CRM种子数据注入脚本")
    print("=" * 60)

    # 保存旧的activities
    old_activities = load_json("crm_activities.json")
    print(f"\n📌 保留原有activities: {len(old_activities)} 条")

    # 清空旧数据（保留activities）
    files_to_clear = ["crm_customers.json", "crm_deals.json", "crm_contacts.json", "crm_contracts.json"]
    for f in files_to_clear:
        save_json(f, [])
    print("  ✓ 已清空旧测试数据")

    # 构建映射：company_name -> customer_id
    company_to_cust_id = {}
    customers_data = []
    deals_data = []
    contacts_data = []
    activities_data = []
    contracts_data = []

    print(f"\n📦 生成 {len(CUSTOMERS)} 条客户数据...")

    for idx, c in enumerate(CUSTOMERS):
        cust_id = generate_id("cust")
        company_to_cust_id[c["company"]] = cust_id

        days_ago = {
            "lead": random.randint(15, 45),
            "prospect": random.randint(30, 60),
            "qualified": random.randint(45, 90),
            "customer": random.randint(60, 120),
        }[c["stage"]]

        created_at = make_ts(days_ago)
        updated_at = make_ts(random.randint(1, 5))

        # ---- customer ----
        cust = {
            "id": cust_id,
            "name": c["name"],
            "company": c["company"],
            "industry": c["industry"],
            "source": "hunt_engine",
            "stage": c["stage"],
            "tags": ["VIP"] if c["stage"] in ("qualified", "customer") else [],
            "phone": c["phone"],
            "email": c["email"],
            "address": "",
            "website": "",
            "notes": f"{c['industry']}行业{c['stage']}阶段客户",
            "score": {"lead": 20, "prospect": 40, "qualified": 70, "customer": 95}[c["stage"]],
            "created_at": created_at,
            "updated_at": updated_at,
        }
        customers_data.append(cust)

        # ---- contact (primary) ----
        contact_id = generate_id("cont")
        contact = {
            "id": contact_id,
            "customer_id": cust_id,
            "name": c["contact_name"],
            "role": c["contact_role"],
            "phone": c["contact_phone2"],
            "email": c["contact_email2"],
            "wechat": "",
            "is_primary": True,
            "notes": "",
            "created_at": created_at,
        }
        contacts_data.append(contact)

        # ---- deal ----
        deal_id = generate_id("deal")
        prob_map = {"discovery": 20, "proposal": 50, "negotiation": 75, "closed_won": 100, "closed_lost": 0}
        deal = {
            "id": deal_id,
            "customer_id": cust_id,
            "title": c["deal_title"],
            "stage": c["deal_stage"],
            "amount": c["deal_amount"],
            "probability": prob_map.get(c["deal_stage"], 50),
            "expected_close": (datetime.now() + timedelta(days=random.randint(30, 90))).strftime("%Y-%m-%d") if c["deal_stage"] != "closed_won" else datetime.now().strftime("%Y-%m-%d"),
            "product_info": "",
            "notes": f"{c['company']}的{c['deal_title']}商机",
            "created_at": created_at,
            "updated_at": updated_at,
        }
        deals_data.append(deal)

        # ---- activity (1 primary) ----
        act_id = generate_id("act")
        activity = {
            "id": act_id,
            "customer_id": cust_id,
            "contact_id": contact_id,
            "deal_id": deal_id,
            "type": c["act_type"],
            "title": c["act_title"],
            "content": c["act_content"],
            "created_by": "system",
            "created_at": make_ts(random.randint(1, 14)),
        }
        activities_data.append(activity)

        # ---- 额外activities (2-3条) ----
        extra_count = random.randint(2, 3)
        for _ in range(extra_count):
            tmpl = random.choice(EXTRA_ACTIVITIES_TEMPLATE)
            act_id2 = generate_id("act")
            extra_act = {
                "id": act_id2,
                "customer_id": cust_id,
                "contact_id": contact_id,
                "deal_id": deal_id,
                "type": tmpl["type"],
                "title": tmpl["title"],
                "content": tmpl["content"],
                "created_by": "system",
                "created_at": make_ts(random.randint(1, 20)),
            }
            activities_data.append(extra_act)

    # ---- 额外联系人 ----
    for ec in EXTRA_CONTACTS:
        cid = company_to_cust_id.get(ec["company"])
        if not cid:
            continue
        cont_id = generate_id("cont")
        contact = {
            "id": cont_id,
            "customer_id": cid,
            "name": ec["name"],
            "role": ec["role"],
            "phone": ec["phone"],
            "email": "",
            "wechat": "",
            "is_primary": ec.get("is_primary", False),
            "notes": "",
            "created_at": make_ts(random.randint(30, 90)),
        }
        contacts_data.append(contact)

    # ---- 合同（仅customer阶段有） ----
    for c in CUSTOMERS:
        if c["stage"] != "customer":
            continue
        cid = company_to_cust_id[c["company"]]
        ct_id = generate_id("ct")
        signed_date = (datetime.now() - timedelta(days=random.randint(5, 20))).strftime("%Y-%m-%d")
        contract = {
            "id": ct_id,
            "deal_id": "",
            "customer_id": cid,
            "title": f"{c['deal_title']}服务合同",
            "amount": c["deal_amount"],
            "status": "signed",
            "signed_date": signed_date,
            "start_date": signed_date,
            "end_date": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d"),
            "content": f"{c['company']}与Gavvy SalesMaster签订的{c['deal_title']}服务合同",
            "notes": "合同已签署，服务期一年",
            "created_at": make_ts(random.randint(30, 60)),
            "updated_at": make_ts(random.randint(1, 10)),
        }
        contracts_data.append(contract)

    # ========== 写入文件 ==========
    print("\n💾 写入数据文件...")
    save_json("crm_customers.json", customers_data)
    save_json("crm_deals.json", deals_data)
    save_json("crm_contacts.json", contacts_data)
    save_json("crm_contracts.json", contracts_data)

    # 合并新旧activities
    all_activities = old_activities + activities_data
    save_json("crm_activities.json", all_activities)

    # ========== 统计报告 ==========
    print("\n" + "=" * 60)
    print("📊 种子数据统计报告")
    print("=" * 60)
    print(f"  客户 (Customers):     {len(customers_data)} 条")
    for s in ["lead", "prospect", "qualified", "customer"]:
        cnt = sum(1 for c in customers_data if c["stage"] == s)
        print(f"    - {s}: {cnt}")
    print(f"  商机 (Deals):         {len(deals_data)} 条")
    for s in ["discovery", "proposal", "negotiation", "closed_won", "closed_lost"]:
        cnt = sum(1 for d in deals_data if d["stage"] == s)
        if cnt:
            print(f"    - {s}: {cnt}")
    print(f"  联系人 (Contacts):    {len(contacts_data)} 条")
    print(f"  合同 (Contracts):     {len(contracts_data)} 条")
    print(f"  活动记录 (Activities): {len(all_activities)} 条 (新{len(activities_data)} + 旧{len(old_activities)})")
    print(f"  行业分布:")
    industries = set(c["industry"] for c in customers_data)
    for ind in sorted(industries):
        cnt = sum(1 for c in customers_data if c["industry"] == ind)
        print(f"    - {ind}: {cnt}")

    deal_amounts = [d["amount"] for d in deals_data]
    print(f"  商机金额范围: {min(deal_amounts):,} ~ {max(deal_amounts):,} 元")
    print(f"  商机总金额: {sum(deal_amounts):,} 元")
    print("\n✅ 种子数据注入完成！")


if __name__ == "__main__":
    main()
