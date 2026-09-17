#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：__init__.py.py
@Author  ：李小涛
@Date    ：2025/12/11 上午9:04
@Explain :
"""
table_prefix = "system_"

from .api_white.models import ApiWhiteModel
from .area.models import AreaModel
from .config.models import ConfigModel
from .dept.models import DeptModel
from .dictionary.models import DictionaryModel
from .file.models import FileModel
from .export_field_template.models import ExportFieldTemplateModel
from .log_login.models import LogLoginModel
from .log_request.models import LogRequestModel
from .menu.models import MenuModel
from .menu_button.models import MenuButtonModel
from .menu_field.models import MenuFieldModel
from .message_center.models import MessageCenter, MessageCenterTargetUser
from .role.models import RoleModel
from .role_menu_button.models import RoleMenuButtonModel
from .role_menu_field.models import RoleMenuFieldModel
from .user.models import UserModel
