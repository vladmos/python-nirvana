import sys
import commands

def get_commands():
    return [c for c in dir(commands) if not c.startswith('_') and c.islower()]

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
                command = getattr(commands, command_name, None)
                if command:
                    command()
                    return

        print self.main_help_text()

def main():
    Client().execute()


if __name__ == '__main__':
    main()