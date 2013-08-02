python-nirvana
==============

A tool for easier deployment of python/django projects on debian-like systems.

Initializing
------------

Create a file `nirvana.ini` in your project's root with the following sections:

    [project]
    name = project_name (will become the debian source name)
    description = Long description
    maintainer = Your Name
    maintainer_email = your@email
    
    [python]
    version = >=2.5
    source_dir = src
    
    [entry_points]  # optional
    uber_command = package:function
    
    [package]
    name = package_name (in case of one-package project should be equal to the source name)
    description = Long description
    debian-requirements = debian-requirements.txt  # Optional, name of a file with debian packages dependences, one per line
    
    [django]  # optional
    # structure TBA
    
    [nginx]  # optional, requires django
    server_name = example.com
    # full structure TBA
    
    [cron]  # optional
    # structure TBA
    
In case if you need to create several packages from one source, create `nirvana.ini` with sections `project`,
`python` and `entry_points`, and several configs `<something>.ini` each containing complement sections for each
package you need.

Usage
-----

You need to generate a gpg key in order to sign deb packages: `gpg --gen-key`.

  * Initial installation of nirvana: `python src/nirvana/__init__.py` (here and later it's assumed the current dir is the project's root).
  * Install a nirvana-driven package: `nirvana install`
  * Just debianize: `nirvana debianize`
  * Just build deb-package(s): `nirvana build`
  * Update changelog: `nirvana changelog`

License
-------

© Vladimir Moskva. Distribution is free.
