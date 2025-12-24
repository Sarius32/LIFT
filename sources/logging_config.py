CONFIG = lambda file_path: {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s | %(name)-20s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s',
        },
        'simple': {
            'format': '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s'
        },
        'minimal': {
            'format': '%(levelname)s: %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': "INFO",
            'formatter': 'simple',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': "DEBUG",
            'formatter': 'detailed',
            'filename': str(file_path),
            'mode': 'a',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 50,
            'encoding': 'utf-8'
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console', 'file']
    },
    'loggers': {
        # Silence httpx access logs (like HTTP Request: ...)
        'httpx': {
            'level': 'WARNING',  # show only warnings and above
            'propagate': False
        },
        'httpcore': {
            'level': 'WARNING',
            'propagate': False
        }
    }
}
