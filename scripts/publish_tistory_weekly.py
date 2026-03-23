#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from wedding_expo_scraper.tistory_web_publisher import main


if __name__ == "__main__":
    raise SystemExit(main())
