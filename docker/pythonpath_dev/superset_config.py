# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
# This file is included in the final Docker image and SHOULD be overridden when
# deploying the image to prod. Settings configured here are intended for use in local
# development environments. Also note that superset_config_docker.py is imported
# as a final step as a means to override "defaults" configured here
#
import logging
import os
import sys

from celery.schedules import crontab
from flask_caching.backends.filesystemcache import FileSystemCache

logger = logging.getLogger()

DATABASE_DIALECT = os.getenv("DATABASE_DIALECT")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT")
DATABASE_DB = os.getenv("DATABASE_DB")

EXAMPLES_USER = os.getenv("EXAMPLES_USER")
EXAMPLES_PASSWORD = os.getenv("EXAMPLES_PASSWORD")
EXAMPLES_HOST = os.getenv("EXAMPLES_HOST")
EXAMPLES_PORT = os.getenv("EXAMPLES_PORT")
EXAMPLES_DB = os.getenv("EXAMPLES_DB")

# The SQLAlchemy connection string.
SQLALCHEMY_DATABASE_URI = (
    f"{DATABASE_DIALECT}://"
    f"{DATABASE_USER}:{DATABASE_PASSWORD}@"
    f"{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_DB}"
)

# Use environment variable if set, otherwise construct from components
# This MUST take precedence over any other configuration
SQLALCHEMY_EXAMPLES_URI = os.getenv(
    "SUPERSET__SQLALCHEMY_EXAMPLES_URI",
    (
        f"{DATABASE_DIALECT}://"
        f"{EXAMPLES_USER}:{EXAMPLES_PASSWORD}@"
        f"{EXAMPLES_HOST}:{EXAMPLES_PORT}/{EXAMPLES_DB}"
    ),
)

# modify by wht
# REDIS_HOST = os.getenv("REDIS_HOST", "redis")
# REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_HOST = "superset_cache"
REDIS_PORT = "6379"
REDIS_CELERY_DB = os.getenv("REDIS_CELERY_DB", "0")
# REDIS_RESULTS_DB = os.getenv("REDIS_RESULTS_DB", "1")
REDIS_RESULTS_DB = os.getenv("REDIS_RESULTS_DB", "0")

RESULTS_BACKEND = FileSystemCache("/app/superset_home/sqllab")

CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 86400,
    "CACHE_KEY_PREFIX": "superset_",
    "CACHE_REDIS_HOST": REDIS_HOST,
    "CACHE_REDIS_PORT": REDIS_PORT,
    "CACHE_REDIS_DB": REDIS_RESULTS_DB,
}
DATA_CACHE_CONFIG = CACHE_CONFIG
THUMBNAIL_CACHE_CONFIG = CACHE_CONFIG

# modify by wht this to add user-defined
FEATURE_FLAGS = {
    "ALERT_REPORTS": True,
    'DASHBOARD_RBAC': True,
    'DASHBOARD_RBAC_STRICT': True,
    'ENABLE_JAVASCRIPT_CONTROLS': True,
    'ENABLE_TEMPLATE_PROCESSING': True,  # 启用模板处理
    'DYNAMIC_PLUGINS': True,  # 启用动态插件
    'TAGGING_SYSTEM': True,  # 启用标签系统
    'ENABLE_ADVANCED_DATA_TYPES': True,  # 启用高级数据类型
    'ENABLE_JSON_EDITOR': True,  # 启用JSON编辑器
    'SHOW_ADVANCED_CONTROLS': True,  # 显示高级控制面板选项
    'CORS_OPTIONS': {},  # 设置CORS选项
    'ENABLE_CORS': True
}

class CeleryConfig:
    broker_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_CELERY_DB}"
    imports = (
        "superset.sql_lab",
        "superset.tasks.scheduler",
        "superset.tasks.thumbnails",
        "superset.tasks.cache",
    )
    result_backend = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_RESULTS_DB}"
    # modify by wht
    # worker_prefetch_multiplier = 1
    # task_acks_late = False
    worker_prefetch_multiplier = 10
    task_acks_late = True
    task_annotations = {
        "sql_lab.get_sql_results": {
            "rate_limit": "100/s",
        },
    }
    beat_schedule = {
        "reports.scheduler": {
            "task": "reports.scheduler",
            "schedule": crontab(minute="*", hour="*"),
        },
        "reports.prune_log": {
            "task": "reports.prune_log",
            # modify by wht
            #"schedule": crontab(minute=10, hour=0),
            "schedule": crontab(minute=0, hour=0),
        },
    }


CELERY_CONFIG = CeleryConfig

#modify by wht
SCREENSHOT_LOCATE_WAIT = 100
SCREENSHOT_LOAD_WAIT = 600

# modify by wht this to add user-defined
ALERT_REPORTS_NOTIFICATION_DRY_RUN = False
WEBDRIVER_BASEURL = "http://superset:8088/"  # When using docker compose baseurl should be http://superset_app:8088/  # noqa: E501
# The base URL for the email report hyperlinks.
# modify by wht
# WEBDRIVER_BASEURL_USER_FRIENDLY = WEBDRIVER_BASEURL
WEBDRIVER_BASEURL_USER_FRIENDLY = "http://172.31.37.206:8088"

SQLLAB_CTAS_NO_LIMIT = True

# 修改 CSP 配置以允许外站图片
TALISMAN_CONFIG = {
    "content_security_policy": {
        "base-uri": ["'self'"],
        "default-src": ["'self'"],
        "img-src": [
            "'self'",
            "blob:",
            "data:",
            "https:",  # 允许所有 HTTPS 图片源
            # 如果需要 HTTP 图片，添加下面这行（不推荐）
            # "http:",
        ],
        "worker-src": ["'self'", "blob:"],
        "connect-src": [
            "'self'",
            "https://api.mapbox.com",
            "https://events.mapbox.com",
        ],
        "object-src": "'none'",
        "style-src": ["'self'", "'unsafe-inline'"],
        "script-src": ["'self'", "'strict-dynamic'"],
    },
    "content_security_policy_nonce_in": ["script-src"],
    "force_https": False,
    "session_cookie_secure": False,
}

log_level_text = os.getenv("SUPERSET_LOG_LEVEL", "INFO")
LOG_LEVEL = getattr(logging, log_level_text.upper(), logging.INFO)

if os.getenv("CYPRESS_CONFIG") == "true":
    # When running the service as a cypress backend, we need to import the config
    # located @ tests/integration_tests/superset_test_config.py
    base_dir = os.path.dirname(__file__)
    module_folder = os.path.abspath(
        os.path.join(base_dir, "../../tests/integration_tests/")
    )
    sys.path.insert(0, module_folder)
    from superset_test_config import *  # noqa

    sys.path.pop(0)

#
# Optionally import superset_config_docker.py (which will have been included on
# the PYTHONPATH) in order to allow for local settings to be overridden
#
try:
    import superset_config_docker
    from superset_config_docker import *  # noqa: F403

    logger.info(
        "Loaded your Docker configuration at [%s]", superset_config_docker.__file__
    )
except ImportError:
    logger.info("Using default Docker config...")

# modify by wht
# WebDriver configuration
# If you use Firefox, you can stick with default values
# If you use Chrome, then add the following WEBDRIVER_TYPE and WEBDRIVER_OPTION_ARGS
WEBDRIVER_TYPE = "chrome"
WEBDRIVER_OPTION_ARGS = [
    "--force-device-scale-factor=2.0",
    "--high-dpi-support=2.0",
    "--headless",
    "--disable-gpu",
    "--disable-dev-shm-usage",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-extensions",
]

from superset.tasks.types import FixedExecutor
ALERT_REPORTS_EXECUTORS = [FixedExecutor("admin")]

# Set a minimum interval threshold between executions (for each Alert/Report)
# Value should be an integer
# 最小执行间隔配置
from datetime import timedelta
ALERT_MINIMUM_INTERVAL = int(timedelta(minutes=10).total_seconds())
REPORT_MINIMUM_INTERVAL = int(timedelta(minutes=5).total_seconds())

#添加汉化支持
#https://zhuanlan.zhihu.com/p/6623611242
BABEL_DEFAULT_LOCALE='zh'  # 默认语言为中文
BABEL_DEFAULT_FOLDER = 'superset/translations'  # 多语言路径
#可选语言
LANGUAGES = {
    'zh': {'flag': 'cn', 'name': '简体中文'},
    'en': {'flag': 'us', 'name': 'English'}
}

# 允许图片大小调整 - 扩展 HTML 清理规则
HTML_SANITIZATION_SCHEMA_EXTENSIONS = {
    "attributes": {
        "img": ["style", "width", "height", "class"],  # 允许样式和尺寸属性
        "div": ["style", "class"],  # 也允许 div 的样式
        "span": ["style", "class"],  # 允许 span 的样式
    }
}

# 1. 降低查询行数限制（减轻 Doris 负担）
ROW_LIMIT = 10000
SAMPLES_ROW_LIMIT = 1000
FILTER_SELECT_ROW_LIMIT = 5000
NATIVE_FILTER_DEFAULT_ROW_LIMIT = 500

# 2. 增加超时时间
SUPERSET_WEBSERVER_TIMEOUT = 120
SQLLAB_TIMEOUT = 120
SQLLAB_ASYNC_TIME_LIMIT_SEC = 3600  # 1小时

# 3. 数据库连接池优化（已有，确认配置）
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 10,
    "pool_recycle": 3600,
    "pool_pre_ping": True,
    "max_overflow": 20,
    "pool_timeout": 30,
    "isolation_level": "READ COMMITTED",
}

# 4. 优化缓存配置
CACHE_DEFAULT_TIMEOUT = 86400  # 1天

