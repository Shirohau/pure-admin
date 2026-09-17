FROM swr.cn-southwest-2.myhuaweicloud.com/muzili/vdd-base-django
WORKDIR /backend
COPY ./backend/ .
# uvicorn application.asgi:application --host 0.0.0.0 --port 8000 --workers 4
CMD ["uvicorn", "application.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]