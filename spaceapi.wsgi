import logging, sys
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, '/opt/SpaceAPI/')
from SpaceAPI import app as application
