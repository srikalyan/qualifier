import subprocess

from hamcrest import assert_that, is_, equal_to, calling, raises
from mock import patch

from qualifier.executor import Executor


class TestExecutor(object):
    def setup(self):
        self.dev_qualifier = "dev_qualifier"
        self.rc_qualifier = "rc_qualifier"
        self.use_git = True
        self.branch_name = "branch_name"
        self.tag_name = "tag_name"
        self.rc_branch = "rc_branch"
        self.qualifier_expression = "qualifier_expression"
        self.qualifier_template = "qualifier_template {}"
        self.qualifier_file_name = "qualifier_file_name"
        self.executor = Executor(
            dev_qualifier=self.dev_qualifier,
            rc_qualifier=self.rc_qualifier,
            use_git=self.use_git,
            branch_name=None,
            tag_name=None,
            rc_branch=self.rc_branch,
            qualifier_expression=self.qualifier_expression,
            qualifier_template=self.qualifier_template,
            qualifier_file_name=self.qualifier_file_name,
        )

    def test_constructor_with_no_use_git_and_no_branch(self):
        assert_that(calling(Executor).with_args(
            dev_qualifier=self.dev_qualifier,
            rc_qualifier=self.rc_qualifier,
            use_git=False,
            branch_name=None,
            tag_name=None,
            rc_branch=self.rc_branch,
            qualifier_expression=self.qualifier_expression,
            qualifier_template=self.qualifier_template,
            qualifier_file_name=self.qualifier_file_name,
        ), raises(ValueError))

    def test_constructor_with_use_git_and_branch(self):
        assert_that(calling(Executor).with_args(
            dev_qualifier=self.dev_qualifier,
            rc_qualifier=self.rc_qualifier,
            use_git=True,
            branch_name=self.branch_name,
            tag_name=None,
            rc_branch=self.rc_branch,
            qualifier_expression=self.qualifier_expression,
            qualifier_template=self.qualifier_template,
            qualifier_file_name=self.qualifier_file_name,
        ), raises(ValueError))

    def test_constructor_with_use_git_and_tag(self):
        assert_that(calling(Executor).with_args(
            dev_qualifier=self.dev_qualifier,
            rc_qualifier=self.rc_qualifier,
            use_git=True,
            branch_name=None,
            tag_name=self.tag_name,
            rc_branch=self.rc_branch,
            qualifier_expression=self.qualifier_expression,
            qualifier_template=self.qualifier_template,
            qualifier_file_name=self.qualifier_file_name,
        ), raises(ValueError))

    @patch("subprocess.check_output")
    @patch("shlex.split")
    def test_run_command(self, mock_split, mock_check_output):
        command = "something"
        assert_that(self.executor._run_command(command=command), is_(equal_to(mock_check_output.return_value)))
        mock_check_output.assert_called_once_with(mock_split.return_value)
        mock_split.assert_called_once_with(command)

    def test_get_branch_name(self):
        with patch.object(self.executor, "_run_command") as mock_run_command:
            assert_that(self.executor._get_branch_name(),
                        is_(equal_to(mock_run_command.return_value.decode.return_value.strip.return_value)))
            mock_run_command.assert_called_once_with(command="git rev-parse --abbrev-ref HEAD")
            mock_run_command.return_value.decode.assert_called_once_with("UTF-8")
            mock_run_command.return_value.decode.return_value.strip.assert_called_once_with()

    def test_get_branch_name_without_git(self):
        self.executor.use_git = False
        self.executor.branch_name = self.branch_name

        assert_that(self.executor._get_branch_name(), is_(equal_to(self.branch_name)))

    def test_get_tag_name(self):
        with patch.object(self.executor, "_run_command") as mock_run_command:
            assert_that(self.executor._get_tag_name(),
                        is_(equal_to(mock_run_command.return_value.decode.return_value.strip.return_value)))
            mock_run_command.assert_called_once_with(command="git describe --tags --exact-match")
            mock_run_command.return_value.decode.assert_called_once_with("UTF-8")
            mock_run_command.return_value.decode.return_value.strip.assert_called_once_with()

    def test_get_tag_name_no_tag(self):
        with patch.object(self.executor, "_run_command") as mock_run_command:
            mock_run_command.side_effect = subprocess.CalledProcessError(20, "something bad happened")
            assert_that(self.executor._get_tag_name(),
                        is_(equal_to(None)))
            mock_run_command.assert_called_once_with(command="git describe --tags --exact-match")

    def test_get_tag_name_without_git(self):
        self.executor.use_git = False
        self.executor.tag_name = self.tag_name

        assert_that(self.executor._get_tag_name(), is_(equal_to(self.tag_name)))

    def test_generate_qualifier_no_qualifier(self):
        with patch.object(self.executor, "_get_branch_name") as mock_get_branch_name:
            with patch.object(self.executor, "_get_tag_name") as mock_get_tag_name:
                mock_get_branch_name.return_value = self.rc_branch
                mock_get_tag_name.return_value = self.tag_name
                assert_that(self.executor._generate_qualifier(), is_(equal_to(None)))

                mock_get_tag_name.assert_called_once_with()
                mock_get_branch_name.assert_called_once_with()

    @patch("time.time")
    def test_generate_qualifier_with_rc_qualifier(self, mock_time):
        mock_time_value = 20
        mock_time.return_value = mock_time_value

        with patch.object(self.executor, "_get_branch_name") as mock_get_branch_name:
            with patch.object(self.executor, "_get_tag_name") as mock_get_tag_name:
                mock_get_branch_name.return_value = self.rc_branch
                mock_get_tag_name.return_value = None
                assert_that(self.executor._generate_qualifier(),
                            is_(equal_to("{}{}".format(self.rc_qualifier, mock_time_value))))

                mock_get_tag_name.assert_called_once_with()
                mock_get_branch_name.assert_called_once_with()

        mock_time.assert_called_once_with()

    @patch("time.time")
    def test_generate_qualifier_with_dev_qualifier(self, mock_time):
        mock_time_value = 20
        mock_time.return_value = mock_time_value

        with patch.object(self.executor, "_get_branch_name") as mock_get_branch_name:
            with patch.object(self.executor, "_get_tag_name") as mock_get_tag_name:
                mock_get_branch_name.return_value = "non_{}".format(self.rc_branch)
                mock_get_tag_name.return_value = None
                assert_that(self.executor._generate_qualifier(),
                            is_(equal_to("{}{}".format(self.dev_qualifier, mock_time_value))))

                mock_get_tag_name.assert_called_once_with()
                mock_get_branch_name.assert_called_once_with()

        mock_time.assert_called_once_with()

    def test_run(self):
        with patch.object(self.executor, '_generate_qualifier') as mock_generate_qualifier:
            with patch.object(self.executor, '_update_qualifier') as mock_update_qualifier:
                self.executor.run()
                mock_generate_qualifier.assert_called_once_with()
                mock_update_qualifier.assert_called_once_with(qualifier=mock_generate_qualifier.return_value)

    def test_run_without_update(self):
        with patch.object(self.executor, '_generate_qualifier') as mock_generate_qualifier:
            with patch.object(self.executor, '_update_qualifier') as mock_update_qualifier:
                mock_generate_qualifier.return_value = None
                self.executor.run()
                mock_generate_qualifier.assert_called_once_with()
                mock_update_qualifier.assert_not_called()
