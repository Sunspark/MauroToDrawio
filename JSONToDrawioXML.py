import argparse
import textwrap
import logging
import datetime
import json

import os
import re
import sys

from pathlib import Path
from jinja2 import Template
from operator import itemgetter

from MauroAPIInterface import MauroAPIInterface

#####################################################################
## Argument Parsing
#####################################################################

help_text = "Turns a JSON file to a Draw.io entity diagram"
epilog_text = '''Outputs an XML object to a filepath.
'''

ap = argparse.ArgumentParser(
  description=help_text,
  epilog=textwrap.dedent(epilog_text)
)
# Log-related arguments
ap.add_argument(
  '-l',
  '--log-level',
  action='store',
  nargs=1, # '?' is optional 1
  default='INFO',
  choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
  help='Sets File logging to specified level (default INFO). Overridden by --verbose.'
)
ap.add_argument(
  '-v',
  '--verbose',
  action='store_true',
  help='Sets File logging to DEBUG (default info), and StdOut logging to INFO (default none). Overrides --log-level.'
)
ap.add_argument(
  '-p',
  '--log-path',
  action='store',
  default='logs/',
  help="Sets destination path for file logs. Default 'logs/'."
)

# Input related arguments
ap.add_argument(
  '-i',
  '--input-file',
  action='store',
  required=True,
  help="The filename of the JSON to be converted."
)
# Output related arguments
ap.add_argument(
  '-o',
  '--output-file',
  action='store',
  default='new_model.xml',
  help="Sets filename of output file."
)




args = ap.parse_args()

#####################################################################
## Log Handling
#####################################################################

# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) #Sets the level that is passed to the handlers. The handlers then determine what is passed onward.

# Create handlers
now_string = datetime.datetime.now().strftime("%Y%m%d-%H%M%S%f")
if not args.log_path.endswith('/'):
  args.log_path = args.log_path + '/'
f_handler = logging.FileHandler(args.log_path + 'JSONToDrawioXML_' + now_string + '.log', encoding='utf-8')
strloglevel = args.log_level
intloglevel = getattr(logging, strloglevel.upper())
file_logging_level = intloglevel
if args.verbose:
  file_logging_level = logging.DEBUG
f_handler.setLevel(file_logging_level)

# Create formatters and add it to handlers
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
f_handler.setFormatter(logging.Formatter(log_format))

# Add handlers to the logger. Nothing logs prior to now.
logger.addHandler(f_handler)
if args.verbose:
  c_handler = logging.StreamHandler()
  c_handler.setLevel(logging.INFO)
  c_handler.setFormatter(logging.Formatter(log_format))
  logger.addHandler(c_handler)

#####################################################################
## Handle exiting
#####################################################################

def crit_and_die(message):
  logger.critical(message)
  logger.critical('Execution ends')
  sys.exit(message)

def err_and_die(err, message):
  logger.exception(err)
  logger.critical(message)
  logger.critical('Execution ends')
  sys.exit(err)

#####################################################################
## Actual program
#####################################################################

logger.info('Execution begins')
print("fish")

srcpath = ""
template_filename = "drawio_entities_diagram.tem"
data_filename = args.input_file

template = Path(os.path.join(srcpath, template_filename)).read_text()

with open(os.path.join(srcpath, data_filename)) as jsonfile:
  data = json.load(jsonfile)

logger.debug(str(data))

j2_template = Template(template)

rendered_template_string = j2_template.render(data)

output_filename = args.output_file
with open(output_filename, "w") as text_file:
  text_file.write(rendered_template_string)

logger.info("Execution ends")