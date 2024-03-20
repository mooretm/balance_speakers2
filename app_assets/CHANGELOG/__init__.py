""" Paths to CHANGELOG resources. """

###########
# Imports #
###########
# System imports
from pathlib import Path


#############
# Constants #
#############
CHANGELOG_DIRECTORY = Path(__file__).parent


##############
# Change Log #
##############
CHANGELOG_HTML = CHANGELOG_DIRECTORY / 'CHANGELOG.html'
CHANGELOG_MD = CHANGELOG_DIRECTORY / 'CHANGELOG.md'
