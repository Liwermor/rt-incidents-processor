# RT Incident Report Processor Guide

## Preparing Your Environment

Before you start using the RT Incident Report Processor, you need to set up a Python virtual environment. This will keep your dependencies organized and project-specific.

### Setting Up a Virtual Environment

1. Open your command line interface (CLI).
2. Navigate to the folder where you want to store your project.
3. Run the following command to create a new virtual environment:
    ```shell
    python -m venv rt_env
    ```
    This command creates a new folder `rt_env` in your project directory, which will contain the Python virtual environment.

### Activating the Virtual Environment

Depending on your operating system, you activate the virtual environment using one of the following commands:

- On Windows:
    ```shell
    rt_env\Scripts\activate
    ```
- On macOS or Linux:
    ```shell
    source rt_env/bin/activate
    ```

You'll know that you're in the virtual environment when you see the environment's name in parentheses before your command prompt, like so: `(rt_env)`.

### Installing Required Packages

With the virtual environment activated, install the required packages using the `requirements.txt` file provided with the RT Incident Report Processor:

```shell
pip install -r requirements.txt

Now, with the dependencies installed, you're ready to configure the application settings and process incidents.
```
