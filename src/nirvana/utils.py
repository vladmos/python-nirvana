from subprocess import call


class CommandError(Exception):
    pass


def call_command(command):

    error = call(command.split())
    if error:
        raise CommandError('Calling "%s", error code: %s' % (command, error))
