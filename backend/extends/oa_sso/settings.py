from application import settings

settings.PLUGINS_URL_PATTERNS += [{'path': 'api/oa-sso/', 'include': 'extends.oa_sso.urls'}]
settings.MIDDLEWARE += ['extends.oa_sso.middleware.OaSsoMiddleware']
settings.CELERY_IMPORTS = tuple(getattr(settings, 'CELERY_IMPORTS', ())) + ('extends.oa_sso.tasks',)
settings.CELERY_BEAT_SCHEDULE = {
    **getattr(settings, 'CELERY_BEAT_SCHEDULE', {}),
    'oa-sso-revoke-pending': {'task': 'extends.oa_sso.tasks.revoke_pending', 'schedule': 30.0},
}
