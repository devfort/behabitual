from __future__ import print_function, unicode_literals

import time

from django.core.management.base import BaseCommand, CommandError

from watchdog.observers.polling import PollingObserver as Observer
from watchdog.tricks import ShellCommandTrick


class SassCompilerTrick(ShellCommandTrick):

    def __init__(self, sass_dir='assets/scss', output_file='assets/main.css'):
        self.sass_dir = sass_dir
        self.output_file = output_file

        command = 'sass {0}/_manifest.scss:{1}'.format(self.sass_dir, self.output_file)

        super(SassCompilerTrick, self).__init__(command,
                                                patterns=['*.scss', '*.sass'],
                                                ignore_directories=True,
                                                wait_for_process=True)

    def on_any_event(self, event):
        print("Sass recompiling... ", end="")
        super(SassCompilerTrick, self).on_any_event(event)
        print("done")


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        trick = SassCompilerTrick(output_file='assets/hobbit.css')
        observer = Observer(timeout=0.5)
        observer.schedule(trick, trick.sass_dir, recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
