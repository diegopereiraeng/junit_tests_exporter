# JUnit Tests Exporter

## Overview

The JUnit Tests Exporter script processes JUnit XML report files, generating test statistics, including total tests run, total failures, and a failure rate. It outputs these metrics along with a gate status that indicates whether the failure rate exceeds a predefined threshold. This tool is especially useful in CI/CD pipelines for gating deployments based on test outcomes.

## Features

- **Test Metrics Calculation**: Calculates and reports test statistics.
- **Gate Status Reporting**: Determines pass/fail status based on a configurable failure rate threshold.
- **Environment Variables**: Sets key metrics as environment variables for downstream use.
- **Visual Reporting**: Utilizes ANSI color codes and PrettyTable for enhanced console output.
- **Docker Integration**: Packaged as a Docker image for easy integration into CI/CD pipelines.

## Prerequisites

When using the `diegokoala/junit_tests_exporter:latest` Docker image, no additional setup for Python or PrettyTable is required.

## Configuration

- **`EXPRESSION`**: (Optional) Glob pattern to match JUnit XML files. Defaults to `**/*.xml`.
- **`THRESHOLD`**: (Optional) Failure rate acceptance threshold as a percentage. Defaults to `0`. Any error fails by default

## Usage

### Harness CI/CD

Example step configuration in Harness where threshold is 3 if the 2 variables comparinson matches:

```yaml
steps:
  - step:
      type: Plugin
      name: junit_tests_exporter
      identifier: junit_tests_exporter
      spec:
        connectorRef: account.dockerHub
        image: diegokoala/junit_tests_exporter:latest
        settings:
          PLUGIN_THRESHOLD: "<+<+stage.variables.filter_tags> == \"test_api\" && <+stage.variables.environment> == 'dev' ? 3 : 0>"
```

### Drone CI

Example `.drone.yml` step:

```yaml
steps:
  - name: junit-tests-exporter
    image: diegokoala/junit_tests_exporter:latest
    commands:
      - junit_tests_exporter.py
    environment:
      PLUGIN_EXPRESSION: "**/*.xml"
      PLUGIN_THRESHOLD: 5
```

## Customization

The script and Docker image are designed to be flexible for integration into various CI/CD workflows. You can adjust the environment variables and threshold logic as needed to suit your specific requirements.

## Support

For any support-related queries, issues, or contributions, please refer to the project's GitHub repository. Your feedback and contributions are highly appreciated and help in improving the tool.

## Installation

No installation is required when using the `diegokoala/junit_tests_exporter:latest` Docker image in your CI/CD pipelines. For local development or testing, ensure you have Docker installed and run the following command:

```bash
docker pull diegokoala/junit_tests_exporter:latest
```

This command pulls the latest version of the JUnit Tests Exporter Docker image to your local machine.

## Local Usage

To run the JUnit Tests Exporter locally using Docker, you can use the following command:

```bash
docker run --rm -v $(pwd):/data diegokoala/junit_tests_exporter:latest junit_tests_exporter.py
```

Ensure to adjust the command based on your specific file paths or additional parameters.

## Contributing

Contributions to the JUnit Tests Exporter are welcome! If you have suggestions for improvements or have encountered issues, please feel free to open an issue or pull request on the GitHub repository.

## License

The JUnit Tests Exporter is released under the MIT License. See the LICENSE file in the GitHub repository for full details.

