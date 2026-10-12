import json
import os
import time

from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections, DatabaseError
from extends.oa_directory.store import source_configuration, process_events
from extends.oa_directory.sync import DirectoryClient, DirectorySyncError


class Command(BaseCommand):
    help = '处理已保存的通讯录事件，通过详情接口更新本地组织架构'

    def add_arguments(self, parser):
        parser.add_argument('--watch', action='store_true')
        parser.add_argument('--interval', type=float, default=2)
        parser.add_argument('--limit', type=int, default=100)

    def handle(self, *args, **options):
        if not 0.2 <= options['interval'] <= 60 or not 1 <= options['limit'] <= 1000:
            raise CommandError('处理数量应为 1 到 1000，间隔应为 0.2 到 60 秒')
        client = DirectoryClient(os.environ)
        while True:
            close_old_connections()
            try:
                result = process_events(source_configuration(), client, options['limit'])
            except (DirectorySyncError, DatabaseError) as exc:
                if not options['watch']:
                    raise CommandError(str(exc)) from None
                self.stderr.write(str(exc) if isinstance(exc, DirectorySyncError) else '数据库暂时无法访问，稍后重试')
            else:
                if any(result.values()) or not options['watch']:
                    self.stdout.write(json.dumps(result, ensure_ascii=False))
                    self.stdout.flush()
            if not options['watch']:
                return
            time.sleep(options['interval'])
