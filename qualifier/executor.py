import shlex
import shutil
import subprocess
import time
import os
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from tempfile import mkstemp

import logging

logger = logging.getLogger(__name__)

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)


class Executor(object):
    def __init__(self,
                 dev_qualifier,
                 rc_qualifier,
                 use_git,
                 branch_name,
                 tag_name,
                 rc_branch,
                 qualifier_expression,
                 qualifier_template,
                 qualifier_file_name):
        self.dev_qualifier = dev_qualifier
        self.rc_qualifier = rc_qualifier
        self.use_git = use_git
        self.branch_name = branch_name
        self.tag_name = tag_name
        self.rc_branch = rc_branch
        self.qualifier_expression = qualifier_expression
        self.qualifier_template = qualifier_template
        self.qualifier_file_name = qualifier_file_name

        if not use_git and not branch_name:
            raise ValueError("If use git is False then either branch name must be provided!")

        if use_git and (branch_name or tag_name):
            raise ValueError("if use git is True then both branch name and tag name must not be provided!")

    def _run_command(self, command):
        return subprocess.check_output(shlex.split(command))

    def _get_branch_name(self):
        if not self.use_git:
            return self.branch_name

        git_command = "git rev-parse --abbrev-ref HEAD"
        output = self._run_command(command=git_command)
        return output.decode("UTF-8").strip() if output else output

    def _get_tag_name(self):
        if not self.use_git:
            return self.tag_name

        git_command = "git describe --tags --exact-match"

        try:
            output = self._run_command(command=git_command)
            return output.decode("UTF-8").strip() if output else output
        except subprocess.CalledProcessError:
            logger.debug("Seems like current SHA is not tagged so returning none")

        return None

    def _generate_qualifier(self):
        current_branch = self._get_branch_name()
        tag_name = self._get_tag_name()

        if tag_name and (current_branch == self.rc_branch or current_branch == tag_name):
            return None

        logger.debug("Current branch name is {}".format(current_branch))

        qualifier = self.rc_qualifier if current_branch == self.rc_branch else self.dev_qualifier
        epoch_time = int(time.time())

        return "{}{}".format(qualifier, epoch_time)

    def _update_qualifier(self, qualifier):
        file_handle, file_path = mkstemp()
        new_qualifier_expression = self.qualifier_template.format(qualifier)

        with os.fdopen(file_handle, "w") as temp_file:
            with open(self.qualifier_file_name) as current_file:
                for line in current_file:
                    temp_file.write(line.replace(self.qualifier_expression, new_qualifier_expression))

        shutil.move(file_path, self.qualifier_file_name)

    def run(self):
        qualifier = self._generate_qualifier()
        logger.info("The qualifier is '{}'".format(qualifier))

        if not qualifier:
            return

        self._update_qualifier(qualifier=qualifier)


def main():
    parser = ArgumentParser(description="Updates setup.py file based on the rules to defined in the project. "
                                        "Please take a look at README.md",
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("--dev-qualifier",
                        default=".dev",
                        help="String to be used for tagging a dev build")
    parser.add_argument("--rc-qualifier",
                        default="rc",
                        help="String to be used for tagging a rc build")
    parser.add_argument("--no-use-git",
                        default=True,
                        dest="use_git",
                        action="store_false",
                        help="Whether to use git commands to fetch branch and tags information")
    parser.add_argument("--branch-name",
                        default=None,
                        help="If use-git is set to false then provide the branch name")
    parser.add_argument("--tag-name",
                        default=None,
                        help="If use-git is set to false then provide the tag name")
    parser.add_argument("--rc-branch",
                        default="master",
                        help="The branch which is used for classifying rc")
    parser.add_argument("--qualifier-expression",
                        default="__QUALIFIER__ = \"\"",
                        help="The expression in the qualifier file that should be replaced with derived qualifier")
    parser.add_argument("--qualifier-template",
                        default="__QUALIFIER__ = \"{}\"",
                        help="String format template used to update the qualifier")
    parser.add_argument("--qualifier-file-name",
                        default="setup.py",
                        help="Name of the file where qualifier expression is defined")

    Executor(**vars(parser.parse_args())).run()
