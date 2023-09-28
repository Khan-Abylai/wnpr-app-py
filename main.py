import argparse

from src.app import Application
from src.template_matching import TemplateMatching
from src.package_sender import PackageSender

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-ip',
                        default='10.66.149.22',
                        help='ip address of one camera')
    parser.add_argument("-server",
                        "--server",
                        default='10.66.149.2',
                        help="ip of server")

    args = parser.parse_args()

    camera_ip = args.ip

    template_matching = TemplateMatching()

    package_sender = PackageSender(args.server)

    app = Application(camera_ip, template_matching, package_sender)
    app.run()
