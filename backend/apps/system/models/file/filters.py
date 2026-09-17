from extends.drf.filters import CustomFilter
from .models import FileModel


class FileFilter(CustomFilter):
    class Meta(CustomFilter.Meta):
        model = FileModel
