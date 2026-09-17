FROM swr.cn-southwest-2.myhuaweicloud.com/muzili/vdd-base-django
WORKDIR /backend
COPY ./backend/ .
CMD ["celery", "-A", "application.celery", "worker", "-B", "--loglevel=info"]