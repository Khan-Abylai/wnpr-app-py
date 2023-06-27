import argparse

from src.app import Application
from src.template_matching import TemplateMatching

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-ip',
                        default='0.0.0.0',
                        help='ip address of one camera')
    parser.add_argument("-server",
                        "--server",
                        default='127.0.0.1',
                        help="ip of server")

    args = parser.parse_args()

    camera_ip = args.ip

    template_matching = TemplateMatching()

    app = Application(camera_ip, template_matching, args.server)
    app.run()
