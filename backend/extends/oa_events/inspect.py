"""在应用容器内执行 python -m extends.oa_events.inspect 查看最近接收记录。"""
import json
import os


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'application.settings')
    import django
    django.setup()
    from django_redis import get_redis_connection
    from .receiver import configuration, receipts_key
    app_id, _, _ = configuration()
    rows = get_redis_connection('default').lrange(receipts_key(app_id), 0, 99)
    print(json.dumps([json.loads(row) for row in rows], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
