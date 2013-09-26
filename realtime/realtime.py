#!/usr/bin/env python

import argparse
import logging
import sys
import threading
import time

import rt

class Parser(argparse.ArgumentParser):

    def error(self, message):
        self.print_help()
        sys.stderr.write('\n{}\n'.format(message))
        sys.exit(2)

def handle_line(translator, line, output, ctx_name):
    if '|||' in line:
        translator.command_line(line, ctx_name)
    else:
        hyp = translator.decode(line, ctx_name)
        output.write('{}\n'.format(hyp))
        output.flush()

def test1(translator, input, output, ctx_name):
    inp = open(input)
    out = open(output, 'w')
    for line in inp:
        handle_line(translator, line.strip(), out, ctx_name)
    out.close()

def debug(translator, input):
    # Test 1: identical output
    threads = []
    for i in range(4):
        t = threading.Thread(target=test1, args=(translator, input, '{}.out.{}'.format(input, i), str(i)))
        threads.append(t)
        t.start()
        time.sleep(30)
    for t in threads:
        t.join()
    # Test 2: flood (same number of lines)
    threads = []
    out = open('{}.out.flood'.format(input), 'w')
    for line in open(input):
        t = threading.Thread(target=handle_line, args=(translator, line.strip(), out, None))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

def main():

    parser = Parser(description='Real-time adaptive translation with cdec.  (See README.md)')
    parser.add_argument('-c', '--config', required=True, help='Config directory')
    parser.add_argument('-s', '--state', help='Load state file (saved incremental data)')
    parser.add_argument('-n', '--normalize', help='Normalize text (tokenize, translate, detokenize)', action='store_true')
    parser.add_argument('-T', '--temp', help='Temp directory (default /tmp)', default='/tmp')
    parser.add_argument('-a', '--cache', help='Grammar cache size (default 5)', default='5')
    parser.add_argument('-v', '--verbose', help='Info to stderr', action='store_true')
    parser.add_argument('-D', '--debug-test', help='Run debug tests on input file')
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    with rt.RealtimeTranslator(args.config, tmpdir=args.temp, cache_size=int(args.cache), norm=args.normalize) as translator:

        # Debugging
        if args.debug_test:
            debug(translator, args.debug_test)
            return

        # Read lines and commands
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if '|||' in line:
                translator.command_line(line)
            else:
                hyp = translator.decode(line)
                sys.stdout.write('{}\n'.format(hyp))
                sys.stdout.flush()
     
if __name__ == '__main__':
    main()
