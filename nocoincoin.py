#!/usr/bin/env python3

# Written by Stephen Fromm <sfromm gmail com>
# Copyright (C) 2018 Stephen Fromm
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import nocoin
import logging

def setup_logging(args):
    ''' set up logging bits '''
    if args.verbose >= 2:
        loglevel = 'DEBUG'
    elif args.verbose >= 1:
        loglevel = 'INFO'
    else:
        loglevel = 'WARN'

    logger = logging.getLogger()
    logger.level = getattr(logging, loglevel.upper(), None)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='Port to listen to')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='Be verbose')
    args = parser.parse_args()
    setup_logging(args)

    nocoin.app.run(host='0.0.0.0', port=args.port)
