#!/usr/bin/env python
""" main application file """
import os
from portal import APP

PORT = int(os.environ.get('PORT', 5000))
APP.secret_key = 'A0Zr98j/3asakdjal(&*(ajsdnasdasdhajhdasdr2342'
APP.run(host='0.0.0.0', port=PORT, debug=True)
