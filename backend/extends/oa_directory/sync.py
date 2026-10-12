"""参考钉钉调用顺序，从 ECP 拉取授权范围内的当前通讯录。"""
import argparse
import json
import os
import tempfile
import time
from collections import Counter, deque
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler


class DirectorySyncError(RuntimeError):
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code


class NoRedirect(HTTPRedirectHandler):
    # 凭证与成员资料只能发送给配置的服务，不能由 HTTP 重定向转发。
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def load_env(path):
    values = {}
    for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        key, separator, value = line.partition('=')
        if not separator or not key.startswith('OA_'):
            raise DirectorySyncError('配置文件只允许 OA_ 开头的应用接入配置项')
        values[key] = value[1:-1] if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'") else value
    return values


class DirectoryClient:
    def __init__(self, config):
        issuer = config.get('OA_ISSUER', '').rstrip('/')
        self.base = config.get('OA_DIRECTORY_BASE_URL', issuer + '/api/platform' if issuer else '').rstrip('/')
        parsed = urlsplit(self.base)
        if (not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment
                or '\\' in self.base or any(char.isspace() for char in self.base)):
            raise DirectorySyncError('请配置完整的 ECP 接口根地址')
        local_http = config.get('OA_DIRECTORY_LOCAL_HTTP') == '1' and parsed.hostname in {'localhost', '127.0.0.1', '::1', 'gateway', 'ecp-gateway'}
        if parsed.scheme != 'https' and not (parsed.scheme == 'http' and local_http):
            raise DirectorySyncError('接口应使用 HTTPS，本地容器测试才允许显式开启本地 HTTP')
        self.key = config.get('OA_DIRECTORY_CLIENT_ID') or config.get('OA_CLIENT_ID', '')
        self.secret = config.get('OA_DIRECTORY_CLIENT_SECRET') or config.get('OA_CLIENT_SECRET', '')
        if issuer and (self.key != config.get('OA_CLIENT_ID') or
                       (not local_http and (urlsplit(issuer).hostname, urlsplit(issuer).port or 443) != (parsed.hostname, parsed.port or 443))):
            raise DirectorySyncError('通讯录同步应复用当前免登应用的凭据和 ECP 来源')
        if not self.key or not self.secret:
            raise DirectorySyncError('缺少 Client ID 或 Client Secret')
        self.token = None
        self.token_until = 0
        self.calls = Counter()
        # 本地回环不走系统代理；HTTPS 服务可使用部署环境的标准代理配置。
        handlers = [NoRedirect()]
        if local_http:
            handlers.append(ProxyHandler({}))
        self.opener = build_opener(*handlers)

    def authenticate(self):
        if self.token and time.monotonic() < self.token_until:
            return
        self.token = None
        token = self.call('POST', '/v1.0/oauth2/accessToken', {'appKey': self.key, 'appSecret': self.secret})
        self.token = token.get('accessToken')
        if not isinstance(self.token, str) or not self.token:
            raise DirectorySyncError('未获得有效的 accessToken')
        self.token_until = time.monotonic() + max(1, int(token.get('expireIn', 7200)) - 60)

    def call(self, method, path, body=None, refresh=True):
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        if self.token:
            headers['x-acs-dingtalk-access-token'] = self.token
        raw = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
        request = Request(self.base + path, data=raw, headers=headers, method=method)
        self.calls[f'{method} {path}'] += 1
        try:
            with self.opener.open(request, timeout=30) as response:
                value = json.load(response)
        except HTTPError as exc:
            try:
                value = json.load(exc)
                code = value.get('errcode')
            except (ValueError, AttributeError):
                code = None
            if code == 40014 and refresh and path != '/v1.0/oauth2/accessToken':
                self.token = None
                self.authenticate()
                return self.call(method, path, body, refresh=False)
            raise DirectorySyncError(f'{path} 请求失败，HTTP {exc.code}，错误码 {code}', code) from None
        except (URLError, TimeoutError, ValueError) as exc:
            raise DirectorySyncError(f'{path} 网络请求或 JSON 返回失败，请检查接口服务') from None
        if not isinstance(value, dict):
            raise DirectorySyncError(f'{path} 返回结构不正确')
        if value.get('errcode', 0) != 0:
            code = value.get('errcode')
            if code == 40014 and refresh and path != '/v1.0/oauth2/accessToken':
                self.token = None
                self.authenticate()
                return self.call(method, path, body, refresh=False)
            raise DirectorySyncError(f'{path} 请求失败，错误码 {code}', code)
        return value

    def pull(self, page_size=100):
        if not 1 <= page_size <= 100:
            raise DirectorySyncError('每页数量应为 1 到 100')
        self.authenticate()
        scopes = self.call('GET', '/auth/scopes')
        organization_scope = scopes.get('auth_org_scopes', {})
        if not isinstance(organization_scope.get('authed_dept'), list) or not isinstance(organization_scope.get('authed_user'), list):
            raise DirectorySyncError('授权范围返回结构不正确')
        if '1' not in {str(value) for value in organization_scope['authed_dept']}:
            raise DirectorySyncError('ECP 尚未为此应用开通全部通讯录范围，已停止覆盖本地组织架构')
        pending, visited = deque(['1']), set()
        departments, members, inaccessible = {}, {}, set()
        memberships_seen, extra_pages = 0, 0
        while pending:
            identifier = pending.popleft()
            if identifier in visited:
                continue
            visited.add(identifier)
            children = self.call('POST', '/topapi/v2/department/listsubid', {'dept_id': identifier})['result']['dept_id_list']
            for child in children:
                if str(child) != '-7' and str(child) not in visited:
                    pending.append(str(child))
            try:
                detail = self.call('POST', '/topapi/v2/department/get', {'dept_id': identifier})['result']
                if str(detail.get('dept_id')) != identifier:
                    raise DirectorySyncError('返回的部门编号与请求不一致')
                detail['_child_ids'] = [str(value) for value in children if str(value) != '-7']
                departments[identifier] = detail
            except DirectorySyncError as exc:
                if exc.code != 50004:
                    raise
                inaccessible.add(identifier)
                continue
            cursor, cursors = 0, set()
            while True:
                page = self.call('POST', '/topapi/v2/user/list', {'dept_id': identifier, 'cursor': cursor, 'size': page_size})['result']
                if not isinstance(page.get('list'), list) or type(page.get('has_more')) is not bool:
                    raise DirectorySyncError('成员分页返回结构不正确')
                for member in page['list']:
                    uid = member.get('userid')
                    if not isinstance(uid, str) or not uid:
                        raise DirectorySyncError('成员缺少稳定编号，停止更新本地通讯录')
                    members[uid] = member
                    memberships_seen += 1
                if not page['has_more']:
                    break
                cursor = page.get('next_cursor')
                if not cursor or cursor in cursors:
                    raise DirectorySyncError('接口返回重复或缺失的分页游标')
                cursors.add(cursor)
                extra_pages += 1
        # 单独授权成员未必属于任何授权部门，必须补查。
        for uid in organization_scope['authed_user']:
            member = self.call('POST', '/topapi/v2/user/get', {'userid': uid})['result']
            if member.get('userid') != uid:
                raise DirectorySyncError('返回的成员编号与请求不一致')
            members[uid] = member
        # 权限在拉取中变化时不保存混合范围的记录；服务端也会吊销旧凭证。
        final_scopes = self.call('GET', '/auth/scopes')
        if final_scopes != scopes:
            raise DirectorySyncError('拉取期间授权范围发生变化，请重新拉取')
        summary = {'department_count': len([uid for uid in departments if uid != '1']),
                   'member_count': len(members), 'enumerated_department_count': len(visited) - 1,
                   'skipped_department_count': len(inaccessible), 'department_membership_rows': memberships_seen,
                   'extra_member_pages': extra_pages,
                   'mobile_fields': sum('mobile' in row for row in members.values()),
                   'email_fields': sum('email' in row for row in members.values()),
                   'api_calls': dict(self.calls)}
        return {'source': self.base, 'pulled_at': datetime.now(timezone.utc).isoformat(),
                'scopes': scopes, 'departments': list(departments.values()),
                'members': list(members.values()), 'summary': summary}


def save_snapshot(path, value):
    destination = Path(path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=destination.parent, delete=False) as output:
            temporary = Path(output.name)
            json.dump(value, output, ensure_ascii=False, indent=2)
            output.write('\n')
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def main():
    parser = argparse.ArgumentParser(description='按钉钉参考流程拉取 ECP 通讯录')
    parser.add_argument('--env-file', help='可选：读取现有 .env.oa-sso；默认复用当前进程的免登环境变量')
    parser.add_argument('--output', default='backend/private/oa-directory.json')
    parser.add_argument('--page-size', type=int, default=100)
    options = parser.parse_args()
    try:
        config = {**os.environ, **(load_env(options.env_file) if options.env_file else {})}
        result = DirectoryClient(config).pull(options.page_size)
        save_snapshot(options.output, result)
    except (DirectorySyncError, OSError) as exc:
        parser.exit(1, f'拉取失败：{exc}\n')
    # 终端仅输出数量和接口调用次数，不输出人员资料或应用凭证。
    print(json.dumps({'output': str(Path(options.output).resolve()), **result['summary']}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
