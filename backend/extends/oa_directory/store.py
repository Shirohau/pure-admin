"""先全量导入，再按事件编号读取当前详情；仅修改本来源管理的记录。"""
import hashlib
import os
import uuid
from datetime import timedelta
from urllib.parse import urlsplit

from django.apps import apps
from django.conf import settings
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone

from .models import DirectorySource, DirectoryDepartment, DirectoryMember, DirectoryMembership, DirectoryEvent
from .sync import DirectorySyncError


def source_configuration():
    from extends.oauth2.models import UserOAuthModel
    from extends.oa_sso.constants import OA_BINDING_PLATFORM
    try:
        issuer = os.environ['OA_ISSUER'].strip().rstrip('/')
        parsed = urlsplit(issuer)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.path or parsed.query or parsed.fragment or parsed.username:
            raise ValueError()
        client_id = os.environ['OA_CLIENT_ID'].strip()
        if not client_id:
            raise ValueError()
        configured_app = os.getenv('OA_DIRECTORY_APP_ID') or os.getenv('OA_EVENT_APP_ID', '')
        app_id = uuid.UUID(configured_app) if configured_app else None
        configured_tenant = os.getenv('OA_DIRECTORY_TENANT_ID', '').strip()
        tenant_id = int(configured_tenant) if configured_tenant else None
        if tenant_id is not None and tenant_id < 1:
            raise ValueError()
    except (KeyError, ValueError, TypeError):
        raise DirectorySyncError('请保留有效的 OA_ISSUER、OA_CLIENT_ID；可选企业编号和 App ID 格式不正确') from None
    identifier = uuid.uuid5(uuid.NAMESPACE_URL, f'ecp-directory:{issuer}:{client_id}')
    source, _ = DirectorySource.objects.get_or_create(pk=identifier,
        defaults={'tenant_id': tenant_id, 'app_id': app_id, 'issuer': issuer, 'client_id': client_id})
    # 已免登人员的企业编号来自此前已验签的身份记录，不从姓名、网址参数推断。
    if tenant_id is None and source.tenant_id is None:
        values = list(UserOAuthModel.objects.filter(platform=OA_BINDING_PLATFORM,
            uinfo__identity__issuer=issuer).values_list('uinfo', flat=True))
        tenants = {value.get('identity', {}).get('tenant_id') for value in values if isinstance(value, dict)}
        tenants.discard(None)
        if len(tenants) == 1:
            try:
                tenant_id = int(tenants.pop())
                if tenant_id < 1:
                    raise ValueError()
            except (TypeError, ValueError):
                raise DirectorySyncError('已有免登记录中的企业编号无效') from None
    if source.issuer != issuer or source.client_id != client_id or (tenant_id and source.tenant_id and source.tenant_id != tenant_id):
        raise DirectorySyncError('应用来源企业不一致，禁止覆盖已有组织架构')
    if source.app_id and app_id and source.app_id != app_id:
        raise DirectorySyncError('事件 App ID 与此来源不一致')
    updates = {}
    if tenant_id and source.tenant_id is None:
        updates['tenant_id'] = tenant_id
    if app_id and source.app_id is None:
        updates['app_id'] = app_id
    if updates:
        DirectorySource.objects.filter(pk=source.pk, tenant_id=source.tenant_id, app_id=source.app_id).update(**updates)
        source.refresh_from_db()
    return source


def remember_verified_connection(payload):
    source = source_configuration()
    app_id = uuid.UUID(payload['app_id'])
    tenant = payload.get('tenant_id')
    if type(tenant) is not int or tenant < 1 or (source.app_id and source.app_id != app_id) or (source.tenant_id and source.tenant_id != tenant):
        raise ValueError('验证连接的应用或企业不匹配')
    changed = DirectorySource.objects.filter(pk=source.pk, app_id=source.app_id, tenant_id=source.tenant_id).update(app_id=app_id, tenant_id=tenant)
    if changed != 1:
        raise DirectorySyncError('应用来源正在更新，请重试验证连接')


def capture_event(payload):
    source = source_configuration()
    data, event_type = payload['data'], payload['type']
    object_type = 'member' if event_type.startswith('directory.user.') else 'department'
    uid, version = data.get('object_id'), data.get('version')
    if (not source.app_id or str(source.app_id) != payload.get('app_id') or source.tenant_id != payload.get('tenant_id')
            or data.get('object_type') != object_type or not isinstance(uid, str) or not 0 < len(uid) <= 80
            or type(version) is not int or not 0 < version < 2 ** 63):
        raise ValueError('事件企业、对象编号或版本不正确')
    values = dict(event_type=event_type, object_type=object_type, object_id=uid, version=version)
    row, created = DirectoryEvent.objects.get_or_create(source=source, event_id=payload['id'], defaults=values)
    if not created and any(getattr(row, key) != value for key, value in values.items()):
        raise ValueError('同一事件编号的内容不一致')
    return row


def claim_source(source):
    token, now = str(uuid.uuid4()), timezone.now()
    claimed = DirectorySource.objects.filter(pk=source.pk).filter(
        Q(claim_until__isnull=True) | Q(claim_until__lte=now)).update(
            claim_token=token, claim_until=now + timedelta(minutes=15))
    if not claimed:
        raise DirectorySyncError('此来源正在同步，请稍后再试')
    return token


def require_claim(source, token):
    # 在写入事务里再次核对租约；过期进程不能覆盖后来接管的同步结果。
    if not DirectorySource.objects.filter(pk=source.pk, claim_token=token,
            claim_until__gt=timezone.now()).update(claim_until=timezone.now() + timedelta(minutes=15)):
        raise DirectorySyncError('同步租约已失效，请重试')


def release_source(source, token):
    DirectorySource.objects.filter(pk=source.pk, claim_token=token).update(claim_token='', claim_until=None)


def organization_is_replaced():
    if os.getenv('OA_DIRECTORY_SYNC_ENABLED') != '1':
        return False
    source = source_configuration()
    return bool(source.initialized_at and source.replace_organization)


def stable_local_code(source, kind, uid):
    return ('oa_dir_' if kind == 'member' else 'oa_') + hashlib.sha256(f'{source.pk}:{kind}:{uid}'.encode()).hexdigest()[:40]


def existing_login_user(source, uid):
    from extends.oauth2.models import UserOAuthModel
    from extends.oa_sso.constants import OA_BINDING_PLATFORM
    users = list(UserOAuthModel.objects.filter(platform=OA_BINDING_PLATFORM,
        uinfo__identity__issuer=source.issuer, uinfo__identity__tenant_id=str(source.tenant_id),
        uinfo__member_uid=uid).values_list('user_id', flat=True).distinct()[:2])
    if len(users) > 1:
        raise DirectorySyncError('同一 ECP 成员关联多个本地账号，请先处理身份关联')
    return apps.get_model(settings.AUTH_USER_MODEL).objects.filter(pk=users[0]).first() if users else None


def adopt_login_user(source, row, user):
    """使用已验证的 member_uid 关联，不能合并两个既有业务账号。"""
    from extends.oauth2.models import UserOAuthModel
    if row.native_id and row.native_id != user.pk:
        previous = apps.get_model(settings.AUTH_USER_MODEL).objects.get(pk=row.native_id)
        if (previous.username != stable_local_code(source, 'member', row.uid) or previous.has_usable_password()
                or previous.is_staff or previous.is_superuser or previous.role.exists()
                or UserOAuthModel.objects.filter(user=previous).exists()):
            raise DirectorySyncError('ECP 成员已关联其他业务账号，禁止自动合并')
        apps.get_model(settings.AUTH_USER_MODEL).objects.filter(pk=previous.pk).update(is_active=False, dept=None)
    others = DirectoryMember.objects.filter(native_id=user.pk).exclude(pk=row.pk)
    if others.filter(active=True).exists():
        raise DirectorySyncError('本地账号已关联其他在职 ECP 成员')
    others.update(native=None)
    row.native = user
    row.save(update_fields=['native'])


def login_directory_user(identity):
    if os.getenv('OA_DIRECTORY_SYNC_ENABLED') != '1' or not identity.get('member_uid'):
        return None
    source = source_configuration()
    if str(source.tenant_id) != identity.get('tenant_id'):
        return None
    row = DirectoryMember.objects.filter(source=source, uid=identity['member_uid'], active=True).select_related('native').first()
    return row.native if row else None


@transaction.atomic
def associate_login(identity, user):
    if os.getenv('OA_DIRECTORY_SYNC_ENABLED') != '1' or not identity.get('member_uid'):
        return True
    source = source_configuration()
    if str(source.tenant_id) != identity.get('tenant_id'):
        return True
    row = DirectoryMember.objects.filter(source=source, uid=identity['member_uid'], active=True).first()
    if row:
        # 与同步进程共用租约，关联旧免登账号时不能同时改写其部门树。
        if source.claim_until and source.claim_until > timezone.now():
            return False
        try:
            token = claim_source(source)
        except DirectorySyncError:
            # 全量正在网络拉取时，让已经验证通过的免登继续；事件进程随后补关联。
            return False
        try:
            require_claim(source, token)
            adopt_login_user(source, row, user)
            if row.details:
                upsert_member(source, row.details, row.version)
        finally:
            release_source(source, token)
    return True


def reconcile_login_bindings(source):
    from extends.oauth2.models import UserOAuthModel
    from extends.oa_sso.constants import OA_BINDING_PLATFORM
    bindings = UserOAuthModel.objects.filter(platform=OA_BINDING_PLATFORM,
        uinfo__identity__issuer=source.issuer, uinfo__identity__tenant_id=str(source.tenant_id),
        uinfo__directory_pending=True).select_related('user')[:100]
    for binding in bindings:
        row = DirectoryMember.objects.filter(source=source, uid=binding.uinfo.get('member_uid'), active=True).first()
        if row:
            adopt_login_user(source, row, binding.user)
            if row.details:
                upsert_member(source, row.details, row.version)
        UserOAuthModel.objects.filter(pk=binding.pk, uinfo=binding.uinfo).update(
            uinfo={**binding.uinfo, 'directory_pending': False})


def upsert_department(source, detail, version=0):
    uid = str(detail['dept_id'])
    row, _ = DirectoryDepartment.objects.get_or_create(source=source, uid=uid)
    parent_uid = '' if uid == '1' else str(detail['parent_id'])
    parent = DirectoryDepartment.objects.filter(source=source, uid=parent_uid, active=True).first() if parent_uid else None
    if parent_uid and not parent:
        raise DirectorySyncError('部门上级尚未同步，等待后续重试')
    model = apps.get_model(settings.DEPT_MODEL)
    native = model.objects.filter(pk=row.native_id).first() if row.native_id else None
    if native is None:
        values = dict(name=str(detail['name'])[:64], code=stable_local_code(source, 'dept', uid), status=True)
        native = parent.native.add_child(**values) if parent else model.add_root(**values)
    else:
        current_parent = native.get_parent()
        if (current_parent.pk if current_parent else None) != (parent.native_id if parent else None):
            if parent:
                native.move(parent.native, 'last-child')
            else:
                other_root = model.get_root_nodes().exclude(pk=native.pk).last()
                if other_root:
                    native.move(other_root, 'last-sibling')
            native.refresh_from_db()
        native.name, native.status = str(detail['name'])[:64], True
        native.save(update_fields=['name', 'status', 'update_dt'])
    row.native = native
    row.parent_uid, row.details, row.active = parent_uid, detail, True
    row.version = max(row.version, version)
    row.save()
    return row


def upsert_member(source, detail, version=0):
    uid = detail['userid']
    row, _ = DirectoryMember.objects.get_or_create(source=source, uid=uid)
    user_model = apps.get_model(settings.AUTH_USER_MODEL)
    login_user = existing_login_user(source, uid)
    if login_user:
        adopt_login_user(source, row, login_user)
    user = user_model.objects.filter(pk=row.native_id).first() if row.native_id else None
    if user is None:
        # 不按姓名、手机或邮箱合并；不创建可用密码、管理员身份或角色。
        user = user_model(username=stable_local_code(source, 'member', uid), name=str(detail['name'])[:40])
        user.set_unusable_password()
        user.save()
    depts = list(dict.fromkeys(str(value) for value in detail.get('dept_id_list', [])))
    known = {d.uid: d for d in DirectoryDepartment.objects.filter(source=source, uid__in=depts, active=True)}
    # 本应用原生用户只有一个部门字段，采用返回列表中的首个可访问部门；所有归属另存关系表。
    primary = next((known[uid] for uid in depts if uid in known), None)
    user.name, user.dept_id = str(detail['name'])[:40], primary.native_id if primary else None
    if row.disabled_by_directory:
        user.is_active = True
        row.disabled_by_directory = False
    user.save(update_fields=['name', 'is_active', 'dept'])
    row.native, row.details, row.active = user, detail, True
    row.version = max(row.version, version)
    row.save()
    DirectoryMembership.objects.filter(member=row).exclude(department__uid__in=known).delete()
    for dept in known.values():
        DirectoryMembership.objects.update_or_create(member=row, department=dept,
            defaults={'is_primary': bool(primary and primary.pk == dept.pk)})
    return row


def update_owners(source):
    model = apps.get_model(settings.DEPT_MODEL)
    for dept in DirectoryDepartment.objects.filter(source=source, active=True, native__isnull=False):
        manager = DirectoryMember.objects.filter(source=source, active=True,
            uid__in=dept.details.get('dept_manager_userid_list', [])).order_by('uid').first()
        model.objects.filter(pk=dept.native_id).update(owner_id=manager.native_id if manager else None)


def reorder_departments(source):
    """物化路径树按接口返回的子部门顺序排列，保留原节点和历史引用。"""
    model = apps.get_model(settings.DEPT_MODEL)
    rows = list(DirectoryDepartment.objects.filter(source=source, active=True, native__isnull=False))
    for parent in rows:
        children = [row for row in rows if row.parent_uid == parent.uid]
        ranks = {uid: index for index, uid in enumerate(parent.details.get('_child_ids', []))}
        children.sort(key=lambda row: (ranks.get(row.uid, len(ranks)), row.details.get('order', 0), row.native_id))
        previous = None
        for child in children:
            native = model.objects.get(pk=child.native_id)
            if previous:
                previous.refresh_from_db()
                if native.path < previous.path:
                    native.move(previous, 'right')
            previous = native


def deactivate_member(source, uid, version=0, resigned=False):
    row, _ = DirectoryMember.objects.get_or_create(source=source, uid=uid)
    if row.native_id:
        from extends.oauth2.models import UserOAuthModel
        from extends.oa_sso.constants import OA_BINDING_PLATFORM
        has_login = UserOAuthModel.objects.filter(user_id=row.native_id, platform=OA_BINDING_PLATFORM).exists()
        # 收回通讯录读取范围与员工离职分别处理，不能仅因资料不可读就撤销正常免登。
        fields = {'dept': None}
        native_active = apps.get_model(settings.AUTH_USER_MODEL).objects.filter(pk=row.native_id, is_active=True).exists()
        if (resigned or not has_login) and native_active:
            fields['is_active'] = False
            row.disabled_by_directory = True
        apps.get_model(settings.AUTH_USER_MODEL).objects.filter(pk=row.native_id).update(**fields)
        apps.get_model(settings.DEPT_MODEL).objects.filter(owner_id=row.native_id).update(owner=None)
    row.memberships.all().delete()
    row.active, row.version = False, max(row.version, version)
    row.save(update_fields=['active', 'version', 'disabled_by_directory'])


def deactivate_department(source, uid, version=0):
    row, _ = DirectoryDepartment.objects.get_or_create(source=source, uid=uid)
    if row.native_id:
        apps.get_model(settings.DEPT_MODEL).objects.filter(pk=row.native_id).update(status=False, owner=None)
        affected = list(DirectoryMember.objects.filter(memberships__department=row))
        DirectoryMembership.objects.filter(department=row).delete()
        for member in affected:
            membership = member.memberships.filter(department__active=True).order_by('-is_primary', 'id').first()
            if membership:
                member.memberships.update(is_primary=False)
                DirectoryMembership.objects.filter(pk=membership.pk).update(is_primary=True)
            apps.get_model(settings.AUTH_USER_MODEL).objects.filter(pk=member.native_id).update(
                dept_id=membership.department.native_id if membership else None)
    row.active, row.version = False, max(row.version, version)
    row.save(update_fields=['active', 'version'])


def import_snapshot(source, snapshot, token, replace_organization=False):
    departments = {str(row['dept_id']): row for row in snapshot['departments']}
    members = {row['userid']: row for row in snapshot['members']}
    ordered, pending, completed = [], dict(departments), set()
    while pending:
        ready = [uid for uid, row in pending.items() if uid == '1' or str(row['parent_id']) in completed]
        if not ready:
            raise DirectorySyncError('返回的部门树缺少上级或有循环，未覆盖本地组织架构')
        for uid in ready:
            ordered.append(pending.pop(uid))
            completed.add(uid)
    with transaction.atomic():
        require_claim(source, token)
        for detail in ordered:
            upsert_department(source, detail)
        reorder_departments(source)
        for detail in members.values():
            upsert_member(source, detail)
        for uid in list(DirectoryMember.objects.filter(source=source, active=True).exclude(uid__in=members).values_list('uid', flat=True)):
            deactivate_member(source, uid)
        for uid in list(DirectoryDepartment.objects.filter(source=source, active=True).exclude(uid__in=departments).values_list('uid', flat=True)):
            deactivate_department(source, uid)
        update_owners(source)
        if replace_organization:
            # 保留旧部门及业务历史外键，当前组织树改为本次完整同步的部门。
            model = apps.get_model(settings.DEPT_MODEL)
            current_ids = DirectoryDepartment.objects.filter(source=source, active=True).values('native_id')
            old_ids = list(model.objects.exclude(pk__in=current_ids).values_list('pk', flat=True))
            model.objects.filter(pk__in=old_ids).update(status=False)
            apps.get_model(settings.AUTH_USER_MODEL).objects.filter(dept_id__in=old_ids).update(dept=None)
        DirectorySource.objects.filter(pk=source.pk, claim_token=token).update(initialized_at=timezone.now(),
            replace_organization=source.replace_organization or replace_organization)
    return snapshot['summary']


def read_department_chain(client, source, uid, collected, visiting=None, detail=None):
    if uid in collected:
        return
    visiting = set(visiting or ())
    if uid in visiting or len(visiting) >= 30:
        raise DirectorySyncError('部门上级关系有循环或层级过多')
    visiting.add(uid)
    if detail is None:
        detail = client.call('POST', '/topapi/v2/department/get', {'dept_id': uid})['result']
    if str(detail.get('dept_id')) != uid:
        raise DirectorySyncError('返回的部门编号不一致')
    parent = str(detail['parent_id'])
    if uid != '1' and parent not in collected and not DirectoryDepartment.objects.filter(source=source, uid=parent, active=True).exists():
        read_department_chain(client, source, parent, collected, visiting)
    collected[uid] = detail


def process_events(source, client, limit=100):
    source.refresh_from_db()
    if source.initialized_at is None:
        return {'applied': 0, 'waiting_for_initial_sync': True}
    token = claim_source(source)
    applied, skipped, retries = 0, 0, 0
    try:
        with transaction.atomic():
            require_claim(source, token)
            reconcile_login_bindings(source)
        events = list(DirectoryEvent.objects.filter(source=source, state='pending', next_attempt_at__lte=timezone.now())
            .order_by('received_at', 'id')[:limit])
        for event in events:
            try:
                model = DirectoryMember if event.object_type == 'member' else DirectoryDepartment
                current = model.objects.filter(source=source, uid=event.object_id).first()
                if current and current.version >= event.version:
                    with transaction.atomic():
                        require_claim(source, token)
                        DirectoryEvent.objects.filter(pk=event.pk, state='pending').update(state='skipped', processed_at=timezone.now())
                    skipped += 1
                    continue
                client.authenticate()
                depts, detail, gone = {}, None, False
                path = '/topapi/v2/user/get' if event.object_type == 'member' else '/topapi/v2/department/get'
                body = {'userid': event.object_id} if event.object_type == 'member' else {'dept_id': event.object_id}
                try:
                    detail = client.call('POST', path, body)['result']
                except DirectorySyncError as exc:
                    if exc.code in ({50004, 33012} if event.object_type == 'member' else {50004, 60003}):
                        gone = True
                    else:
                        raise
                # 上级读取失败不等于目标对象离职或删除。
                if detail and event.object_type == 'member':
                    if detail.get('userid') != event.object_id:
                        raise DirectorySyncError('返回的人员编号不一致')
                    for uid in detail.get('dept_id_list', []):
                        if not DirectoryDepartment.objects.filter(source=source, uid=str(uid), active=True).exists():
                            read_department_chain(client, source, str(uid), depts)
                elif detail:
                    read_department_chain(client, source, event.object_id, depts, detail=detail)
                child_orders = {}
                if detail and event.object_type == 'department':
                    # 自己的子部门和上级的子部门列表同时覆盖新增、移动和排序事件。
                    for uid in {event.object_id, str(detail['parent_id'])}:
                        children = client.call('POST', '/topapi/v2/department/listsubid', {'dept_id': uid})['result']['dept_id_list']
                        child_orders[uid] = [str(value) for value in children if str(value) != '-7']
                with transaction.atomic():
                    require_claim(source, token)
                    if gone:
                        if event.object_type == 'member':
                            deactivate_member(source, event.object_id, event.version, resigned=event.event_type == 'directory.user.resigned')
                        else:
                            deactivate_department(source, event.object_id, event.version)
                    else:
                        for dept in depts.values():
                            upsert_department(source, dept,
                                event.version if str(dept['dept_id']) == event.object_id and event.object_type == 'department' else 0)
                        for uid, children in child_orders.items():
                            parent = DirectoryDepartment.objects.get(source=source, uid=uid)
                            parent.details = {**parent.details, '_child_ids': children}
                            parent.save(update_fields=['details'])
                        if child_orders:
                            reorder_departments(source)
                        if event.object_type == 'member':
                            upsert_member(source, detail, event.version)
                        update_owners(source)
                    DirectoryEvent.objects.filter(pk=event.pk, state='pending').update(state='applied',
                        processed_at=timezone.now(), attempts=F('attempts') + 1, last_error='')
                applied += 1
            except DirectorySyncError as exc:
                DirectoryEvent.objects.filter(pk=event.pk, state='pending').update(attempts=F('attempts') + 1,
                    next_attempt_at=timezone.now() + timedelta(seconds=min(300, 5 * 2 ** min(event.attempts, 6))),
                    last_error=str(exc)[:300])
                retries += 1
        return {'applied': applied, 'skipped': skipped, 'retry_pending': retries}
    finally:
        release_source(source, token)
