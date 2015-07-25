#!/usr/bin/env python
import os
from portal import app

port = int(os.environ.get('PORT', 5000))
app.secret_key = 'A0Zr98j/3asakdjal(&*(ajsdnasdasdhajhdasdr2342'
app.run(host='0.0.0.0', port=port, debug=True)