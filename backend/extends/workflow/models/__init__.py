#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：__init__.py
@Explain : 审批流模型包（按模型拆分独立目录，参照 apps/system/models 组织方式）
"""
table_prefix = "workflow_"

AUDIT_STATUS = (
    (0, '进行中'),
    (1, '审核通过'),
    (2, '审核驳回'),
    (3, '审核撤销'),
)

FLOW_TYPE = (
    (0, '数据库表'),
    (1, '动态表单'),
)

from .a_flow_info.models import FlowInfoModel
from .b_flow_node.models import FlowNode
from .c_flow_data.models import FlowData
from .d_flow_record.models import FlowRecord
from .e_flow_audit_users.models import FlowAuditUsers
