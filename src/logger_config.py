import logging

logging.basicConfig(filename='/home/parqour/wnpr_logs/wnprapp.log',
                    level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s: %(message)s')

logger = logging.getLogger(__name__)