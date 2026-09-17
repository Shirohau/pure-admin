#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：resources.py
@Author  ：李小涛
@Date    ：2026/8/3
@Explain : 出版社导入导出资源（同步/异步通用）
"""
from import_export.fields import Field

from extends.drf.resources import CustomCeleryResource
from .filters import PublisherFilter
from .models import PublisherModel


class PublisherResource(CustomCeleryResource):
    """出版社导入导出资源（同步/异步通用）"""

    filterset_class = PublisherFilter

    # 导入模板示例数据（下载模板时包含示例行）
    examples_data = [
        {"出版社名称": "人民文学出版社", "省份": "北京", "城市": "北京", "区县": "东城区", "详细地址": "朝内大街166号",
         "联系电话": "010-65132849", "邮箱": "info@rwxsw.com", "官网网址": "https://www.rwxsw.com"},
        {"出版社名称": "上海译文出版社", "省份": "上海", "城市": "上海", "区县": "黄浦区", "详细地址": "福建中路193号",
         "联系电话": "021-63221111", "邮箱": "contact@yiwen.com", "官网网址": "https://www.yiwen.com"},
        {"出版社名称": "浙江文艺出版社", "省份": "浙江", "城市": "杭州", "区县": "西湖区", "详细地址": "天目山路148号",
         "联系电话": "0571-85179876", "邮箱": "service@zjwy.com", "官网网址": "https://www.zjwy.com"},
    ]

    # 导入模板列宽配置（xlsx 格式生效）
    import_column_widths = {
        "出版社名称": 15,
        "省份": 8,
        "城市": 8,
        "区县": 15,
        "详细地址": 40,
        "联系电话": 15,
        "邮箱": 15,
        "官网网址": 15,
    }

    name = Field(attribute="name", column_name="出版社名称")
    province = Field(attribute="province", column_name="省份")
    city = Field(attribute="city", column_name="城市")
    district = Field(attribute="district", column_name="区县")
    address = Field(attribute="address", column_name="详细地址")
    phone = Field(attribute="phone", column_name="联系电话")
    email = Field(attribute="email", column_name="邮箱")
    website = Field(attribute="website", column_name="官网网址")

    class Meta:
        model = PublisherModel
        fields = ("name", "province", "city", "district", "address", "phone", "email", "website")
        import_id_fields = ["name"]
        use_bulk = False
        batch_size = 100
        skip_unchanged = True
