import argparse
import textwrap
import logging
import datetime
import csv
import json
#import requests
import os
import re
import sys

from MauroAPIInterface import MauroAPIInterface

#####################################################################
## Argument Parsing
#####################################################################

help_text = "Pulls a given model in JSON format from Mauro Data Mapper. Requires a user to have set up an API key."
epilog_text = '''Outputs a JSON object to a filepath.
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
# API-related arguments
ap.add_argument(
  '-u',
  '--mauro-url',
  action='store',
  required=True,
  help="Sets URL of the Mauro API. e.g.'http://localhost:8082/api'"
)
ap.add_argument(
  '-k',
  '--mauro-api-key',
  action='store',
  required=True,
  help="Sets API key for interacting with the Mauro API. Note that the API won't return 'bad key' - it only returns 404."
)
# Input related arguments
ap.add_argument(
  '-i',
  '--model-id',
  action='store',
  required=True,
  help="The UUID of the Model that is being extracted."
)
# Output related arguments
ap.add_argument(
  '-o',
  '--output-file',
  action='store',
  default='output.json',
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
f_handler = logging.FileHandler(args.log_path + 'MauroModelToJSON_' + now_string + '.log', encoding='utf-8')
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

# Create interface object for throwing things at the API
api_base_url = args.mauro_url
logger.info("Connecting to Mauro API at: " + str(api_base_url))
try:
  mapi = MauroAPIInterface(logger, api_base_url)
except ValueError as err :
  err_and_die(err, "Could not create Mauro API interface")

api_key = args.mauro_api_key
logger.debug("Incoming API key not logged, as it's secret.")
try:
  mapi.api_key = api_key
except ValueError as err :
  err_and_die(err, "Given API key appears to be bad. It should look like a UUID.")  

# Start output
output_dict = {}

# Get initial classes in model
target_model_uuid = args.model_id
output_dict['model_id'] = target_model_uuid
output_dict['classes'] = []

logger.info("Attempting to retrieve Model ID: " + str(target_model_uuid))
classes_in_model_json = mapi.get_classes_in_model(target_model_uuid)
logger.debug(str(classes_in_model_json))

full_text_model = json.loads(classes_in_model_json['full_text'])
for found_class in full_text_model['items'] :
  logger.info("Found class ID: " + str(found_class['id']))
  logger.info("Found class Label: " + str(found_class['label']))

  class_dict = {
    'id' : found_class['id'],
    'label' : found_class['label'],
    'elements' : [],
    'links' : []
  }

  # Get elements in class
  logger.info("Attempting to retrieve Class ID: " + str(found_class['id']))
  elements_in_class_json = mapi.get_elements_in_class(target_model_uuid, found_class['id'])
  logger.debug(str(elements_in_class_json))

  full_text_class = json.loads(elements_in_class_json['full_text'])
  for found_element in full_text_class['items'] :
    logger.info("Found element ID: " + str(found_element['id']))
    logger.info("Found element Label: " + str(found_element['label']))

    element_dict = {
      'id' : found_element['id'],
      'label' : found_element['label'],
      'data_type' : found_element['dataType']['label'],
      'is_pk' : False
    }

    # Get Metadata per element
    logger.info("Attempting to retrieve metadata for element ID: " + str(found_element['id']))
    element_metadata_json = mapi.get_element_metadata(found_element['id'])
    logger.debug(str(element_metadata_json))

    full_text_element = json.loads(element_metadata_json['full_text'])
    for found_metadata in full_text_element['items'] :
      logger.info("Found metadata ID: " + str(found_metadata['id']))

      # Filter out only the PK
      if (
        found_metadata['namespace'] == "BusinessEntityDiagram.will-list.co.uk"
        and found_metadata['key'] == "BusinessEntityUniqueIdentifier"
        and found_metadata['value'] == "true"
      ) :
        element_dict['is_pk'] = True

    class_dict['elements'].append(element_dict)

  # Get class links
  logger.info("Attempting to retrieve links for Class ID: " + str(found_class['id']))
  links_in_class_json = mapi.get_links_in_class(found_class['id'])
  logger.debug(str(links_in_class_json))

  full_text_links = json.loads(links_in_class_json['full_text'])
  for found_link in full_text_links['items'] :
    logger.info("Found link ID: " + str(found_link['id']))

    # Filter to only outgoing links (this class is the source)
    if (
      found_link['sourceMultiFacetAwareItem']['id'] == found_class['id']
    ) :
      link_dict = {
        'id' : found_link['id'],
        'source_id' : found_class['id'],
        'target_id' : found_link['targetMultiFacetAwareItem']['id']
      }
      class_dict['links'].append(link_dict)

  output_dict['classes'].append(class_dict)

logger.debug(str(output_dict))

# Output to file
logger.info("Attempting to output to: " + str(args.output_file))
with open(args.output_file, 'w', encoding='utf-8') as output_file:
  json.dump(output_dict, output_file, ensure_ascii=False, indent=2)

logger.info("Execution ends")