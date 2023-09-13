import logging
import src.constants as constants

logging.basicConfig(filename=constants.logging_filename,
                    level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s: %(message)s')

logger = logging.getLogger(__name__)