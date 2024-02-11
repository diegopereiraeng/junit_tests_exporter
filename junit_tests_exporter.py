import os
import xml.etree.ElementTree as ET
import sys
import subprocess
import json
import traceback
import glob  # pattern matching
from prettytable import PrettyTable # python iage need to add pip install prettytable

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def colorize(text, color):
    return f"{color}{str(text)}{Colors.ENDC}"

def log_info(message):
    print(colorize("INFO: " + message, Colors.OKBLUE))

def log_success(message):
    print(colorize("SUCCESS: " + message,Colors.OKGREEN))

def log_warning(message):
    print(colorize("WARNING: " + message, Colors.WARNING))

def log_error(message):
    print(colorize("ERROR: " + message, Colors.FAIL))

def log_error_with_traceback(message, exc):
    tb_str = traceback.format_exception(etype=type(exc), value=exc, tb=exc.__traceback__)
    error_message = "".join(tb_str)
    print(colorize("ERROR: " + message + "\n" + error_message, Colors.FAIL))

num_tests = 0
num_failures = 0
failed_tests_details = []

def process_xml_file(file_path):
    global num_tests, num_failures
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        tests_in_file = int(root.get('tests', '0'))
        failures_in_file = int(root.get('failures', '0'))
        num_tests += tests_in_file
        num_failures += failures_in_file

        for testcase in root.findall('.//testcase'):
            failure = testcase.find('failure')
            if failure is not None:
                failed_tests_details.append({
                    'class': testcase.get('classname'),
                    'name': testcase.get('name'),
                    'message': failure.get('message'),
                    'stack_trace': failure.text
                })
        log_info(f"Processed file '{file_path}' successfully.")
        if tests_in_file > 0:
            log_success(f"Processed '{tests_in_file}' tests in file.")
            if failures_in_file > 0:
                log_warning(f"Processed '{failures_in_file}' failures in file.")
    except Exception as e:
        log_error_with_traceback(f"Error processing file '{file_path}'", e)

def process_directories_glob(pattern):
    log_info(f"Starting processing of directories for JUnit Tests Exporter with pattern: {pattern}")
    for file_path in glob.glob(pattern, recursive=True):
        process_xml_file(file_path)

def process_directories_old(include_dirs):
    log_info("Starting processing of directories for JUnit Tests Exporter.")
    for include_dir in include_dirs:
        if os.path.isdir(include_dir):
            for root, _, files in os.walk(include_dir):
                for file in files:
                    if file.endswith(".xml"):
                        file_path = os.path.join(root, file)
                        process_xml_file(file_path)
        else:
            log_warning(f"Directory '{include_dir}' does not exist or is not accessible.")

# Function to write environment variables to the .env file
def write_env_file(variables, file_path):
    try:
        with open(file_path, 'w') as f:
            for key, value in variables.items():
                f.write(f"{key}={value}\n")
    except IOError as e:
        print(f"Error writing to .env file: {e}")

def output_results():
    log_info("JUnit Tests Exporter - Summary of Test Results")
    
    if failed_tests_details:
        # Creating a table for failed tests details
        failed_tests_table = PrettyTable()
        failed_tests_table.field_names = ["Class", "Test", "Message", "Stack Trace"]
        failed_tests_table.align = "l"

        # Adjust the 'max_width' settings for the columns
        # failed_tests_table.max_width["Test"] = 50  # Set a narrower max width for the Test column
        # failed_tests_table.max_width["Stack Trace"] = 600  # Set a wider max width for the Stack Trace column
        failed_tests_table._min_width = {"Stack Trace" : 600}
        failed_tests_table._max_width = {"Stack Trace" : 600, "Test" : 50}
        

        for test in failed_tests_details:
            # failed_tests_table.add_row([test['class'], colorize(f"{test['name']}", Colors.WARNING), colorize(f"{test['message']}", Colors.WARNING) , colorize(f"{test['stack_trace']}", Colors.FAIL)])
            failed_tests_table.add_row([
                colorize(test['class'], Colors.BOLD),  # Make class names bold
                test['name'],  # Keep test names in default color for neutrality
                colorize(test['message'], Colors.WARNING),  # Warning messages in yellow
                colorize(test['stack_trace'], Colors.FAIL)  # Error details in red
            ])
        
        print(colorize("Failed Tests Details:", Colors.FAIL))
        print(failed_tests_table)
    # Gate Status Table
    gate_status_table = PrettyTable()
    gate_status_table.field_names = ["Gate Status", "Details"]
    if num_tests > 0:
        failure_rate = (num_failures / num_tests) * 100  # Calculate failure_rate immediately after checking num_tests
        num_failures_text = colorize(num_failures, Colors.FAIL if num_failures > 0 else Colors.OKGREEN)
        failure_rate_text = colorize(f"{failure_rate:.2f}%", Colors.OKGREEN if failure_rate == 0 else Colors.WARNING if failure_rate < 80 else Colors.FAIL)


        # Summary table
        summary_table = PrettyTable()
        summary_table.field_names = ["Total Tests Run", "Total Failures", "Failure Rate"]
        summary_table.add_row([num_tests, num_failures_text, failure_rate_text])
        print(summary_table)

        # Setting environment variables using os.environ
        os.environ['TOTAL_TESTS'] = str(num_tests)
        os.environ['TOTAL_FAILURES'] = str(num_failures)
        os.environ['FAILURE_RATE'] = str(failure_rate) 
        os.environ['FAILED_TESTS_JSON'] = json.dumps(failed_tests_details)

        # Prepare your environment variables for writing to the .env file
        env_variables = {
            "TOTAL_TESTS": os.environ['TOTAL_TESTS'],
            "TOTAL_FAILURES": os.environ['TOTAL_FAILURES'],
            "FAILURE_RATE": os.environ['FAILURE_RATE'],
            "FAILED_TESTS_JSON": os.environ['FAILED_TESTS_JSON'],
        }

        # Specify the path to your .env file
        file_path = os.getenv('DRONE_OUTPUT', 'default_env_file.env')

        # Call the function to write the environment variables to the .env file
        write_env_file(env_variables, file_path)
        
        # print(colorize(f"Total tests run: {num_tests}", Colors.OKGREEN))
        # print(colorize(f"Total failures: {num_failures}", Colors.WARNING))
        # print(colorize(f"Failure Rate: {failure_rate}%", Colors.WARNING if failure_rate > 0 else Colors.OKGREEN))

        # Use environment variable for threshold with a default value
        threshold = float(os.getenv('PLUGIN_THRESHOLD', '0'))  # Ensure it's a float for comparison
        
        if failure_rate > threshold:
            log_error(f"Failure rate is higher than {threshold}% ({failure_rate}%). Exiting with error.")
            gate_status_table.add_row([colorize("FAILED", Colors.FAIL), f"Failure rate ({failure_rate:.2f}%) exceeds threshold ({threshold}%)"])
            print(gate_status_table)
            sys.exit(1)
        gate_status_table.add_row([colorize("PASSED", Colors.OKGREEN), f"Failure rate ({failure_rate:.2f}%) is within acceptable threshold ({threshold}%)"])
        print(gate_status_table)
    else:
        gate_status_table.add_row([colorize("FAILED", Colors.FAIL), f"No tests were run or total_tests is 0. Exiting with error."])
        print(gate_status_table)
        sys.exit(1)

def print_plugin_header():
    plugin_name_art = """
#       ____. ____ ___        .__   __                             
#      |    ||    |   \ ____  |__|_/  |_                           
#      |    ||    |   //    \ |  |\   __\                          
#  /\__|    ||    |  /|   |  \|  | |  |                            
#  _________________/ |___|  /___| |__|                            
#  \__    ___/____    _______/  |_  ______                         
#    |    | _/ __ \  /  ___/\   __\/  ___/                         
#    |    | \  ___/  \___ \  |  |  \___ \                          
#  ______________  >/____  > |__| /____  >     __                  
#  \_   _____/___\/_________    ____ _______ _/  |_   ____ _______ 
#   |    __)_ \  \/  /\____ \  /  _ \\_  __ \\   __\_/ __ \\_  __ \

#   |        \ >    < |  |_> >(  <_> )|  | \/ |  |  \  ___/ |  | \/
#  /_______  //__/\_ \|   __/  \____/ |__|    |__|   \___  >|__|   
#          \/       \/|__|                               \/        
"""


    developer_name = "Developed by: Diego Paes Ramalho Pereira"

    print(colorize(plugin_name_art, Colors.HEADER)) 

    print(colorize(developer_name, Colors.OKGREEN)) 

def main():
    print_plugin_header()
    
    # Retrieve the glob pattern and threshold from environment variables
    pattern = os.getenv('PLUGIN_EXPRESSION', '**/*.xml')  # Default pattern if not specified
    include_dirs = [
        "target/site/serenity",
        "checkstyle",
        "target/failsafe-reports"
    ]
    
    # Instead of processing static directories, use glob with dynamic pattern
    process_directories_glob(pattern)
    output_results()

if __name__ == "__main__":
    main()
