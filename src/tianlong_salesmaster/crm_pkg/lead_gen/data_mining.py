"""智能寻客模块 - 公开数据挖掘

支持真实API对接和Mock模式切换
"""

import json
import time
import random
import requests
from typing import List, Dict, Optional
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


class DataSource(ABC):
    """数据源抽象基类"""
    
    @abstractmethod
    def search_companies(self, keyword: str, **kwargs) -> List[CompanyInfo]:
        """搜索公司信息"""
        pass
    
    @abstractmethod
    def get_company_detail(self, company_id: str) -> Optional[CompanyInfo]:
        """获取公司详情"""
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
        """搜索公司信息"""
        results = []
        for company in self.mock_data["companies"]:
            if keyword.lower() in company["name"].lower() or \
               keyword.lower() in company["industry"].lower() or \
               keyword.lower() in company["business_scope"].lower():
                results.append(CompanyInfo(**company))
        return results
    
    def get_company_detail(self, company_id: str) -> Optional[CompanyInfo]:
        """获取公司详情"""
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
        """发送API请求"""
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
        """搜索公司信息"""
        params = {
            "keyword": keyword,
            "pageSize": kwargs.get("page_size", 10),
            "pageNum": kwargs.get("page_num", 1)
        }
        
        data = self._make_request("/services/open/search/company", params)
        if not data:
            return self._fallback_search(keyword)
        
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
        """获取公司详情"""
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
    
    def _fallback_search(self, keyword: str) -> List[CompanyInfo]:
        """API不可用时的降级方案"""
        mock = TianYanChaMock()
        return mock.search_companies(keyword)
    
    def _fallback_detail(self, company_id: str) -> Optional[CompanyInfo]:
        """API不可用时的降级方案"""
        mock = TianYanChaMock()
        return mock.get_company_detail(company_id)


class QiChaChaMock(DataSource):
    """企查查模拟数据源"""
    
    def search_companies(self, keyword: str, **kwargs) -> List[CompanyInfo]:
        """搜索公司信息"""
        tianyancha = TianYanChaMock()
        return tianyancha.search_companies(keyword, **kwargs)
    
    def get_company_detail(self, company_id: str) -> Optional[CompanyInfo]:
        """获取公司详情"""
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
        """发送API请求"""
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
        """搜索公司信息"""
        params = {
            "keyword": keyword,
            "page_size": kwargs.get("page_size", 10),
            "page_index": kwargs.get("page_num", 1)
        }
        
        data = self._make_request("/api/search", params)
        if not data:
            return self._fallback_search(keyword)
        
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
        """获取公司详情"""
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
    
    def _fallback_search(self, keyword: str) -> List[CompanyInfo]:
        """API不可用时的降级方案"""
        mock = TianYanChaMock()
        return mock.search_companies(keyword)
    
    def _fallback_detail(self, company_id: str) -> Optional[CompanyInfo]:
        """API不可用时的降级方案"""
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
    
    def crawl_tenders(self, keyword: str = "", region: str = "", days: int = 7) -> List[TenderInfo]:
        """抓取招标信息"""
        if self.use_real_api:
            return self._crawl_real_tenders(keyword, region, days)
        return self._crawl_mock_tenders(keyword, region, days)
    
    def _crawl_real_tenders(self, keyword: str = "", region: str = "", days: int = 7) -> List[TenderInfo]:
        """从真实数据源抓取招标信息"""
        results = []
        try:
            import feedparser
            rss_urls = [
                "https://www.cebpubservice.com/rss",
                "https://www.ccgp.gov.cn/rss"
            ]
            
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
                                results.append(tender)
                except Exception as e:
                    print(f"抓取RSS失败 {url}: {e}")
        except ImportError:
            print("未安装feedparser，使用mock数据")
            return self._crawl_mock_tenders(keyword, region, days)
        
        return sorted(results[:10], key=lambda x: x.publish_date, reverse=True)
    
    def _crawl_mock_tenders(self, keyword: str = "", region: str = "", days: int = 7) -> List[TenderInfo]:
        """使用mock数据"""
        results = []
        today = datetime.now()
        
        for tender in self.mock_tenders:
            publish_date = datetime.strptime(tender["publish_date"], "%Y-%m-%d")
            days_diff = (today - publish_date).days
            
            if days_diff <= days:
                if not keyword or keyword.lower() in tender["title"].lower() or keyword.lower() in tender["summary"].lower():
                    if not region or region.lower() in tender["region"].lower():
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
    
    def analyze_recruitment(self, keyword: str = "", location: str = "") -> List[RecruitmentInfo]:
        """分析招聘信息"""
        if self.use_real_api:
            return self._analyze_real_recruitment(keyword, location)
        return self._analyze_mock_recruitment(keyword, location)
    
    def _analyze_real_recruitment(self, keyword: str = "", location: str = "") -> List[RecruitmentInfo]:
        """从真实数据源获取招聘信息"""
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
                            results.append(recruitment)
                except Exception as e:
                    print(f"抓取招聘信息失败 {url}: {e}")
        except ImportError:
            print("未安装pyquery，使用mock数据")
            return self._analyze_mock_recruitment(keyword, location)
        
        return sorted(results[:10], key=lambda x: x.publish_date, reverse=True)
    
    def _analyze_mock_recruitment(self, keyword: str = "", location: str = "") -> List[RecruitmentInfo]:
        """使用mock数据"""
        results = []
        
        for recruitment in self.mock_recruitments:
            if not keyword or keyword.lower() in recruitment["title"].lower() or \
               keyword.lower() in recruitment["position"].lower() or \
               any(keyword.lower() in tag.lower() for tag in recruitment["tags"]):
                if not location or location.lower() in recruitment["location"].lower():
                    recruitment["tags"] = recruitment.get("tags", [])
                    results.append(RecruitmentInfo(**recruitment))
        
        return sorted(results, key=lambda x: x.publish_date, reverse=True)
    
    def get_hiring_companies(self) -> List[str]:
        """获取正在招聘的公司列表"""
        return list(set(r.company for r in self.mock_recruitments))


class DataMiningConfig:
    """数据挖掘配置"""
    
    def __init__(self):
        self.tianyancha_api_key = None
        self.qichacha_api_key = None
        self.use_real_api = False
        self.request_timeout = 30
    
    def load_from_env(self):
        """从环境变量加载配置"""
        import os
        self.tianyancha_api_key = os.environ.get("TIANYANCHA_API_KEY")
        self.qichacha_api_key = os.environ.get("QICHACHA_API_KEY")
        self.use_real_api = os.environ.get("USE_REAL_API", "false").lower() == "true"
    
    def load_from_file(self, config_path: str):
        """从配置文件加载"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                self.tianyancha_api_key = config.get("tianyancha_api_key")
                self.qichacha_api_key = config.get("qichacha_api_key")
                self.use_real_api = config.get("use_real_api", False)
        except Exception as e:
            print(f"加载配置文件失败: {e}")


class DataMiningService:
    """数据挖掘服务"""
    
    def __init__(self, config: DataMiningConfig = None):
        self.config = config or DataMiningConfig()
        
        # 根据配置选择数据源
        if self.config.use_real_api and self.config.tianyancha_api_key:
            self.tianyancha = TianYanChaAPI(self.config.tianyancha_api_key, self.config.request_timeout)
        else:
            self.tianyancha = TianYanChaMock()
        
        if self.config.use_real_api and self.config.qichacha_api_key:
            self.qichacha = QiChaChaAPI(self.config.qichacha_api_key, self.config.request_timeout)
        else:
            self.qichacha = TianYanChaMock()
        
        self.tender_crawler = TenderCrawler(self.config.use_real_api)
        self.recruitment_analyzer = RecruitmentAnalyzer(self.config.use_real_api)
    
    def search_companies(self, keyword: str, source: str = "all") -> List[CompanyInfo]:
        """搜索公司信息"""
        results = []
        
        if source == "all" or source == "tianyancha":
            results.extend(self.tianyancha.search_companies(keyword))
        
        if source == "all" or source == "qichacha":
            qc_results = self.qichacha.search_companies(keyword)
            existing_names = set(c.name for c in results)
            for c in qc_results:
                if c.name not in existing_names:
                    results.append(c)
        
        return results
    
    def get_company_detail(self, company_id: str, source: str = "tianyancha") -> Optional[CompanyInfo]:
        """获取公司详情"""
        if source == "qichacha":
            return self.qichacha.get_company_detail(company_id)
        return self.tianyancha.get_company_detail(company_id)
    
    def get_tenders(self, keyword: str = "", region: str = "", days: int = 7) -> List[TenderInfo]:
        """获取招标信息"""
        return self.tender_crawler.crawl_tenders(keyword, region, days)
    
    def get_recruitment(self, keyword: str = "", location: str = "") -> List[RecruitmentInfo]:
        """获取招聘信息"""
        return self.recruitment_analyzer.analyze_recruitment(keyword, location)
    
    def analyze_company_activity(self, company_name: str) -> Dict:
        """综合分析公司活跃度"""
        company = self.tianyancha.get_company_detail(company_name)
        
        recruitments = self.recruitment_analyzer.analyze_recruitment(company_name)
        tenders = self.tender_crawler.crawl_tenders(company_name)
        
        return {
            "company": company.to_dict() if company else None,
            "has_recruitment": len(recruitments) > 0,
            "recruitment_count": len(recruitments),
            "has_tender": len(tenders) > 0,
            "tender_count": len(tenders),
            "activity_score": self._calculate_activity_score(len(recruitments), len(tenders))
        }
    
    def _calculate_activity_score(self, recruitment_count: int, tender_count: int) -> int:
        """计算公司活跃度分数"""
        score = 50
        
        if recruitment_count >= 3:
            score += 30
        elif recruitment_count >= 1:
            score += 15
        
        if tender_count >= 2:
            score += 20
        elif tender_count >= 1:
            score += 10
        
        return min(score, 100)


# 全局实例
_config = DataMiningConfig()
_config.load_from_env()
data_mining_service = DataMiningService(_config)


def get_data_mining_service() -> DataMiningService:
    """获取数据挖掘服务实例"""
    return data_mining_service


def create_data_mining_service(config: DataMiningConfig) -> DataMiningService:
    """创建自定义配置的数据挖掘服务"""
    return DataMiningService(config)