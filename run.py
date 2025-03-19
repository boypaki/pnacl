import os
from app import create_app

# Determinar ambiente a partir da variável de ambiente
env = os.environ.get('FLASK_ENV', 'development')
app = create_app(env)

if __name__ == '__main__':
    app.run()
