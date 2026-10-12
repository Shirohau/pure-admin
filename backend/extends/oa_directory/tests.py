"""通讯录入库与已验签免登身份的关联检查；HTTP 上游为明确标注的桩。"""
import base64
import hashlib
import json
import os
import struct
import uuid
from io import StringIO
from unittest.mock import patch

from Crypto.Cipher import AES
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.system.models import DeptModel, UserModel, RoleModel
from extends.oauth2.models import UserOAuthModel
from extends.oa_sso import service as sso
from extends.oa_directory.models import DirectorySource, DirectoryDepartment, DirectoryMember, DirectoryEvent
from extends.oa_directory.sync import DirectoryClient, DirectorySyncError
from extends.oa_directory.store import (source_configuration, remember_verified_connection, import_snapshot,
    claim_source, release_source, capture_event, process_events, deactivate_member, upsert_member)
from extends.oa_events import receiver

APP_ID = 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee'
DEPT_ID = 'bbbbbbbb-cccc-4ddd-8eee-ffffffffffff'
ENV = {'OA_SSO_ENABLED': '1', 'OA_ISSUER': 'https://ecp.test', 'OA_CLIENT_ID': 'unit-client',
    'OA_CLIENT_SECRET': 'unit-secret', 'OA_APP_ORIGIN': 'https://app.test', 'OA_REDIRECT_URI': 'https://app.test/',
    'OA_STORE_ENCRYPTION_KEY': '11' * 32, 'OA_DIRECTORY_SYNC_ENABLED': '1', 'OA_EVENT_APP_ID': APP_ID,
    'OA_EVENT_TOKEN': 'unitEventToken', 'OA_EVENT_AES_KEY': base64.b64encode(b'x' * 32).decode().rstrip('=')}


class CurrentDetailsStub:
    def __init__(self, member):
        self.member = member
        self.paths = []

    def authenticate(self):
        pass

    def call(self, method, path, body=None):
        self.paths.append(path)
        if path == '/topapi/v2/user/get':
            return {'result': self.member}
        raise AssertionError('非预期的上游接口')


class DirectoryAdapterTests(TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, ENV)
        self.env.start()
        sso.config.cache_clear()
        self.old_dept = DeptModel.add_root(name='原有部门', code='original')
        self.admin = UserModel.objects.create(username='local-admin', name='管理员', is_staff=True,
            is_superuser=True, dept=self.old_dept)
        self.admin.set_password('unit-admin-password')
        self.admin.save(update_fields=['password'])
        remember_verified_connection({'app_id': APP_ID, 'tenant_id': 1})
        self.source = source_configuration()
        self.detail = {'userid': 'm_unit_1', 'name': '同步人员', 'title': '测试岗位', 'dept_id_list': [DEPT_ID]}
        self.snapshot = {'departments': [{'dept_id': '1', 'name': '企业', 'parent_id': '1'},
            {'dept_id': DEPT_ID, 'name': 'ECP 部门', 'parent_id': '1'}], 'members': [self.detail],
            'summary': {'department_count': 1, 'member_count': 1}}

    def tearDown(self):
        sso.config.cache_clear()
        self.env.stop()

    def full(self, snapshot=None):
        token = claim_source(self.source)
        try:
            return import_snapshot(self.source, snapshot or self.snapshot, token, replace_organization=True)
        finally:
            release_source(self.source, token)

    def identity(self):
        return {'tenant_id': '1', 'sub': 'trusted-subject', 'member_uid': 'm_unit_1'}

    def legacy_binding(self):
        user = UserModel.objects.create(username='old-oa-user', name='既有免登人员', dept=self.old_dept)
        user.set_unusable_password()
        user.save(update_fields=['password'])
        subject = {'issuer': ENV['OA_ISSUER'], 'tenant_id': '1', 'sub': 'trusted-subject'}
        uid = hashlib.sha256(json.dumps(subject, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        UserOAuthModel.objects.create(user=user, platform='oa_sso', uid=uid, uinfo={'identity': subject})
        role = RoleModel.objects.create(name='原有角色', code='original-role')
        user.role.add(role)
        return user

    def event(self, version=1, kind='directory.user.updated'):
        return {'id': str(uuid.uuid4()), 'app_id': APP_ID, 'tenant_id': 1, 'type': kind,
            'data': {'object_type': 'member', 'object_id': 'm_unit_1', 'version': version}}

    def test_client_reuses_existing_sso_configuration(self):
        client = DirectoryClient(ENV)
        self.assertEqual(client.base, 'https://ecp.test/api/platform')
        self.assertEqual((client.key, client.secret), ('unit-client', 'unit-secret'))

    def test_company_can_be_inferred_from_verified_login_binding(self):
        self.legacy_binding()
        DirectorySource.objects.update(tenant_id=None)
        self.assertEqual(source_configuration().tenant_id, 1)

    def test_full_replaces_visible_departments_and_keeps_administrator(self):
        self.full()
        self.admin.refresh_from_db()
        self.old_dept.refresh_from_db()
        self.assertFalse(self.old_dept.status)
        self.assertTrue(self.admin.is_active and self.admin.is_superuser and self.admin.has_usable_password())
        self.assertIsNone(self.admin.dept_id)
        self.assertEqual(DeptModel.objects.filter(status=True).count(), 2)
        member = DirectoryMember.objects.get(uid='m_unit_1')
        self.assertEqual(member.native.name, '同步人员')
        self.assertFalse(member.native.has_usable_password())
        self.assertFalse(member.native.role.exists())

    def test_repeated_full_preserves_native_identifiers(self):
        self.full()
        first = DirectoryMember.objects.get(uid='m_unit_1').native_id
        department = DirectoryDepartment.objects.get(uid=DEPT_ID).native_id
        self.full()
        self.assertEqual(DirectoryMember.objects.get(uid='m_unit_1').native_id, first)
        self.assertEqual(DirectoryDepartment.objects.get(uid=DEPT_ID).native_id, department)

    def test_first_login_reuses_imported_person(self):
        self.full()
        native = DirectoryMember.objects.get(uid='m_unit_1').native
        user = sso.mapped_user(self.identity(), create=True)
        self.assertEqual(user.pk, native.pk)
        self.assertEqual(UserModel.objects.count(), 2)

    def test_existing_login_preserves_identity_role_and_history(self):
        old = self.legacy_binding()
        self.full()
        placeholder = DirectoryMember.objects.get(uid='m_unit_1').native
        user = sso.mapped_user(self.identity(), create=True)
        self.assertEqual(user.pk, old.pk)
        self.assertEqual(user.role.count(), 1)
        self.assertEqual(DirectoryMember.objects.get(uid='m_unit_1').native_id, old.pk)
        placeholder.refresh_from_db()
        self.assertFalse(placeholder.is_active)
        self.assertEqual(user.dept_id, DirectoryDepartment.objects.get(uid=DEPT_ID).native_id)

    def test_local_manual_suspension_is_not_reset_by_directory_update(self):
        old = self.legacy_binding()
        UserOAuthModel.objects.filter(user=old).update(uinfo={'identity': {
            'issuer': ENV['OA_ISSUER'], 'tenant_id': '1', 'sub': 'trusted-subject'}, 'member_uid': 'm_unit_1'})
        self.full()
        UserModel.objects.filter(pk=old.pk).update(is_active=False)
        upsert_member(self.source, {**self.detail, 'name': '已修改姓名'}, 2)
        old.refresh_from_db()
        self.assertFalse(old.is_active)

    def test_scope_withdrawal_clears_department_but_keeps_login(self):
        self.full()
        user = sso.mapped_user(self.identity(), create=True)
        deactivate_member(self.source, 'm_unit_1', 2)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertIsNone(user.dept_id)

    def test_resignation_and_rehire_reuse_same_user(self):
        self.full()
        user = sso.mapped_user(self.identity(), create=True)
        deactivate_member(self.source, 'm_unit_1', 2, resigned=True)
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        upsert_member(self.source, self.detail, 3)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertEqual(DirectoryMember.objects.get(uid='m_unit_1').native_id, user.pk)

    def test_duplicate_and_conflicting_event_identifiers(self):
        event = self.event()
        first = capture_event(event)
        self.assertEqual(capture_event(event).pk, first.pk)
        event['data']['version'] = 2
        with self.assertRaises(ValueError):
            capture_event(event)
        self.assertEqual(DirectoryEvent.objects.count(), 1)

    def test_events_wait_for_first_full(self):
        capture_event(self.event())
        result = process_events(self.source, CurrentDetailsStub(self.detail))
        self.assertTrue(result['waiting_for_initial_sync'])
        self.assertEqual(DirectoryMember.objects.count(), 0)

    def test_event_queries_current_details_and_ignores_older_version(self):
        self.full()
        capture_event(self.event(3))
        capture_event(self.event(1))
        stub = CurrentDetailsStub({**self.detail, 'name': '最新姓名'})
        result = process_events(self.source, stub)
        self.assertEqual((result['applied'], result['skipped']), (1, 1))
        self.assertEqual(DirectoryMember.objects.get(uid='m_unit_1').native.name, '最新姓名')
        self.assertEqual(stub.paths, ['/topapi/v2/user/get'])

    def test_department_event_updates_sibling_order_without_recreating_nodes(self):
        other = 'cccccccc-dddd-4eee-8fff-aaaaaaaaaaaa'
        snapshot = {**self.snapshot, 'departments': [
            {**self.snapshot['departments'][0], '_child_ids': [DEPT_ID, other]},
            {**self.snapshot['departments'][1], 'order': 1},
            {'dept_id': other, 'parent_id': '1', 'name': '另一个部门', 'order': 2}]}
        self.full(snapshot)
        native_id = DirectoryDepartment.objects.get(uid=DEPT_ID).native_id
        event = self.event(kind='directory.department.updated')
        event['data'] = {'object_type': 'department', 'object_id': DEPT_ID, 'version': 1}
        capture_event(event)
        stub = CurrentDetailsStub(None)
        def reply(method, path, body=None):
            if path.endswith('/department/get'):
                return {'result': {**snapshot['departments'][1], 'order': 3}}
            if path.endswith('/department/listsubid'):
                return {'result': {'dept_id_list': [other, DEPT_ID] if body['dept_id'] == '1' else []}}
            raise AssertionError('非预期的上游接口')
        stub.call = reply
        process_events(self.source, stub)
        self.assertEqual(DirectoryDepartment.objects.get(uid=DEPT_ID).native_id, native_id)
        actual = list(DirectoryDepartment.objects.filter(parent_uid='1', active=True).order_by('native__path').values_list('uid', flat=True))
        self.assertEqual(actual, [other, DEPT_ID])

    def test_login_during_full_is_associated_by_worker_later(self):
        old = self.legacy_binding()
        self.full()
        token = claim_source(self.source)
        try:
            self.assertEqual(sso.mapped_user(self.identity(), create=True).pk, old.pk)
            self.assertTrue(UserOAuthModel.objects.get(user=old).uinfo['directory_pending'])
        finally:
            release_source(self.source, token)
        process_events(self.source, CurrentDetailsStub(self.detail))
        self.assertEqual(DirectoryMember.objects.get(uid='m_unit_1').native_id, old.pk)
        self.assertFalse(UserOAuthModel.objects.get(user=old).uinfo['directory_pending'])

    def test_failed_pull_does_not_replace_old_organization(self):
        with patch('extends.oa_directory.management.commands.sync_ecp_directory.DirectoryClient') as client:
            client.return_value.pull.side_effect = DirectorySyncError('请求失败')
            with self.assertRaises(CommandError):
                call_command('sync_ecp_directory', replace_organization=True, stdout=StringIO())
        self.old_dept.refresh_from_db()
        self.assertTrue(self.old_dept.status)
        self.assertEqual(DirectoryMember.objects.count(), 0)

    def test_partial_scope_is_rejected_before_department_traversal(self):
        client = DirectoryClient(ENV)
        with patch.object(client, 'authenticate'), patch.object(client, 'call', return_value={
            'auth_org_scopes': {'authed_dept': [DEPT_ID], 'authed_user': []}, 'auth_user_field': []}):
            with self.assertRaisesRegex(DirectorySyncError, '全部通讯录范围'):
                client.pull()

    def test_encrypted_callback_persists_before_success_response(self):
        event = self.event()
        app, token, key = receiver.configuration()
        raw = json.dumps(event).encode()
        frame = b'x' * 16 + struct.pack('!I', len(raw)) + raw + app.encode()
        padding = 32 - len(frame) % 32
        encrypted = base64.b64encode(AES.new(key, AES.MODE_CBC, key[:16]).encrypt(frame + bytes([padding]) * padding)).decode()
        import time
        timestamp, nonce = str(int(time.time())), 'unit-nonce'
        signature = receiver.signature(token, timestamp, nonce, encrypted)
        with patch.object(receiver, 'record'):
            response = self.client.post(f'/oa-events/callback/?timestamp={timestamp}&nonce={nonce}&signature={signature}',
                json.dumps({'encrypt': encrypted}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(DirectoryEvent.objects.get(event_id=event['id']).state, 'pending')
        ack = response.json()
        plain = AES.new(key, AES.MODE_CBC, key[:16]).decrypt(base64.b64decode(ack['encrypt']))
        self.assertEqual(plain[20:27], b'success')
        self.assertEqual(ack['msg_signature'], receiver.signature(token, ack['timeStamp'], ack['nonce'], ack['encrypt']))
