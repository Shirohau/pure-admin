"""
根据Django的要求，导入本APP定义的所有模型
参考资料：https://docs.djangoproject.com/zh-hans/4.2/topics/db/models/#organizing-models-in-a-package
"""
table_prefix = "example_"

from .publisher.models import PublisherModel
from .author.models import AuthorModel
from .book.models import BookModel
