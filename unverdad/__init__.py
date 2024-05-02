import logging
import unverdad.commands as cmds
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def main():
    cmds.parse_args()
