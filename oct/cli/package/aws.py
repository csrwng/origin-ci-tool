# coding=utf-8
from __future__ import absolute_import, division, print_function

from click import command, option, pass_context, UsageError

from .common_options import package_options
from ..util.common_options import ansible_output_options

_SHORT_HELP = 'Package a running AWS EC2 virtual machine.'


@command(
    short_help=_SHORT_HELP,
    help=_SHORT_HELP + '''

This command allows for a virtual machine in EC2 to be packaged
as an update for its current stage or as an instance of the next
stage in the pipeline.

\b
Examples:
  Package a VM as a stage upgrade
  $ oct package ami --stage next
\b
  Package a VM for a specific stage
  $ oct package ami --stage fork
\b
  Mark a packaged AMI as ready for use
  $ oct package ami --mark-ready
\b
  Package a VM with custom tags
  $ oct package ami --tag FOO=BAR --tag OTHER=VAL
''',
)
@option(
    '--mark-ready',
    '-r',
    'mark_ready',
    is_flag=True,
    help='Mark an AMI created previously as ready.',
)
@option(
    '--tag',
    '-t',
    "tags",
    metavar='KEY=VALUE',
    multiple=True,
    help='Tag an AMI with the provided key-value pair.',
)
@ansible_output_options
@package_options
@pass_context
def ami(context, upgrade_stage, mark_ready, tags):
    """
    Package a running AWS EC2 virtual machine.

    :param context: Click context
    :param upgrade_stage: whether or not to upgrade the current stage
    :param mark_ready: whether or not to mark a previous AMI from this instance ready
    :param tags: tag an AMI with the provided key-value pair
    """
    configuration = context.obj

    validate_options(upgrade_stage, mark_ready, tags)

    ami_tags = {}
    for tag in tags:
        value = u""
        if "=" in tag:
            key, value = tag.split("=")
        else:
            key = tag
        ami_tags[key] = value

    if mark_ready:
        ami_tags["ready"] = "yes"
        configuration.run_playbook(
            playbook_relative_path='package/ami-mark-ready',
            playbook_variables={'origin_ci_aws_additional_tags': ami_tags},
        )
    else:
        configuration.run_playbook(
            playbook_relative_path='package/ami',
            playbook_variables={
                'origin_ci_aws_stage_strategy': upgrade_stage,
                'origin_ci_inventory_dir': configuration.ansible_client_configuration.host_list,
                'origin_ci_aws_additional_tags': ami_tags,
            },
        )


def validate_options(upgrade_stage, mark_ready, tags):
    if not mark_ready and upgrade_stage is None:
        raise UsageError('--stage must be specified')

    for tag in tags:
        if "=" in tag:
            key, value = tag.split("=")
        else:
            key = tag

        if len(key) == 0:
            raise UsageError('Invalid tag: {} - key must have non-zero length'.format(tag))

        if mark_ready and key == "ready":
            raise UsageError("Invalid tag: {} - will be overwritten by --mark-ready (ready=yes)".format(tag))
