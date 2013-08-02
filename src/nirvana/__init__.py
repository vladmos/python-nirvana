import sys

from commands import commands


def get_commands():
    return [c[8:] for c in dir(commands) if c.startswith('command_')]


def get_command(command_name):
    return getattr(commands, 'command_' + command_name, None)


class Client(object):
    def __init__(self, argv=None):
        self.argv = argv or sys.argv[:]
        self.prog_name = self.argv[0]

    def main_help_text(self):
        """
        Returns the script's main help text, as a string.
        """
        usage = [
            '',
            "Type '%s help <subcommand>' for help on a specific subcommand."
            % self.prog_name,
            '',
            'Available subcommands:'
        ]
        commands = get_commands()
        commands.sort()
        for cmd in commands:
            usage.append('  %s' % cmd)
        return '\n'.join(usage)

    def execute(self):
        if len(self.argv) > 1:
            command_name = self.argv[1].lower()
            if command_name != 'help':
                command = get_command(command_name)
                if command:
                    command(self.argv[2:])
                    return
            else:
                if len(self.argv) > 2:
                    command_name = self.argv[2].lower()
                    command = get_command(command_name)
                    if command:
                        print(command.__doc__)
                        return

        print(self.main_help_text())


def main():
    Client().execute()


if __name__ == '__main__':
    main()
