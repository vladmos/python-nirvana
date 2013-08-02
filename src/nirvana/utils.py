from subprocess import call


class CommandError(Exception):
    pass


def call_command(*args):
    error = call(args)
    if error:
        raise CommandError('Calling "%s", error code: %s' % (u' '.join(args), error))
