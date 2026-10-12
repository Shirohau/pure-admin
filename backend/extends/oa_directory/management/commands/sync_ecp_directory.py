import json
import os
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from extends.oa_directory.store import source_configuration, claim_source, release_source, import_snapshot
from extends.oa_directory.sync import DirectoryClient, DirectorySyncError, save_snapshot


class Command(BaseCommand):
    help = '拉取 ECP 当前授权通讯录，导入本应用部门、用户和多部门归属'

    def add_arguments(self, parser):
        parser.add_argument('--snapshot', help='可选：同时保存此次拉取的 JSON 快照')
        parser.add_argument('--page-size', type=int, default=100)
        parser.add_argument('--dry-run', action='store_true', help='只拉取并报告数量，不修改本地组织架构')
        parser.add_argument('--replace-organization', action='store_true', help='备份后停用旧部门，让当前组织树采用 ECP 全量数据')

    def backup_native(self):
        directory = Path(settings.BASE_DIR) / 'private' / 'directory-backups'
        path = directory / (timezone.now().strftime('%Y%m%d-%H%M%S-%f') + '.json')
        data = {'created_at': timezone.now().isoformat(),
            'departments': list(apps.get_model(settings.DEPT_MODEL).objects.values(
                'id', 'name', 'code', 'status', 'owner_id', 'path', 'depth', 'numchild')),
            'users': list(apps.get_model(settings.AUTH_USER_MODEL).objects.values('id', 'name', 'dept_id', 'is_active'))}
        save_snapshot(path, data)
        os.chmod(path, 0o600)
        return str(path)

    def handle(self, *args, **options):
        source, token = None, None
        try:
            source = source_configuration()
            token = claim_source(source)
            snapshot = DirectoryClient(os.environ).pull(options['page_size'])
            if options['dry_run']:
                self.stdout.write(json.dumps({'dry_run': True, **snapshot['summary']}, ensure_ascii=False))
                return
            if source.tenant_id is None:
                raise DirectorySyncError('请先完成一次免登或验证事件连接；也可配置 OA_DIRECTORY_TENANT_ID 指定企业编号')
            backup = self.backup_native() if options['replace_organization'] else None
            result = import_snapshot(source, snapshot, token, replace_organization=options['replace_organization'])
            if backup:
                result = {**result, 'native_backup': backup}
            if options['snapshot']:
                save_snapshot(options['snapshot'], snapshot)
        except DirectorySyncError as exc:
            raise CommandError(str(exc)) from None
        finally:
            if source and token:
                release_source(source, token)
        self.stdout.write(json.dumps(result, ensure_ascii=False))
