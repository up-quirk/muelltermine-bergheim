import argparse
import json
import logging
from pathlib import Path

from muelltermine.service import Service
from muelltermine.web import run


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', default='/data')
    parser.add_argument('--editor-port', type=int, default=8099)
    parser.add_argument('--feed-port', type=int, default=8098)
    parser.add_argument('--local', action='store_true', help='Editor ohne Ingress nur für lokale Entwicklung')
    parser.add_argument('--no-refresh', action='store_true')
    args = parser.parse_args()
    options_path = Path(args.data_dir) / 'options.json'
    options = json.loads(options_path.read_text()) if options_path.exists() else {}
    logging.basicConfig(level=getattr(logging, options.get('log_level', 'info').upper(), logging.INFO),
                        format='%(asctime)s %(levelname)s %(message)s')
    run(Service(Path(args.data_dir)), args.editor_port, args.feed_port, not args.local, not args.no_refresh)
