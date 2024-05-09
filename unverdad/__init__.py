import logging
from unverdad import config 
import unverdad.commands as cmds
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

__version__ = config.APP_VERSION

def main():
    cmds.parse_args()
