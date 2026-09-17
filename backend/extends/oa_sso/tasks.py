from celery import shared_task
from . import service


@shared_task(ignore_result=True)
def revoke_pending():
    if service.enabled():
        service.retry_revocations()
