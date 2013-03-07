from __future__ import print_function, unicode_literals

import time

from watchdog.observers import Observer
from watchdog.tricks import ShellCommandTrick


class SassCompilerTrick(ShellCommandTrick):

    def __init__(self, sass_dir='scss'):
        self.sass_dir = sass_dir

        command = 'sh tools/take_screengrab.sh'

        super(SassCompilerTrick, self).__init__(command,
                                                patterns=['*.scss', '*.sass'],
                                                ignore_directories=True,
                                                wait_for_process=True)

def main():

    trick = SassCompilerTrick()
    observer = Observer(timeout=0.5)
    observer.schedule(trick, trick.sass_dir, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == '__main__':
    main()
