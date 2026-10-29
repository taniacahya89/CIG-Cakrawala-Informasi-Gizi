"""CIG Application Runner."""

import os
from app import create_app

app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host=os.environ.get('HOST', '127.0.0.1'), port=port,
            debug=(os.environ.get('FLASK_DEBUG') == '1' and os.environ.get('FLASK_ENV') != 'production'))
