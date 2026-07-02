"""Celery 实例 — Agent-Algorithm 负责注册任务"""
from celery import Celery
import os


def make_celery(app_name='traffic_prediction'):
    broker = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    return Celery(app_name, broker=broker)


celery = make_celery()
