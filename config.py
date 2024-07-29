import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()
def get_config():
    environment = os.getenv('APP_ENV', 'dev')
    print(environment)
    base_config = {
        'DEBUG': False,
        'PROPAGATE_EXCEPTIONS': True,
        'SERVER_NAME': 'bizbox.withfirst.com:3001',
        'SECRET_KEY': os.getenv('SECRET_KEY'),
        'JWT_SECRET_KEY': os.getenv('T_S_KEY'),
        'JWT_ACCESS_TOKEN_EXPIRES': timedelta(minutes=30),
        'JWT_REFRESH_TOKEN_EXPIRES': timedelta(days=3),
    }

    if environment == 'dev':
        base_config.update({
            'DEBUG': True,
            'SERVER_NAME': '192.168.0.18:3001',
            'DATABASE': os.getenv('DEV_DB_ROOT'),
        })
    elif environment == 'prod':
        base_config.update({
            'SERVER_NAME': 'bizbox.withfirst.com:3001',
            'DATABASE': os.getenv('DB_ROOT'),
        })

    return base_config

