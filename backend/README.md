### 启动后端

```bash
# 进入后端项目目录
cd backend
# 安装依赖环境
pip install -r requirements.txt
# 执行迁移命令
python manage.py makemigrations
python manage.py migrate
# 初始化数据
python manage.py init
python manage.py init_area
# 启动服务
python manage.py runserver 0.0.0.0:8000
```

# celery 使用说明

```shell
mac/linux:
celery -A application.celery worker -B --loglevel=info

win:
# 需要安装: pip install eventlet,
# 需要启动两个程序（worker + beat 顺序不分先后）
celery -A application.celery worker -l INFO -P solo
celery -A application.celery beat --loglevel=info

# 监听celery 需要安装  pip install flower 
celery -A application.celery flower --port=5555 --address=0.0.0.0
```

多队列使用说明

```shell
celery -A application.celery worker -n celery.%h -Q celery -P eventlet --concurrency=4 --loglevel=info 
celery -A application.celery worker -n worker1.%h -Q worker1 -P eventlet  --loglevel=info
celery -A application.celery worker -n worker2.%h -Q worker2 -P eventlet  --loglevel=info
```

- `-A`：指定`celery`配置文件
- `-n`：指定新`worker`的名称
-
    - `%h`：表示运行`worker`的包含域名的完整主机名称，除了`%h`外还可以用`%n`来表示主机名，或是`%d`表示`domain`域名。
- `-Q`：指定队列名字，
- `-P`：指定`worker`的运行模式，`eventlet`是异步模式，`gevent`是同步模式，默认是`solo`模式，`solo`模式下，`worker`运行在一个线程中，不会出现多进程并发的问题，但是性能会比较低。
- `--concurrency`：控制不同队列消费的进程数量
- `--loglevel`：指定`worker`的日志级别，默认是`info`级别，可以设置为`debug`、`info`、`warning`、`error`、`critical`等

# websocket

```shell
uvicorn application.asgi:application --reload
```