#!/usr/bin/env python
"""Bootstrap virutalenv installation

If you want to use virutalenv in your bootstap script, just include this
file in the same directory with it, and add this to the top::

    from ve_setup import use_virtualenv
    use_virtualenv()

If you want to require a specific version of virtualenv, set a download
mirror, or use an alternate installation directory, you can do so by supplying
the appropriate options to ``use_virtualenv()``.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import urllib


# Defaults
VIRTUALENV_VERSION = '1.5.1'
VIRTUALENV_ARGS = ['python']

#
# Working around error with PYTHONHOME
#
if 'PYTHONHOME' in os.environ:
    del os.environ['PYTHONHOME']
    print "WARNING: ignoring the value of the PYTHONHOME environment " \
          " variable! This value can corrupt the virtual python installation."

def use_virtualenv(argv, version=VIRTUALENV_VERSION, activate=True):
    """Install and use virtualenv environment."""

    virtualenv = VirtualEnv(argv, version=version)
    if activate:
        virtualenv.activate()
    return virtualenv

def log(message):
    """Log message"""

    sys.stderr.write(": %s\n" % message)


class VirtualEnv(object):
    """Virtual environment"""

    def __init__(self, argv, version=None):
        self.python_name = os.path.basename(sys.executable)
        self.version = version or VIRTUALENV_VERSION
        self.path = os.path.abspath(argv[-1])
        self.argv = argv
        if not self.is_installed:
            self.install()

    @property
    def scripts_dir(self):
        """Return path where scripts directory is located."""

        return os.path.join(self.path, 'Scripts' if sys.platform == 'win32'
                else 'bin')

    @property
    def is_installed(self):
        """Check this environment is installed."""

        return os.path.isfile(os.path.join(self.scripts_dir, self.python_name))
    
    @property
    def is_activated(self):
        """Check this environment is activated."""

        return 'VIRTUAL_ENV' in os.environ and \
                os.environ['VIRTUAL_ENV'] == self.path

    def install(self):
        """Install this environment."""

        tmpdir = tempfile.mkdtemp()
        virtualenv_requirement = 'virtualenv==%s' % self.version
        try:
            log("using virtualenv version %s" % self.version)
            installer = EZSetupInstaller(tmpdir)
            installer.install(virtualenv_requirement)
            virtualenv_py = os.path.join(tmpdir, 'virtualenv', 'virtualenv.py')
            virtualenv_cmd = [sys.executable, virtualenv_py] + self.argv
            log("execute %s" % " ".join(virtualenv_cmd))
            subprocess.call(virtualenv_cmd)
        finally:
            shutil.rmtree(tmpdir)

    def activate(self):
        """Activate this environment."""

        if self.is_activated:
            return # this environment is activated
        activate_this = os.path.join(self.scripts_dir, 'activate_this.py')
        execfile(activate_this, dict(__file__=activate_this))
        os.environ['VIRTUAL_ENV'] = self.path
        if not self.scripts_dir in os.getenv('PATH', ''):
            os.environ['PATH'] = os.pathsep.join(
                    [self.scripts_dir, os.getenv('PATH', '')])


class EZSetupInstaller(object):
    """Installer"""

    EZ_SETUP_PY = 'ez_setup.py'
    EZ_SETUP_URL = 'http://peak.telecommunity.com/dist/ez_setup.py'

    def __init__(self, install_dir, ez_setup_py=None):
        self.install_dir = install_dir
        self.ez_setup_py = ez_setup_py or (
                os.path.join(os.getcwd(), self.EZ_SETUP_PY) if os.path.isfile(
                    os.path.join(os.getcwd(), self.EZ_SETUP_PY)) else
                os.path.join(self.install_dir, self.EZ_SETUP_PY))
        self._fetch_ez_setup_py()

    def install(self, requirement):
        """Install given requirement."""

        env = os.environ.copy()
        env['PYTHONPATH'] = self.install_dir
        ez_setup_cmd = [sys.executable, self.ez_setup_py,
                '-q', '--editable', '--build-directory',  self.install_dir,
                requirement]
        log("download %s with %s" % (requirement, " ".join(ez_setup_cmd)))
        subprocess.call(ez_setup_cmd, env=env)

    def _fetch_ez_setup_py(self):
        """Fetch ez_setup.py."""

        if not os.path.isfile(self.ez_setup_py):
            ez_setup_url = self.EZ_SETUP_URL
            log("download %s to %s" % (ez_setup_url, self.ez_setup_py))
            urllib.urlretrieve(ez_setup_url, self.ez_setup_py)


if __name__ == '__main__':
    import traceback
    from optparse import OptionParser

    def main():
        """Main function."""

        usage = "usage: %prog [options] [[virtualenv options] DEST_DIR]"
        parser = OptionParser(usage=usage)
        parser.disable_interspersed_args()
        parser.add_option("--version", default=VIRTUALENV_VERSION,
                dest="version",
                help="virtualenv version. "
                "Default is '%s'." % VIRTUALENV_VERSION)
        (options, args) = parser.parse_args()
        version = options.version
        use_virtualenv(args or VIRTUALENV_ARGS, version)

    try:
        main()
        sys.exit(0)
    except Exception, e: # Catch all exceptions. pylint: disable=W0703
        sys.stderr.write(traceback.format_exc() if __debug__ else str(e))
        sys.exit(1)
