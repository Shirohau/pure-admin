# 基础镜像

先公共镜像仓库([轩辕镜像](https://xuanyuan.cloud/))下载，在上传到自己的私有仓库

- MySQL 镜像
    - 下载
  ```
  docker pull docker.xuanyuan.run/library/mysql:8.0
  ```

    - 修改标签
  ```
  docker tag docker.xuanyuan.run/library/mysql:8.0 swr.cn-southwest-2.myhuaweicloud.com/muzili/mysql:8.0
  ```

    - 上传
  ```
  docker push swr.cn-southwest-2.myhuaweicloud.com/muzili/mysql:8.0 
  ```

- Redis 镜像
    - 下载
  ```
  docker pull docker.xuanyuan.run/library/redis:8.2.7
  ```

    - 修改标签
  ```
  docker tag docker.xuanyuan.run/library/redis:8.2.7 swr.cn-southwest-2.myhuaweicloud.com/muzili/redis:8.2.7
  ```

    - 上传
  ```
  docker push swr.cn-southwest-2.myhuaweicloud.com/muzili/redis:8.2.7
  ```

- Python 镜像
    - 下载
  ```
  docker pull docker.xuanyuan.run/library/python:3.11-slim
  ```

    - 修改标签
  ```
  docker tag docker.xuanyuan.run/library/python:3.11-slim swr.cn-southwest-2.myhuaweicloud.com/muzili/python:3.11-slim
  ```

    - 上传
  ```
  docker push swr.cn-southwest-2.myhuaweicloud.com/muzili/python:3.11-slim
  ```
  
- Nginx 镜像
    - 下载
  ```
  docker pull docker.xuanyuan.run/library/nginx:stable-alpine3.23-perl
  ```

    - 修改标签
  ```
  docker tag docker.xuanyuan.run/library/nginx:stable-alpine3.23-perl swr.cn-southwest-2.myhuaweicloud.com/muzili/nginx:stable-alpine3.23-perl
  ```

    - 上传
  ```
  docker push swr.cn-southwest-2.myhuaweicloud.com/muzili/nginx:stable-alpine3.23-perl
  ```

# 项目镜像

- 后端镜像
    - 构建
  ```
  # 关闭 BuildKit 并重新构建
  $env:DOCKER_BUILDKIT=0
  # 构建
  docker build -f ./ops/django/DockerfileBuild -t swr.cn-southwest-2.myhuaweicloud.com/muzili/vdd-base-django .
  ```

    - 上传
  ```
  docker push swr.cn-southwest-2.myhuaweicloud.com/muzili/vdd-base-django
  ```
  
    - 下载
  ```
  docker pull swr.cn-southwest-2.myhuaweicloud.com/muzili/vdd-base-django
  ```

- Nginx镜像
    - 构建
  ```
  # 关闭 BuildKit 并重新构建
  $env:DOCKER_BUILDKIT=0
  # 构建
  docker build -f ./ops/nginx/DockerfileBuild -t swr.cn-southwest-2.myhuaweicloud.com/muzili/vdd-base-nginx .
  ```

    - 上传
  ```
  docker push swr.cn-southwest-2.myhuaweicloud.com/muzili/vdd-base-nginx
  ```
  
    - 下载
  ```
  docker pull swr.cn-southwest-2.myhuaweicloud.com/muzili/vdd-base-nginx
  ```


数据库迁移

```shell
# 迁移数据库
docker exec django python manage.py makemigrations
docker exec django python manage.py migrate
# 初始化
docker exec django python manage.py init
docker exec django python manage.py init_area
# 指定app 初始化
docker exec django python manage.py init --app_model_name system.LogRequestModel
```

进入容器

```shell
docker exec -it django sh
```

清空无效资源

```shell
docker system prune -a

```

查看容器

```shell
docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Command}}\t{{.Ports}}"

```

删除本地全部镜像

```shell
docker rmi -f $(docker images -q)
```

celery 使用说明

```shell
mac/linux:
celery -A application.celery worker -B --loglevel=info

win:
单线程
celery -A application.celery worker -l INFO -P solo

多线程
需要安装: pip install eventlet,需要启动两个程序（worker + beat 顺序不分先后）
celery -A application.celery worker -P eventlet --loglevel=info
celery -A application.celery beat --loglevel=info

监听celery 需要安装  pip install flower 
方式一：
celery -A application.celery flower --port=5555 --address=0.0.0.0
方式二：
celery --broker=redis://127.0.0.1:6379/4 flower
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

redis错误处理
安装Redis

```shell
# 下载Redis源码:  
wget http://download.redis.io/releases/redis-6.2.6.tar.gz
# 解压源码:  
tar xzf redis-6.2.6.tar.gz
# 进入目录:  
cd redis-6.2.6
# 编译Redis (包括redis-check-aof):  
make
# 安装Redis:
make install

```

redis-check-aof将被安装到/usr/local/bin目录下

```shell
cd /usr/local/bin
# 恢复备份文件
./redis-check-aof --fix /root/fengxin/docker_env/redis/data/appendonly.aof
# 重启redis
docker restart redis
```