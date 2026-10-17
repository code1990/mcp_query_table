from enum import Enum


class QueryType(Enum):
    """查询类型"""
    CNStock = 'A股'
    AShareIndex = 'A股指数'
    ListedETF = '场内ETF'
    HKStock = '港股'
    HKIndex = '港股指数'
    USStock = '美股'
    USIndex = '美股指数'
    Index = '指数'
    Fund = '基金'
    FundProduct = '基金产品'
    FundManager = '基金经理'
    FundCompany = '基金公司'
    ETF = 'ETF'
    ThreeBoard = '新三板'
    ConBond = '可转债'
    Futures = '期货'
    Insurance = '保险'
    WealthManagement = '理财'
    Forex = '外汇'
    Macro = '宏观'
    Board = '板块'
    Info = '资讯'


class Site(Enum):
    """站点"""
    EastMoney = '东方财富'  # 东方财富 条件选股
    TDX = '通达信'  # 通达信 问小达
    THS = '同花顺'  # 同花顺 问财


class Provider(Enum):
    """提供商"""
    Nami = '纳米搜索'  # 360 纳米搜索
    YuanBao = '腾讯元宝'  # 腾讯元宝
    BaiDu = '百度AI搜索'  # 百度AI搜索
    # YiYan = '文心一言'  # 百度文心一言
