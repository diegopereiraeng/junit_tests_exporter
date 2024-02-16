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

def colorize_multiline(text, color):
    """
    Applies ANSI color codes to each line in a multi-line string.
    """
    colored_lines = [f"{color}{line}{Colors.ENDC}" for line in text.split('\n')]
    return '\n'.join(colored_lines)

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
num_errors = 0
failed_tests_details = []
error_tests_details = []

def process_xml_file(file_path):
    global num_tests, num_failures, num_errors
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Check the COUNT_MODE environment variable
        count_mode = os.getenv('PLUGIN_COUNT_MODE', 'aggregate').lower()
        
        tests_in_file = 0
        failures_in_file = 0
        errors_in_file = 0

        if count_mode == 'aggregate':
            # for testsuite in root.findall('.//testsuite'):
            tests_in_file += int(root.get('tests', 0))
            failures_in_file += int(root.get('failures', 0))
            errors_in_file += int(root.get('errors', 0))
            if os.getenv('PLUGIN_DEBUG', 'false') == "true":
                # Debug print
                print(f"DEBUG: {root.get('name')}: Tests={tests_in_file}, Failures={failures_in_file}, Errors={errors_in_file}")
            
            num_tests += tests_in_file
            num_failures += failures_in_file
            num_errors += errors_in_file
        elif count_mode == 'individual':
            # Iterate over each testcase element and count them as individual tests
            for testcase in root.findall('.//testcase'):
                num_tests += 1  # Counting each testcase as an individual test
                tests_in_file += 1  # Counting each testcase as an individual test
                # If there's a failure or an error, increment the respective counters
                if testcase.find('failure') is not None:
                    num_failures += 1
                    failures_in_file += 1
                if testcase.find('error') is not None:
                    num_errors += 1
                    errors_in_file += 1  
        
        # Common logic for processing test details
        for testcase in root.findall('.//testcase'):
            process_test_details(testcase)

        log_info(f"Processed file '{file_path}' successfully.")
        # Logging individual or aggregate counts based on COUNT_MODE
        if tests_in_file > 0:
            log_success(f"Processed '{tests_in_file}' tests in file (Mode: {count_mode}).")
            if os.getenv('PLUGIN_DEBUG', 'false') == "true":
                # Serialize the entire XML tree to a byte string and decode it
                xml_str = ET.tostring(root, encoding='unicode')
                print(xml_str)
        if errors_in_file > 0:
            log_warning(f"Processed '{errors_in_file}' errors in file.")
        if failures_in_file > 0:
            log_warning(f"Processed '{failures_in_file}' failures in file.")
    except Exception as e:
        log_error_with_traceback(f"Error processing file '{file_path}'", e)


def process_test_details(testcase):
    global failed_tests_details, error_tests_details
    # Extract and store failure/error details from each testcase
    failure = testcase.find('failure')
    error = testcase.find('error')
    system_error = testcase.find('system-err')

    if failure is not None:
        failed_tests_details.append({
            'class': testcase.get('classname'),
            'name': testcase.get('name'),
            'message': failure.get('message'),
            'type': "N/A" if failure.get('type') is None else failure.get('type'),
            'failure': failure.text,
            'stack_trace': "N/A" if system_error is None else system_error.text,
        })

    if error is not None:
        error_tests_details.append({
            'class': testcase.get('classname'),
            'name': testcase.get('name'),
            'message': error.get('message'),
            'type': "N/A" if error.get('type') is None else error.get('type'),
            'failure': error.text,
            'stack_trace': "N/A" if system_error is None else system_error.text,
        })

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
    
    # Error tests table, similar to failed tests table
    if error_tests_details:
        error_tests_table = PrettyTable()
        error_tests_table.field_names =  ["Class", "Test", "Message", "Type", "Stack Traces", "Errors"]
        error_tests_table.align = "l"
        error_tests_table._min_width = {"Stack Trace" : 180}
        error_tests_table._max_width = {"Stack Trace" : 180, "Test" : 40}
        for test in error_tests_details:
            error_tests_table.add_row([
                colorize(test['class'], Colors.BOLD),
                test['name'],
                colorize_multiline(test['message'], Colors.WARNING),
                colorize(test['type'], Colors.WARNING),  # Warning messages in yellow
                colorize_multiline(test['stack_trace'], Colors.FAIL),  # Error details in red
                colorize_multiline(test['failure'], Colors.FAIL)  # Error details in red
            ])
    if failed_tests_details:
        # Creating a table for failed tests details
        failed_tests_table = PrettyTable()
        failed_tests_table.field_names = ["Class", "Test", "Message", "Type", "Stack Traces", "Errors"]
        failed_tests_table.align = "l"

        # Adjust the 'max_width' settings for the columns
        # failed_tests_table.max_width["Test"] = 50  # Set a narrower max width for the Test column
        # failed_tests_table.max_width["Stack Trace"] = 600  # Set a wider max width for the Stack Trace column
        failed_tests_table._min_width = {"Stack Trace" : 180}
        failed_tests_table._max_width = {"Stack Trace" : 180, "Test" : 40}
        

        for test in failed_tests_details:
            # failed_tests_table.add_row([test['class'], colorize(f"{test['name']}", Colors.WARNING), colorize(f"{test['message']}", Colors.WARNING) , colorize(f"{test['stack_trace']}", Colors.FAIL)])
            failed_tests_table.add_row([
                colorize(test['class'], Colors.BOLD),  # Make class names bold
                test['name'],  # Keep test names in default color for neutrality
                colorize_multiline(test['message'], Colors.WARNING),  # Warning messages in yellow
                colorize(test['type'], Colors.WARNING),  # Warning messages in yellow
                colorize_multiline(test['stack_trace'], Colors.FAIL),  # Error details in red
                colorize_multiline(test['failure'], Colors.FAIL)  # Error details in red
            ])
        
        
    # Gate Status Table
    gate_status_table = PrettyTable()
    gate_status_table.field_names = ["Gate Status", "Details"]
    if num_tests > 0:
        errors_failures = num_failures + num_errors
        failure_rate = (errors_failures / num_tests) * 100  # Calculate failure_rate immediately after checking num_tests
        
        num_failures_text = colorize(errors_failures, Colors.FAIL if num_failures > 0 else Colors.OKGREEN)
        failure_rate_text = colorize(f"{failure_rate:.2f}%", Colors.OKGREEN if failure_rate == 0 else Colors.WARNING if failure_rate < 80 else Colors.FAIL)

        if num_errors > 0:
            print(colorize(f"{num_errors} Errors Found!", Colors.FAIL))
            print(colorize("Error Tests Details List:", Colors.FAIL))
            print(error_tests_table)
        
        if num_failures > 0:
            print(colorize(f"{num_failures} Failed Tests Found!", Colors.FAIL))
            print(colorize("Failed Tests Details List:", Colors.FAIL))
            print(failed_tests_table)

        # Summary table
        summary_table = PrettyTable()
        summary_table.field_names = ["Total Tests", "Total Errors/Failures", "Failure Rate"]
        summary_table.add_row([num_tests, num_failures_text, failure_rate_text])
        print(summary_table)

        # Serialize the failure and error details to single-line JSON strings
        failures_json_string = json.dumps(failed_tests_details, separators=(',', ':'))
        errors_json_string = json.dumps(error_tests_details, separators=(',', ':'))
        if os.getenv('PLUGIN_DEBUG', 'false') == "true":
            log_info("Error JSON")
            log_info(errors_json_string)
            log_info("Failed JSON")
            log_info(failures_json_string)
            
        # failures_json_string = json.dumps(failed_tests_details, sort_keys=True, indent=0)
        # errors_json_string = json.dumps(error_tests_table, sort_keys=True, indent=0)

        # Setting environment variables using os.environ
        os.environ['TOTAL_TESTS'] = str(num_tests)
        os.environ['TOTAL_FAILURES'] = str(num_failures)
        os.environ['TOTAL_ERRORS'] = str(num_errors)
        os.environ['FAILURE_RATE'] = str(failure_rate) 
        os.environ['FAILURES_TESTS_JSON'] = failures_json_string
        os.environ['ERRORS_TESTS_JSON'] = errors_json_string

        # Prepare your environment variables for writing to the .env file
        env_variables = {
            "TOTAL_TESTS": str(num_tests),
            "TOTAL_FAILURES": str(num_failures),
            "TOTAL_ERRORS": str(num_errors),
            "TOTAL_ERRORS_FAILED": str(num_errors+num_failures),
            "FAILURE_RATE": str(failure_rate),
            "FAILURES_TESTS_JSON": failures_json_string.replace("\n", ""),
            "ERRORS_TESTS_JSON": errors_json_string.replace("\n", ""),
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
