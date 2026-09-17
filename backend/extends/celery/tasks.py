from celery import shared_task


@shared_task(acks_late=False)
def task__one(*args, **kwargs):
    """task__one 任务"""
    print(11111)
    return "task__one"


task__one.verbose_name = "我是one任务"


@shared_task
def task__two(*args, **kwargs):
    """task__two 任务"""
    print(22222)
    return 2


@shared_task
def task__three(*args, **kwargs):
    """task__three 任务"""
    print(33333)
    return {"name": "task__three"}


@shared_task
def task__four(*args, **kwargs):
    """task__four 任务"""
    print(44444)
    return "task__four"
