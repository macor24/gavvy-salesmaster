"""智能寻客模块 - 公开数据挖掘

支持真实API对接和Mock模式切换
"""

import json
import random
import requests
from typing import List, Dict, Optional, Set
from datetime import datetime
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod


@dataclass
class CompanyInfo:
    """公司信息数据结构"""
    name: str
    unified_code: str = ""
    credit_code: str = ""
    registration_number: str = ""
    legal_person: str = ""
    registered_capital: str = ""
    establish_date: str = ""
    status: str = ""
    industry: str = ""
    address: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    business_scope: str = ""
    employees: str = ""
    revenue: str = ""
    description: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class TenderInfo:
    """招标信息数据结构"""
    title: str
    tender_number: str = ""
    source: str = ""
    category: str = ""
    budget: float = 0.0
    region: str = ""
    publish_date: str = ""
    deadline: str = ""
    contact: str = ""
    phone: str = ""
    url: str = ""
    summary: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class RecruitmentInfo:
    """招聘信息数据结构"""
    title: str
    company: str
    company_id: str = ""
    position: str = ""
    salary: str = ""
    location: str = ""
    experience: str = ""
    education: str = ""
    tags: List[str] = None
    publish_date: str = ""
    contact: str = ""
    url: str = ""
    requirements: str = ""

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

    def to_dict(self):
        return asdict(self)


@dataclass
class ShopInfo:
    """电商店铺信息数据结构"""
    id: str
    name: str
    company_name: str = ""
    shop_type: str = ""
    platform: str = ""
    industry: str = ""
    main_category: str = ""
    sub_category: str = ""
    location: str = ""
    established_year: str = ""
    staff_count: str = ""
    annual_revenue: str = ""
    contact_name: str = ""
    contact_phone: str = ""
    contact_email: str = ""
    website: str = ""
    description: str = ""
    products_count: int = 0
    monthly_orders: int = 0
    monthly_revenue: float = 0.0
    rating: float = 0.0
    response_rate: float = 0.0
    trade_assurance: bool = False
    gold_supplier: bool = False
    verified_supplier: bool = False
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

    def to_dict(self):
        return asdict(self)


@dataclass
class ProductInfo:
    """产品信息数据结构"""
    id: str
    name: str
    shop_id: str = ""
    shop_name: str = ""
    category: str = ""
    price: float = 0.0
    original_price: float = 0.0
    min_order: int = 1
    monthly_sales: int = 0
    rating: float = 0.0
    reviews_count: int = 0
    description: str = ""
    image_url: str = ""
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

    def to_dict(self):
        return asdict(self)


class ECommercePlatform:
    ALIBABA_1688 = "1688"
    ALIBABA_INTERNATIONAL = "alibaba"
    INDEPENDENT_SHOP = "independent"


class IndustryCategory:
    ELECTRONICS = "电子元器件"
    MACHINERY = "机械设备"
    TEXTILE = "纺织面料"
    CHEMICAL = "化工原料"
    FOOD = "食品饮料"
    BEAUTY = "美妆护肤"
    CLOTHING = "服装鞋帽"
    TOOLS = "五金工具"
    PACKAGING = "包装材料"
    FURNITURE = "家具家居"
    TOYS = "玩具礼品"
    SPORTS = "运动户外"
    AUTO = "汽车配件"
    MEDICAL = "医疗器械"
    ENERGY = "新能源"
    AI_TECH = "AI科技"
    OTHER = "其他"


class DataSource(ABC):
    """数据源抽象基类"""
    
    @abstractmethod
    def search_companies(self, keyword: str, **kwargs) -> List[CompanyInfo]:
        pass
    
    @abstractmethod
    def get_company_detail(self, company_id: str) -> Optional[CompanyInfo]:
        pass


class TianYanChaMock(DataSource):
    """天眼查模拟数据源"""
    
    def __init__(self):
        self.mock_data = self._load_mock_data()
    
    def _load_mock_data(self) -> Dict:
        return {
            "companies": [
                {
                    "name": "北京科技创新有限公司",
                    "unified_code": "91110108MA01234567",
                    "credit_code": "91110108MA01234567",
                    "legal_person": "张明",
                    "registered_capital": "500万人民币",
                    "establish_date": "2018-05-15",
                    "status": "存续",
                    "industry": "科技推广和应用服务业",
                    "address": "北京市海淀区中关村科技园",
                    "phone": "010-12345678",
                    "email": "contact@bjtech.com",
                    "website": "www.bjtech.com",
                    "business_scope": "技术开发、技术咨询、技术服务",
                    "employees": "50-100人",
                    "revenue": "1000-5000万",
                    "description": "专注于人工智能领域的科技创新企业"
                },
                {
                    "name": "上海智能制造有限公司",
                    "unified_code": "91310104MA06789012",
                    "credit_code": "91310104MA06789012",
                    "legal_person": "李强",
                    "registered_capital": "1000万人民币",
                    "establish_date": "2015-12-20",
                    "status": "存续",
                    "industry": "通用设备制造业",
                    "address": "上海市浦东新区张江高科技园区",
                    "phone": "021-87654321",
                    "email": "info@shsmart.com",
                    "website": "www.shsmart.com",
                    "business_scope": "智能制造设备研发、生产、销售",
                    "employees": "100-200人",
                    "revenue": "5000万-1亿",
                    "description": "领先的智能制造解决方案提供商"
                },
                {
                    "name": "深圳数据科技有限公司",
                    "unified_code": "91440300MA09876543",
                    "credit_code": "91440300MA09876543",
                    "legal_person": "王芳",
                    "registered_capital": "800万人民币",
                    "establish_date": "2019-03-10",
                    "status": "存续",
                    "industry": "软件和信息技术服务业",
                    "address": "深圳市南山区科技园",
                    "phone": "0755-23456789",
                    "email": "sales@szhdata.com",
                    "website": "www.szhdata.com",
                    "business_scope": "数据处理、大数据分析、软件开发",
                    "employees": "200-500人",
                    "revenue": "1亿-5亿",
                    "description": "专业的数据服务和大数据分析公司"
                },
                {
                    "name": "广州智能科技有限公司",
                    "unified_code": "91440101MA0ABCDEF1",
                    "credit_code": "91440101MA0ABCDEF1",
                    "legal_person": "陈伟",
                    "registered_capital": "300万人民币",
                    "establish_date": "2020-08-25",
                    "status": "存续",
                    "industry": "研究和试验发展",
                    "address": "广州市天河区智慧城",
                    "phone": "020-98765432",
                    "email": "support@gzsmart.com",
                    "website": "www.gzsmart.com",
                    "business_scope": "智能设备研发、技术转让、技术咨询",
                    "employees": "10-50人",
                    "revenue": "500-1000万",
                    "description": "专注于物联网和智能硬件的创新企业"
                },
                {
                    "name": "杭州云计算有限公司",
                    "unified_code": "91330108MA0XYZ1234",
                    "credit_code": "91330108MA0XYZ1234",
                    "legal_person": "刘洋",
                    "registered_capital": "2000万人民币",
                    "establish_date": "2017-06-08",
                    "status": "存续",
                    "industry": "互联网和相关服务",
                    "address": "杭州市滨江区互联网小镇",
                    "phone": "0571-56789012",
                    "email": "hello@hzcloud.com",
                    "website": "www.hzcloud.com",
                    "business_scope": "云计算服务、云存储、云安全",
                    "employees": "500-1000人",
                    "revenue": "5亿-10亿",
                    "description": "国内领先的云计算服务提供商"
                }
            ]
        }
    
    def search_companies(self, keyword: str, **kwargs) -> List[CompanyInfo]:
        industry = kwargs.get("industry")
        results = []
        for company in self.mock_data["companies"]:
            match = False
            if keyword.lower() in company["name"].lower() or \
               keyword.lower() in company["industry"].lower() or \
               keyword.lower() in company["business_scope"].lower():
                match = True
            if industry and industry.lower() in company["industry"].lower():
                match = True
            if match:
                results.append(CompanyInfo(**company))
        return results
    
    def get_company_detail(self, company_id: str) -> Optional[CompanyInfo]:
        for company in self.mock_data["companies"]:
            if company["unified_code"] == company_id or company["name"] == company_id:
                return CompanyInfo(**company)
        return None


class TianYanChaAPI(DataSource):
    """天眼查真实API对接"""
    
    BASE_URL = "https://api.tianyancha.com"
    
    def __init__(self, api_key: str = None, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        if not self.api_key:
            return None
        try:
            url = f"{self.BASE_URL}{endpoint}"
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"天眼查API请求失败: {e}")
            return None
    
    def search_companies(self, keyword: str, **kwargs) -> List[CompanyInfo]:
        params = {
            "keyword": keyword,
            "pageSize": kwargs.get("page_size", 10),
            "pageNum": kwargs.get("page_num", 1)
        }
        data = self._make_request("/services/open/search/company", params)
        if not data:
            return self._fallback_search(keyword, **kwargs)
        
        results = []
        for item in data.get("data", []):
            results.append(CompanyInfo(
                name=item.get("name", ""),
                unified_code=item.get("unifiedSocialCreditCode", ""),
                credit_code=item.get("creditCode", ""),
                registration_number=item.get("regNo", ""),
                legal_person=item.get("legalPersonName", ""),
                registered_capital=item.get("regCapital", ""),
                establish_date=item.get("estiblishTime", ""),
                status=item.get("status", ""),
                industry=item.get("industry", ""),
                address=item.get("address", ""),
                phone=item.get("phone", ""),
                email=item.get("email", ""),
                website=item.get("website", ""),
                business_scope=item.get("businessScope", ""),
                employees=item.get("staffNumRange", ""),
                description=item.get("introduction", "")
            ))
        return results
    
    def get_company_detail(self, company_id: str) -> Optional[CompanyInfo]:
        data = self._make_request(f"/services/open/company/getById/{company_id}")
        if not data:
            return self._fallback_detail(company_id)
        
        item = data.get("data", {})
        return CompanyInfo(
            name=item.get("name", ""),
            unified_code=item.get("unifiedSocialCreditCode", ""),
            credit_code=item.get("creditCode", ""),
            registration_number=item.get("regNo", ""),
            legal_person=item.get("legalPersonName", ""),
            registered_capital=item.get("regCapital", ""),
            establish_date=item.get("estiblishTime", ""),
            status=item.get("status", ""),
            industry=item.get("industry", ""),
            address=item.get("address", ""),
            phone=item.get("phone", ""),
            email=item.get("email", ""),
            website=item.get("website", ""),
            business_scope=item.get("businessScope", ""),
            employees=item.get("staffNumRange", ""),
            revenue=item.get("revenue", ""),
            description=item.get("introduction", "")
        )
    
    def _fallback_search(self, keyword: str, **kwargs) -> List[CompanyInfo]:
        mock = TianYanChaMock()
        return mock.search_companies(keyword, **kwargs)
    
    def _fallback_detail(self, company_id: str) -> Optional[CompanyInfo]:
        mock = TianYanChaMock()
        return mock.get_company_detail(company_id)


class QiChaChaMock(DataSource):
    """企查查模拟数据源"""
    
    def search_companies(self, keyword: str, **kwargs) -> List[CompanyInfo]:
        tianyancha = TianYanChaMock()
        return tianyancha.search_companies(keyword, **kwargs)
    
    def get_company_detail(self, company_id: str) -> Optional[CompanyInfo]:
        tianyancha = TianYanChaMock()
        return tianyancha.get_company_detail(company_id)


class QiChaChaAPI(DataSource):
    """企查查真实API对接"""
    
    BASE_URL = "https://api.qcc.com"
    
    def __init__(self, api_key: str = None, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        if not self.api_key:
            return None
        try:
            url = f"{self.BASE_URL}{endpoint}"
            params = params or {}
            params["key"] = self.api_key
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"企查查API请求失败: {e}")
            return None
    
    def search_companies(self, keyword: str, **kwargs) -> List[CompanyInfo]:
        params = {
            "keyword": keyword,
            "page_size": kwargs.get("page_size", 10),
            "page_index": kwargs.get("page_num", 1)
        }
        data = self._make_request("/api/search", params)
        if not data:
            return self._fallback_search(keyword, **kwargs)
        
        results = []
        for item in data.get("result", []):
            results.append(CompanyInfo(
                name=item.get("name", ""),
                unified_code=item.get("unified_social_credit_code", ""),
                credit_code=item.get("credit_code", ""),
                registration_number=item.get("registration_number", ""),
                legal_person=item.get("legal_person", ""),
                registered_capital=item.get("registered_capital", ""),
                establish_date=item.get("establish_date", ""),
                status=item.get("status", ""),
                industry=item.get("industry", ""),
                address=item.get("address", ""),
                phone=item.get("phone", ""),
                email=item.get("email", ""),
                website=item.get("website", ""),
                business_scope=item.get("business_scope", ""),
                employees=item.get("employees", ""),
                description=item.get("description", "")
            ))
        return results
    
    def get_company_detail(self, company_id: str) -> Optional[CompanyInfo]:
        data = self._make_request(f"/api/company/{company_id}")
        if not data:
            return self._fallback_detail(company_id)
        
        item = data.get("data", {})
        return CompanyInfo(
            name=item.get("name", ""),
            unified_code=item.get("unified_social_credit_code", ""),
            credit_code=item.get("credit_code", ""),
            registration_number=item.get("registration_number", ""),
            legal_person=item.get("legal_person", ""),
            registered_capital=item.get("registered_capital", ""),
            establish_date=item.get("establish_date", ""),
            status=item.get("status", ""),
            industry=item.get("industry", ""),
            address=item.get("address", ""),
            phone=item.get("phone", ""),
            email=item.get("email", ""),
            website=item.get("website", ""),
            business_scope=item.get("business_scope", ""),
            employees=item.get("employees", ""),
            revenue=item.get("revenue", ""),
            description=item.get("description", "")
        )
    
    def _fallback_search(self, keyword: str, **kwargs) -> List[CompanyInfo]:
        mock = TianYanChaMock()
        return mock.search_companies(keyword, **kwargs)
    
    def _fallback_detail(self, company_id: str) -> Optional[CompanyInfo]:
        mock = TianYanChaMock()
        return mock.get_company_detail(company_id)


class TenderCrawler:
    """招标信息抓取器"""
    
    def __init__(self, use_real_api: bool = False):
        self.use_real_api = use_real_api
        self.mock_tenders = self._load_mock_tenders()
    
    def _load_mock_tenders(self) -> List[Dict]:
        return [
            {
                "title": "智慧园区信息化建设项目",
                "tender_number": "ZB-2024-001",
                "source": "中国招标投标公共服务平台",
                "category": "信息化工程",
                "budget": 5000000.0,
                "region": "北京市",
                "publish_date": "2024-01-15",
                "deadline": "2024-01-30",
                "contact": "王经理",
                "phone": "010-11112222",
                "url": "https://www.cebpubservice.com/",
                "summary": "智慧园区信息化建设，包括智能安防、智能停车、智能照明等系统"
            },
            {
                "title": "企业数字化转型咨询服务",
                "tender_number": "ZB-2024-002",
                "source": "政府采购网",
                "category": "咨询服务",
                "budget": 2000000.0,
                "region": "上海市",
                "publish_date": "2024-01-16",
                "deadline": "2024-02-01",
                "contact": "李主任",
                "phone": "021-22223333",
                "url": "https://www.ccgp.gov.cn/",
                "summary": "企业数字化转型战略咨询和实施方案设计"
            },
            {
                "title": "大数据分析平台建设",
                "tender_number": "ZB-2024-003",
                "source": "招标投标网",
                "category": "软件开发",
                "budget": 8000000.0,
                "region": "广东省",
                "publish_date": "2024-01-17",
                "deadline": "2024-02-05",
                "contact": "张工",
                "phone": "020-33334444",
                "url": "https://www.ztb.cn/",
                "summary": "建设企业级大数据分析平台，支持实时数据分析和可视化"
            },
            {
                "title": "AI客服系统采购项目",
                "tender_number": "ZB-2024-004",
                "source": "中国招标投标网",
                "category": "IT设备采购",
                "budget": 3500000.0,
                "region": "浙江省",
                "publish_date": "2024-01-18",
                "deadline": "2024-02-10",
                "contact": "陈经理",
                "phone": "0571-44445555",
                "url": "https://www.chinabidding.com/",
                "summary": "采购智能客服系统，支持语音识别和自然语言处理"
            },
            {
                "title": "智能制造生产线改造",
                "tender_number": "ZB-2024-005",
                "source": "机电产品招标投标网",
                "category": "设备采购",
                "budget": 15000000.0,
                "region": "江苏省",
                "publish_date": "2024-01-19",
                "deadline": "2024-02-15",
                "contact": "周总",
                "phone": "025-55556666",
                "url": "https://www.chinamachinery.gov.cn/",
                "summary": "智能制造生产线改造项目，引入工业机器人和自动化设备"
            }
        ]
    
    def crawl_tenders(self, keyword: str = "", region: str = "", days: int = 7, industry: str = "") -> List[TenderInfo]:
        if self.use_real_api:
            return self._crawl_real_tenders(keyword, region, days, industry)
        return self._crawl_mock_tenders(keyword, region, days, industry)
    
    def _crawl_real_tenders(self, keyword: str = "", region: str = "", days: int = 7, industry: str = "") -> List[TenderInfo]:
        results = []
        try:
            import feedparser
            rss_urls = ["https://www.cebpubservice.com/rss", "https://www.ccgp.gov.cn/rss"]
            for url in rss_urls:
                try:
                    feed = feedparser.parse(url)
                    for entry in feed.entries[:10]:
                        tender = TenderInfo(
                            title=entry.get("title", ""),
                            source=url.split("//")[1].split("/")[0],
                            publish_date=entry.get("published", ""),
                            summary=entry.get("summary", ""),
                            url=entry.get("link", "")
                        )
                        if not keyword or keyword.lower() in tender.title.lower():
                            if not region or region.lower() in tender.title.lower():
                                if not industry or industry.lower() in tender.title.lower():
                                    results.append(tender)
                except Exception as e:
                    print(f"抓取RSS失败 {url}: {e}")
        except ImportError:
            print("未安装feedparser，使用mock数据")
            return self._crawl_mock_tenders(keyword, region, days, industry)
        return sorted(results[:10], key=lambda x: x.publish_date, reverse=True)
    
    def _crawl_mock_tenders(self, keyword: str = "", region: str = "", days: int = 7, industry: str = "") -> List[TenderInfo]:
        results = []
        today = datetime.now()
        for tender in self.mock_tenders:
            publish_date = datetime.strptime(tender["publish_date"], "%Y-%m-%d")
            days_diff = (today - publish_date).days
            if days_diff <= days:
                if not keyword or keyword.lower() in tender["title"].lower() or keyword.lower() in tender["summary"].lower():
                    if not region or region.lower() in tender["region"].lower():
                        if not industry or industry.lower() in tender["category"].lower():
                            results.append(TenderInfo(**tender))
        return sorted(results, key=lambda x: x.publish_date, reverse=True)


class RecruitmentAnalyzer:
    """招聘信息分析器"""
    
    def __init__(self, use_real_api: bool = False):
        self.use_real_api = use_real_api
        self.mock_recruitments = self._load_mock_recruitments()
    
    def _load_mock_recruitments(self) -> List[Dict]:
        return [
            {
                "title": "高级产品经理",
                "company": "北京科技创新有限公司",
                "company_id": "91110108MA01234567",
                "position": "产品经理",
                "salary": "30K-50K",
                "location": "北京",
                "experience": "5-10年",
                "education": "本科",
                "tags": ["AI", "SaaS", "B2B"],
                "publish_date": "2024-01-18",
                "contact": "HR",
                "url": "https://www.lagou.com/",
                "requirements": "有SaaS产品经验，熟悉AI领域优先"
            },
            {
                "title": "后端开发工程师",
                "company": "上海智能制造有限公司",
                "company_id": "91310104MA06789012",
                "position": "后端开发",
                "salary": "25K-45K",
                "location": "上海",
                "experience": "3-5年",
                "education": "本科",
                "tags": ["Python", "Go", "微服务"],
                "publish_date": "2024-01-17",
                "contact": "技术部",
                "url": "https://www.zhipin.com/",
                "requirements": "熟悉Python/Go，有微服务架构经验"
            },
            {
                "title": "数据分析师",
                "company": "深圳数据科技有限公司",
                "company_id": "91440300MA09876543",
                "position": "数据分析",
                "salary": "20K-35K",
                "location": "深圳",
                "experience": "3-5年",
                "education": "本科",
                "tags": ["大数据", "SQL", "Python"],
                "publish_date": "2024-01-16",
                "contact": "数据团队",
                "url": "https://www.51job.com/",
                "requirements": "精通SQL，熟悉Python数据分析库"
            },
            {
                "title": "销售经理",
                "company": "广州智能科技有限公司",
                "company_id": "91440101MA0ABCDEF1",
                "position": "销售",
                "salary": "15K-30K",
                "location": "广州",
                "experience": "3-5年",
                "education": "大专",
                "tags": ["B2B销售", "智能硬件", "客户拓展"],
                "publish_date": "2024-01-15",
                "contact": "销售总监",
                "url": "https://www.job5156.com/",
                "requirements": "有智能硬件销售经验，良好的沟通能力"
            },
            {
                "title": "云计算架构师",
                "company": "杭州云计算有限公司",
                "company_id": "91330108MA0XYZ1234",
                "position": "架构师",
                "salary": "40K-70K",
                "location": "杭州",
                "experience": "8-10年",
                "education": "本科",
                "tags": ["云计算", "架构设计", "AWS/阿里云"],
                "publish_date": "2024-01-14",
                "contact": "技术总监",
                "url": "https://www.boss直聘.com/",
                "requirements": "有大型云平台架构设计经验"
            }
        ]
    
    def analyze_recruitment(self, keyword: str = "", location: str = "", industry: str = "") -> List[RecruitmentInfo]:
        if self.use_real_api:
            return self._analyze_real_recruitment(keyword, location, industry)
        return self._analyze_mock_recruitment(keyword, location, industry)
    
    def _analyze_real_recruitment(self, keyword: str = "", location: str = "", industry: str = "") -> List[RecruitmentInfo]:
        results = []
        try:
            from pyquery import PyQuery as pq
            urls = [
                f"https://www.lagou.com/zhaopin/{keyword}/?city={location}" if keyword and location else None,
                f"https://search.51job.com/list/{location},000000,0000,00,9,99,{keyword},2,1.html" if keyword else None
            ]
            for url in [u for u in urls if u]:
                try:
                    doc = pq(url=url)
                    for item in doc(".item_con_list .con_list_item").items():
                        title = item(".position_link").text()
                        company = item(".company_name a").text()
                        if title and company:
                            recruitment = RecruitmentInfo(
                                title=title,
                                company=company,
                                position=title,
                                salary=item(".money").text(),
                                location=location,
                                publish_date=datetime.now().strftime("%Y-%m-%d"),
                                url=url
                            )
                            if not industry or any(industry.lower() in tag.lower() for tag in ["AI", "科技", industry]):
                                results.append(recruitment)
                except Exception as e:
                    print(f"抓取招聘信息失败 {url}: {e}")
        except ImportError:
            print("未安装pyquery，使用mock数据")
            return self._analyze_mock_recruitment(keyword, location, industry)
        return sorted(results[:10], key=lambda x: x.publish_date, reverse=True)
    
    def _analyze_mock_recruitment(self, keyword: str = "", location: str = "", industry: str = "") -> List[RecruitmentInfo]:
        results = []
        for recruitment in self.mock_recruitments:
            keyword_match = not keyword or \
                           keyword.lower() in recruitment["title"].lower() or \
                           keyword.lower() in recruitment["position"].lower() or \
                           any(keyword.lower() in tag.lower() for tag in recruitment["tags"])
            location_match = not location or location.lower() in recruitment["location"].lower()
            industry_match = not industry or any(industry.lower() in tag.lower() for tag in recruitment["tags"])
            if keyword_match and location_match and industry_match:
                recruitment["tags"] = recruitment.get("tags", [])
                results.append(RecruitmentInfo(**recruitment))
        return sorted(results, key=lambda x: x.publish_date, reverse=True)
    
    def get_hiring_companies(self) -> List[str]:
        return list(set(r.company for r in self.mock_recruitments))


class ECommerceSource(ABC):
    """电商平台数据源抽象基类"""
    
    @abstractmethod
    def search_shops(self, keyword: str, **kwargs) -> List[ShopInfo]:
        pass
    
    @abstractmethod
    def get_shop_detail(self, shop_id: str) -> Optional[ShopInfo]:
        pass
    
    @abstractmethod
    def search_products(self, keyword: str, **kwargs) -> List[ProductInfo]:
        pass


class Alibaba1688Mock(ECommerceSource):
    """1688平台模拟数据源"""
    
    def __init__(self):
        self.mock_shops = self._load_mock_shops()
        self.mock_products = self._load_mock_products()
    
    def _load_mock_shops(self) -> List[Dict]:
        return [
            {
                "id": "shop1688_001",
                "name": "深圳市华强电子有限公司",
                "company_name": "深圳市华强电子有限公司",
                "shop_type": "旗舰店",
                "platform": "1688",
                "industry": "电子元器件",
                "main_category": "电子产品",
                "sub_category": "电子元器件",
                "location": "广东省深圳市",
                "established_year": "2015",
                "staff_count": "50-100人",
                "annual_revenue": "5000万-1亿",
                "contact_name": "李经理",
                "contact_phone": "13800138001",
                "contact_email": "sales@huaqiang-elec.com",
                "website": "https://huaqiang-elec.1688.com",
                "description": "专业电子元器件供应商，主营IC芯片、连接器、电阻电容等",
                "products_count": 2580,
                "monthly_orders": 3500,
                "monthly_revenue": 8500000.0,
                "rating": 4.8,
                "response_rate": 98.5,
                "trade_assurance": True,
                "gold_supplier": True,
                "verified_supplier": True,
                "tags": ["电子元器件", "IC芯片", "连接器", "深圳"]
            },
            {
                "id": "shop1688_002",
                "name": "东莞市精密五金制品厂",
                "company_name": "东莞市精密五金制品有限公司",
                "shop_type": "企业店",
                "platform": "1688",
                "industry": "五金工具",
                "main_category": "五金工具",
                "sub_category": "精密零件",
                "location": "广东省东莞市",
                "established_year": "2012",
                "staff_count": "100-200人",
                "annual_revenue": "1亿-5亿",
                "contact_name": "王总",
                "contact_phone": "13900139002",
                "contact_email": "wang@precision-hardware.com",
                "website": "https://precision-hardware.1688.com",
                "description": "专业精密五金加工，CNC数控加工，五金冲压件",
                "products_count": 1250,
                "monthly_orders": 2800,
                "monthly_revenue": 12000000.0,
                "rating": 4.7,
                "response_rate": 96.2,
                "trade_assurance": True,
                "gold_supplier": True,
                "verified_supplier": True,
                "tags": ["五金加工", "CNC", "精密零件", "东莞"]
            },
            {
                "id": "shop1688_003",
                "name": "杭州美妆供应链",
                "company_name": "杭州美妆供应链有限公司",
                "shop_type": "专营店",
                "platform": "1688",
                "industry": "美妆护肤",
                "main_category": "美妆个护",
                "sub_category": "护肤品",
                "location": "浙江省杭州市",
                "established_year": "2018",
                "staff_count": "50-100人",
                "annual_revenue": "5000万-1亿",
                "contact_name": "陈经理",
                "contact_phone": "13700137003",
                "contact_email": "chen@hangzhou-cosmetics.com",
                "website": "https://hz-cosmetics.1688.com",
                "description": "专业美妆供应链，提供护肤品、彩妆、个人护理产品批发",
                "products_count": 3200,
                "monthly_orders": 8500,
                "monthly_revenue": 6500000.0,
                "rating": 4.9,
                "response_rate": 99.1,
                "trade_assurance": True,
                "gold_supplier": False,
                "verified_supplier": True,
                "tags": ["美妆", "护肤品", "批发", "杭州"]
            },
            {
                "id": "shop1688_004",
                "name": "苏州机械设备制造厂",
                "company_name": "苏州机械设备制造有限公司",
                "shop_type": "旗舰店",
                "platform": "1688",
                "industry": "机械设备",
                "main_category": "机械设备",
                "sub_category": "自动化设备",
                "location": "江苏省苏州市",
                "established_year": "2010",
                "staff_count": "200-500人",
                "annual_revenue": "5亿-10亿",
                "contact_name": "刘厂长",
                "contact_phone": "13600136004",
                "contact_email": "liu@sz-machinery.com",
                "website": "https://sz-machinery.1688.com",
                "description": "专业生产自动化生产线、工业机器人、输送设备",
                "products_count": 580,
                "monthly_orders": 320,
                "monthly_revenue": 18000000.0,
                "rating": 4.6,
                "response_rate": 94.8,
                "trade_assurance": True,
                "gold_supplier": True,
                "verified_supplier": True,
                "tags": ["机械设备", "自动化", "工业机器人", "苏州"]
            },
            {
                "id": "shop1688_005",
                "name": "广州服装批发中心",
                "company_name": "广州服装批发有限公司",
                "shop_type": "专营店",
                "platform": "1688",
                "industry": "服装鞋帽",
                "main_category": "服装",
                "sub_category": "女装",
                "location": "广东省广州市",
                "established_year": "2016",
                "staff_count": "100-200人",
                "annual_revenue": "1亿-5亿",
                "contact_name": "张经理",
                "contact_phone": "13500135005",
                "contact_email": "zhang@gz-fashion.com",
                "website": "https://gz-fashion.1688.com",
                "description": "专业女装批发，提供时尚女装、连衣裙、T恤等",
                "products_count": 4500,
                "monthly_orders": 12000,
                "monthly_revenue": 9500000.0,
                "rating": 4.8,
                "response_rate": 97.6,
                "trade_assurance": True,
                "gold_supplier": False,
                "verified_supplier": True,
                "tags": ["女装", "服装批发", "时尚", "广州"]
            }
        ]
    
    def _load_mock_products(self) -> List[Dict]:
        return [
            {
                "id": "prod_001",
                "name": "STM32F103C8T6 单片机芯片",
                "shop_id": "shop1688_001",
                "shop_name": "深圳市华强电子有限公司",
                "category": "电子元器件",
                "price": 8.5,
                "original_price": 10.0,
                "min_order": 10,
                "monthly_sales": 15800,
                "rating": 4.9,
                "reviews_count": 3256,
                "description": "STM32F103C8T6 ARM Cortex-M3 32位微控制器",
                "image_url": "https://example.com/stm32.jpg",
                "tags": ["STM32", "单片机", "MCU", "电子"]
            },
            {
                "id": "prod_002",
                "name": "CNC铝合金精密零件加工",
                "shop_id": "shop1688_002",
                "shop_name": "东莞市精密五金制品厂",
                "category": "五金工具",
                "price": 125.0,
                "original_price": 150.0,
                "min_order": 1,
                "monthly_sales": 280,
                "rating": 4.8,
                "reviews_count": 156,
                "description": "定制CNC铝合金精密零件加工服务",
                "image_url": "https://example.com/cnc.jpg",
                "tags": ["CNC加工", "铝合金", "精密零件"]
            },
            {
                "id": "prod_003",
                "name": "玻尿酸补水面膜",
                "shop_id": "shop1688_003",
                "shop_name": "杭州美妆供应链",
                "category": "美妆护肤",
                "price": 3.5,
                "original_price": 5.0,
                "min_order": 100,
                "monthly_sales": 25600,
                "rating": 4.9,
                "reviews_count": 8920,
                "description": "深层补水保湿面膜，温和不刺激",
                "image_url": "https://example.com/mask.jpg",
                "tags": ["面膜", "玻尿酸", "补水", "护肤"]
            },
            {
                "id": "prod_004",
                "name": "自动化流水线输送线",
                "shop_id": "shop1688_004",
                "shop_name": "苏州机械设备制造厂",
                "category": "机械设备",
                "price": 85000.0,
                "original_price": 100000.0,
                "min_order": 1,
                "monthly_sales": 15,
                "rating": 4.7,
                "reviews_count": 45,
                "description": "定制自动化生产线，适用于电子、食品等行业",
                "image_url": "https://example.com/line.jpg",
                "tags": ["自动化", "流水线", "输送线"]
            },
            {
                "id": "prod_005",
                "name": "夏季碎花连衣裙",
                "shop_id": "shop1688_005",
                "shop_name": "广州服装批发中心",
                "category": "服装鞋帽",
                "price": 45.0,
                "original_price": 68.0,
                "min_order": 10,
                "monthly_sales": 8500,
                "rating": 4.8,
                "reviews_count": 2340,
                "description": "时尚碎花连衣裙，修身显瘦",
                "image_url": "https://example.com/dress.jpg",
                "tags": ["连衣裙", "女装", "碎花", "夏季"]
            }
        ]
    
    def search_shops(self, keyword: str = "", **kwargs) -> List[ShopInfo]:
        industry = kwargs.get("industry")
        location = kwargs.get("location")
        results = []
        for shop in self.mock_shops:
            keyword_match = not keyword or \
                           keyword.lower() in shop["name"].lower() or \
                           keyword.lower() in shop["company_name"].lower() or \
                           keyword.lower() in shop["industry"].lower() or \
                           keyword.lower() in shop["description"].lower() or \
                           any(keyword.lower() in tag.lower() for tag in shop.get("tags", []))
            industry_match = not industry or industry.lower() in shop["industry"].lower()
            location_match = not location or location.lower() in shop["location"].lower()
            if keyword_match and industry_match and location_match:
                shop["tags"] = shop.get("tags", [])
                results.append(ShopInfo(**shop))
        return sorted(results, key=lambda x: x.monthly_revenue, reverse=True)
    
    def get_shop_detail(self, shop_id: str) -> Optional[ShopInfo]:
        for shop in self.mock_shops:
            if shop["id"] == shop_id:
                shop["tags"] = shop.get("tags", [])
                return ShopInfo(**shop)
        return None
    
    def search_products(self, keyword: str = "", **kwargs) -> List[ProductInfo]:
        category = kwargs.get("category")
        min_price = kwargs.get("min_price", 0)
        max_price = kwargs.get("max_price", float('inf'))
        results = []
        for product in self.mock_products:
            keyword_match = not keyword or \
                           keyword.lower() in product["name"].lower() or \
                           keyword.lower() in product["description"].lower() or \
                           any(keyword.lower() in tag.lower() for tag in product.get("tags", []))
            category_match = not category or category.lower() in product["category"].lower()
            price_match = min_price <= product["price"] <= max_price
            if keyword_match and category_match and price_match:
                product["tags"] = product.get("tags", [])
                results.append(ProductInfo(**product))
        return sorted(results, key=lambda x: x.monthly_sales, reverse=True)


class AlibabaInternationalMock(ECommerceSource):
    """阿里国际站模拟数据源"""
    
    def __init__(self):
        self.mock_shops = self._load_mock_shops()
        self.mock_products = self._load_mock_products()
    
    def _load_mock_shops(self) -> List[Dict]:
        return [
            {
                "id": "shop_alibaba_001",
                "name": "Global Tech Components Ltd.",
                "company_name": "深圳全球科技有限公司",
                "shop_type": "Gold Supplier",
                "platform": "alibaba",
                "industry": "电子元器件",
                "main_category": "Electronics",
                "sub_category": "Electronic Components",
                "location": "Guangdong, China",
                "established_year": "2014",
                "staff_count": "100-200 people",
                "annual_revenue": "10M-50M USD",
                "contact_name": "David Li",
                "contact_phone": "+86 13800138001",
                "contact_email": "david@global-tech.cn",
                "website": "https://global-tech.en.alibaba.com",
                "description": "Professional electronic components supplier, IC chips, connectors, capacitors",
                "products_count": 3200,
                "monthly_orders": 4200,
                "monthly_revenue": 1250000.0,
                "rating": 4.9,
                "response_rate": 99.2,
                "trade_assurance": True,
                "gold_supplier": True,
                "verified_supplier": True,
                "tags": ["Electronics", "IC Chips", "Supplier", "China"]
            },
            {
                "id": "shop_alibaba_002",
                "name": "Smart Machinery Co., Ltd.",
                "company_name": "杭州智能机械有限公司",
                "shop_type": "Gold Supplier",
                "platform": "alibaba",
                "industry": "机械设备",
                "main_category": "Machinery",
                "sub_category": "Packaging Machinery",
                "location": "Zhejiang, China",
                "established_year": "2012",
                "staff_count": "200-500 people",
                "annual_revenue": "50M-100M USD",
                "contact_name": "Michael Wang",
                "contact_phone": "+86 13900139002",
                "contact_email": "michael@smart-machinery.cn",
                "website": "https://smart-machinery.en.alibaba.com",
                "description": "Professional packaging machinery manufacturer, automatic packaging lines",
                "products_count": 450,
                "monthly_orders": 180,
                "monthly_revenue": 2800000.0,
                "rating": 4.7,
                "response_rate": 96.8,
                "trade_assurance": True,
                "gold_supplier": True,
                "verified_supplier": True,
                "tags": ["Machinery", "Packaging", "Manufacturer", "China"]
            },
            {
                "id": "shop_alibaba_003",
                "name": "Fashion World Apparel",
                "company_name": "广州时尚世界服饰有限公司",
                "shop_type": "Supplier",
                "platform": "alibaba",
                "industry": "服装鞋帽",
                "main_category": "Apparel",
                "sub_category": "Women's Clothing",
                "location": "Guangdong, China",
                "established_year": "2016",
                "staff_count": "100-200 people",
                "annual_revenue": "10M-50M USD",
                "contact_name": "Lisa Chen",
                "contact_phone": "+86 13700137003",
                "contact_email": "lisa@fashion-world.cn",
                "website": "https://fashion-world.en.alibaba.com",
                "description": "Fashion women's clothing exporter, dresses, tops, accessories",
                "products_count": 5600,
                "monthly_orders": 15000,
                "monthly_revenue": 980000.0,
                "rating": 4.8,
                "response_rate": 98.1,
                "trade_assurance": True,
                "gold_supplier": False,
                "verified_supplier": True,
                "tags": ["Apparel", "Fashion", "Women", "Export"]
            }
        ]
    
    def _load_mock_products(self) -> List[Dict]:
        return [
            {
                "id": "prod_intl_001",
                "name": "Arduino Uno R4 Minima",
                "shop_id": "shop_alibaba_001",
                "shop_name": "Global Tech Components Ltd.",
                "category": "Electronics",
                "price": 28.5,
                "original_price": 35.0,
                "min_order": 10,
                "monthly_sales": 8500,
                "rating": 4.9,
                "reviews_count": 2150,
                "description": "Arduino Uno R4 Minima development board",
                "image_url": "https://example.com/arduino.jpg",
                "tags": ["Arduino", "Development Board", "Electronics"]
            },
            {
                "id": "prod_intl_002",
                "name": "Automatic Bottle Labeling Machine",
                "shop_id": "shop_alibaba_002",
                "shop_name": "Smart Machinery Co., Ltd.",
                "category": "Machinery",
                "price": 18500.0,
                "original_price": 22000.0,
                "min_order": 1,
                "monthly_sales": 45,
                "rating": 4.8,
                "reviews_count": 89,
                "description": "Automatic labeling machine for bottles",
                "image_url": "https://example.com/labeling.jpg",
                "tags": ["Labeling Machine", "Packaging", "Automatic"]
            },
            {
                "id": "prod_intl_003",
                "name": "Women's Summer Maxi Dress",
                "shop_id": "shop_alibaba_003",
                "shop_name": "Fashion World Apparel",
                "category": "Apparel",
                "price": 18.5,
                "original_price": 25.0,
                "min_order": 50,
                "monthly_sales": 12000,
                "rating": 4.7,
                "reviews_count": 3450,
                "description": "Fashion women's summer maxi dress",
                "image_url": "https://example.com/dress-intl.jpg",
                "tags": ["Women Dress", "Summer", "Fashion"]
            }
        ]
    
    def search_shops(self, keyword: str = "", **kwargs) -> List[ShopInfo]:
        industry = kwargs.get("industry")
        location = kwargs.get("location")
        results = []
        for shop in self.mock_shops:
            keyword_match = not keyword or \
                           keyword.lower() in shop["name"].lower() or \
                           keyword.lower() in shop["company_name"].lower() or \
                           keyword.lower() in shop["industry"].lower() or \
                           keyword.lower() in shop["description"].lower() or \
                           any(keyword.lower() in tag.lower() for tag in shop.get("tags", []))
            industry_match = not industry or industry.lower() in shop["industry"].lower()
            location_match = not location or location.lower() in shop["location"].lower()
            if keyword_match and industry_match and location_match:
                shop["tags"] = shop.get("tags", [])
                results.append(ShopInfo(**shop))
        return sorted(results, key=lambda x: x.monthly_revenue, reverse=True)
    
    def get_shop_detail(self, shop_id: str) -> Optional[ShopInfo]:
        for shop in self.mock_shops:
            if shop["id"] == shop_id:
                shop["tags"] = shop.get("tags", [])
                return ShopInfo(**shop)
        return None
    
    def search_products(self, keyword: str = "", **kwargs) -> List[ProductInfo]:
        category = kwargs.get("category")
        min_price = kwargs.get("min_price", 0)
        max_price = kwargs.get("max_price", float('inf'))
        results = []
        for product in self.mock_products:
            keyword_match = not keyword or \
                           keyword.lower() in product["name"].lower() or \
                           keyword.lower() in product["description"].lower() or \
                           any(keyword.lower() in tag.lower() for tag in product.get("tags", []))
            category_match = not category or category.lower() in product["category"].lower()
            price_match = min_price <= product["price"] <= max_price
            if keyword_match and category_match and price_match:
                product["tags"] = product.get("tags", [])
                results.append(ProductInfo(**product))
        return sorted(results, key=lambda x: x.monthly_sales, reverse=True)


class IndependentShopMock(ECommerceSource):
    """独立站模拟数据源"""
    
    def __init__(self):
        self.mock_shops = self._load_mock_shops()
        self.mock_products = self._load_mock_products()
    
    def _load_mock_shops(self) -> List[Dict]:
        return [
            {
                "id": "shop_indep_001",
                "name": "TechGear Pro",
                "company_name": "深圳科技装备有限公司",
                "shop_type": "独立站",
                "platform": "independent",
                "industry": "消费电子",
                "main_category": "Electronics",
                "sub_category": "Gadgets",
                "location": "广东省深圳市",
                "established_year": "2019",
                "staff_count": "50-100人",
                "annual_revenue": "5000万-1亿",
                "contact_name": "Alex Zhang",
                "contact_phone": "13800138001",
                "contact_email": "alex@techgear-pro.com",
                "website": "https://www.techgear-pro.com",
                "description": "专业消费电子独立站，销售智能穿戴、智能家居产品",
                "products_count": 850,
                "monthly_orders": 6800,
                "monthly_revenue": 4200000.0,
                "rating": 4.8,
                "response_rate": 97.5,
                "trade_assurance": False,
                "gold_supplier": False,
                "verified_supplier": True,
                "tags": ["消费电子", "独立站", "DTC", "智能穿戴"]
            },
            {
                "id": "shop_indep_002",
                "name": "GreenLiving Store",
                "company_name": "上海绿色生活有限公司",
                "shop_type": "独立站",
                "platform": "independent",
                "industry": "家居用品",
                "main_category": "Home & Garden",
                "sub_category": "Eco Products",
                "location": "上海市",
                "established_year": "2020",
                "staff_count": "30-50人",
                "annual_revenue": "2000万-5000万",
                "contact_name": "Emma Wang",
                "contact_phone": "13900139002",
                "contact_email": "emma@greenliving-store.com",
                "website": "https://www.greenliving-store.com",
                "description": "环保家居用品独立站，提供绿色环保生活解决方案",
                "products_count": 420,
                "monthly_orders": 3200,
                "monthly_revenue": 1800000.0,
                "rating": 4.9,
                "response_rate": 98.8,
                "trade_assurance": False,
                "gold_supplier": False,
                "verified_supplier": True,
                "tags": ["环保", "家居", "独立站", "绿色"]
            },
            {
                "id": "shop_indep_003",
                "name": "FitStyle Active",
                "company_name": "广州运动时尚有限公司",
                "shop_type": "独立站",
                "platform": "independent",
                "industry": "运动户外",
                "main_category": "Sports",
                "sub_category": "Activewear",
                "location": "广东省广州市",
                "established_year": "2021",
                "staff_count": "50-100人",
                "annual_revenue": "5000万-1亿",
                "contact_name": "James Chen",
                "contact_phone": "13700137003",
                "contact_email": "james@fitstyle-active.com",
                "website": "https://www.fitstyle-active.com",
                "description": "运动服饰独立站，提供高品质运动服装和装备",
                "products_count": 680,
                "monthly_orders": 5400,
                "monthly_revenue": 3500000.0,
                "rating": 4.8,
                "response_rate": 96.2,
                "trade_assurance": False,
                "gold_supplier": False,
                "verified_supplier": True,
                "tags": ["运动", "服饰", "独立站", "健身"]
            }
        ]
    
    def _load_mock_products(self) -> List[Dict]:
        return [
            {
                "id": "prod_indep_001",
                "name": "Smart Watch Pro X",
                "shop_id": "shop_indep_001",
                "shop_name": "TechGear Pro",
                "category": "Electronics",
                "price": 599.0,
                "original_price": 799.0,
                "min_order": 1,
                "monthly_sales": 1200,
                "rating": 4.8,
                "reviews_count": 890,
                "description": "高端智能手表，支持健康监测、运动追踪",
                "image_url": "https://example.com/smartwatch.jpg",
                "tags": ["Smart Watch", "Wearable", "Health"]
            },
            {
                "id": "prod_indep_002",
                "name": "Bamboo Eco Toothbrush Set",
                "shop_id": "shop_indep_002",
                "shop_name": "GreenLiving Store",
                "category": "Home & Garden",
                "price": 25.0,
                "original_price": 35.0,
                "min_order": 1,
                "monthly_sales": 2800,
                "rating": 4.9,
                "reviews_count": 1560,
                "description": "环保竹制牙刷套装，可降解材料",
                "image_url": "https://example.com/bamboo.jpg",
                "tags": ["Eco", "Bamboo", "Toothbrush"]
            },
            {
                "id": "prod_indep_003",
                "name": "Premium Yoga Leggings",
                "shop_id": "shop_indep_003",
                "shop_name": "FitStyle Active",
                "category": "Sports",
                "price": 128.0,
                "original_price": 168.0,
                "min_order": 1,
                "monthly_sales": 1800,
                "rating": 4.7,
                "reviews_count": 670,
                "description": "高品质瑜伽裤，透气舒适",
                "image_url": "https://example.com/yoga.jpg",
                "tags": ["Yoga", "Leggings", "Activewear"]
            }
        ]
    
    def search_shops(self, keyword: str = "", **kwargs) -> List[ShopInfo]:
        industry = kwargs.get("industry")
        location = kwargs.get("location")
        results = []
        for shop in self.mock_shops:
            keyword_match = not keyword or \
                           keyword.lower() in shop["name"].lower() or \
                           keyword.lower() in shop["company_name"].lower() or \
                           keyword.lower() in shop["industry"].lower() or \
                           keyword.lower() in shop["description"].lower() or \
                           any(keyword.lower() in tag.lower() for tag in shop.get("tags", []))
            industry_match = not industry or industry.lower() in shop["industry"].lower()
            location_match = not location or location.lower() in shop["location"].lower()
            if keyword_match and industry_match and location_match:
                shop["tags"] = shop.get("tags", [])
                results.append(ShopInfo(**shop))
        return sorted(results, key=lambda x: x.monthly_revenue, reverse=True)
    
    def get_shop_detail(self, shop_id: str) -> Optional[ShopInfo]:
        for shop in self.mock_shops:
            if shop["id"] == shop_id:
                shop["tags"] = shop.get("tags", [])
                return ShopInfo(**shop)
        return None
    
    def search_products(self, keyword: str = "", **kwargs) -> List[ProductInfo]:
        category = kwargs.get("category")
        min_price = kwargs.get("min_price", 0)
        max_price = kwargs.get("max_price", float('inf'))
        results = []
        for product in self.mock_products:
            keyword_match = not keyword or \
                           keyword.lower() in product["name"].lower() or \
                           keyword.lower() in product["description"].lower() or \
                           any(keyword.lower() in tag.lower() for tag in product.get("tags", []))
            category_match = not category or category.lower() in product["category"].lower()
            price_match = min_price <= product["price"] <= max_price
            if keyword_match and category_match and price_match:
                product["tags"] = product.get("tags", [])
                results.append(ProductInfo(**product))
        return sorted(results, key=lambda x: x.monthly_sales, reverse=True)


class DataMiningConfig:
    """数据挖掘配置"""
    
    def __init__(self):
        self.tianyancha_api_key = None
        self.qichacha_api_key = None
        self.use_real_api = False
        self.request_timeout = 30
        self.ecommerce_platforms = []
    
    def load_from_env(self):
        import os
        self.tianyancha_api_key = os.environ.get("TIANYANCHA_API_KEY")
        self.qichacha_api_key = os.environ.get("QICHACHA_API_KEY")
        self.use_real_api = os.environ.get("USE_REAL_API", "false").lower() == "true"
        platforms = os.environ.get("ECOMMERCE_PLATFORMS", "")
        if platforms:
            self.ecommerce_platforms = [p.strip() for p in platforms.split(",")]
    
    def load_from_file(self, config_path: str):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                self.tianyancha_api_key = config.get("tianyancha_api_key")
                self.qichacha_api_key = config.get("qichacha_api_key")
                self.use_real_api = config.get("use_real_api", False)
                self.ecommerce_platforms = config.get("ecommerce_platforms", [])
        except Exception as e:
            print(f"加载配置文件失败: {e}")


class DataMiningService:
    """数据挖掘服务"""
    
    def __init__(self, config: DataMiningConfig = None):
        self.config = config or DataMiningConfig()
        self.company_sources: Dict[str, DataSource] = {}
        self.ecommerce_sources: Dict[str, ECommerceSource] = {}
        self.tender_crawler = TenderCrawler(self.config.use_real_api)
        self.recruitment_analyzer = RecruitmentAnalyzer(self.config.use_real_api)
        self._init_company_sources()
        self._init_ecommerce_sources()
    
    def _init_company_sources(self):
        if self.config.use_real_api:
            if self.config.tianyancha_api_key:
                self.company_sources["tianyancha"] = TianYanChaAPI(self.config.tianyancha_api_key)
            if self.config.qichacha_api_key:
                self.company_sources["qichacha"] = QiChaChaAPI(self.config.qichacha_api_key)
        
        if not self.company_sources:
            self.company_sources["tianyancha"] = TianYanChaMock()
            self.company_sources["qichacha"] = QiChaChaMock()
    
    def _init_ecommerce_sources(self):
        platforms = self.config.ecommerce_platforms or ["1688", "alibaba", "independent"]
        if "1688" in platforms:
            self.ecommerce_sources["1688"] = Alibaba1688Mock()
        if "alibaba" in platforms:
            self.ecommerce_sources["alibaba"] = AlibabaInternationalMock()
        if "independent" in platforms:
            self.ecommerce_sources["independent"] = IndependentShopMock()
    
    def search_companies(self, keyword: str = "", industry: str = "", source: str = "all") -> List[CompanyInfo]:
        results = []
        sources = self.company_sources.keys() if source == "all" else [source]
        for src in sources:
            if src in self.company_sources:
                results.extend(self.company_sources[src].search_companies(keyword, industry=industry))
        seen = set()
        unique_results = []
        for r in results:
            if r.name not in seen:
                seen.add(r.name)
                unique_results.append(r)
        return unique_results
    
    def get_company_detail(self, company_id: str, source: str = "all") -> Optional[CompanyInfo]:
        sources = self.company_sources.keys() if source == "all" else [source]
        for src in sources:
            if src in self.company_sources:
                result = self.company_sources[src].get_company_detail(company_id)
                if result:
                    return result
        return None
    
    def get_tenders(self, keyword: str = "", region: str = "", days: int = 7, industry: str = "") -> List[TenderInfo]:
        return self.tender_crawler.crawl_tenders(keyword, region, days, industry)
    
    def get_recruitments(self, keyword: str = "", location: str = "", industry: str = "") -> List[RecruitmentInfo]:
        return self.recruitment_analyzer.analyze_recruitment(keyword, location, industry)
    
    def search_shops(self, keyword: str = "", platform: str = "all", industry: str = "", location: str = "") -> List[ShopInfo]:
        results = []
        platforms = self.ecommerce_sources.keys() if platform == "all" else [platform]
        for p in platforms:
            if p in self.ecommerce_sources:
                results.extend(self.ecommerce_sources[p].search_shops(keyword, industry=industry, location=location))
        return sorted(results, key=lambda x: x.monthly_revenue, reverse=True)
    
    def get_shop_detail(self, shop_id: str, platform: str = "all") -> Optional[ShopInfo]:
        platforms = self.ecommerce_sources.keys() if platform == "all" else [platform]
        for p in platforms:
            if p in self.ecommerce_sources:
                result = self.ecommerce_sources[p].get_shop_detail(shop_id)
                if result:
                    return result
        return None
    
    def search_products(self, keyword: str = "", platform: str = "all", category: str = "", min_price: float = 0, max_price: float = float('inf')) -> List[ProductInfo]:
        results = []
        platforms = self.ecommerce_sources.keys() if platform == "all" else [platform]
        for p in platforms:
            if p in self.ecommerce_sources:
                results.extend(self.ecommerce_sources[p].search_products(keyword, category=category, min_price=min_price, max_price=max_price))
        return sorted(results, key=lambda x: x.monthly_sales, reverse=True)
    
    def discover_leads(self, keyword: str = "", industry: str = "", location: str = "") -> Dict[str, List]:
        leads = {
            "companies": self.search_companies(keyword, industry),
            "tenders": self.get_tenders(keyword, location, industry=industry),
            "recruitments": self.get_recruitments(keyword, location, industry),
            "shops": self.search_shops(keyword, industry=industry, location=location)
        }
        return leads


_data_mining_service = None


def get_data_mining_service(config: DataMiningConfig = None) -> DataMiningService:
    """获取数据挖掘服务实例（单例）"""
    global _data_mining_service
    if _data_mining_service is None:
        _data_mining_service = DataMiningService(config)
    return _data_mining_service