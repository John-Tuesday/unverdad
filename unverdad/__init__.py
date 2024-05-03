import logging
import unverdad.commands as cmds
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

__version__ = "0.0.1"

def main():
    cmds.parse_args()
