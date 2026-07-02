import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """基础配置"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevConfig(Config):
    """开发环境"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///dev.db'
    )


class TestConfig(Config):
    """测试环境"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class ProdConfig(Config):
    """生产环境"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')


config_map = {
    'development': DevConfig,
    'testing': TestConfig,
    'production': ProdConfig,
}
