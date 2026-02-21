import os
import tempfile
import subprocess
import shutil

class CodeEvaluationEnvironment:
    def __init__(self, sandbox_dir=None):
        """
        Initialize the code evaluation environment.
        :param sandbox_dir: Optional. Directory to use as a sandbox for code evaluation.
        """
        self.sandbox_dir = sandbox_dir or tempfile.mkdtemp()
        self.cleanup_required = sandbox_dir is None
        self.execution_timeout = 5  # Timeout for code execution in seconds

    def setup_environment(self):
        """
        Sets up the sandbox environment for code execution.
        Ensures the sandbox directory exists and is clean.
        """
        if not os.path.exists(self.sandbox_dir):
            os.makedirs(self.sandbox_dir)
        else:
            self._clean_sandbox()

    def evaluate_code(self, source_code, input_data):
        """
        Evaluates the provided source code with the given input data.
        :param source_code: The code to be executed.
        :param input_data: Input data to provide to the code during execution.
        :return: A dictionary containing the success status, output, and errors (if any).
        """
        result = {"success": False, "output": "", "error": ""}

        try:
            # Write source code to a temporary file
            source_code_path = os.path.join(self.sandbox_dir, "solution.py")
            with open(source_code_path, "w") as code_file:
                code_file.write(source_code)

            # Write input data to a temporary file
            input_data_path = os.path.join(self.sandbox_dir, "input.txt")
            with open(input_data_path, "w") as input_file:
                input_file.write(input_data)

            # Execute the code
            command = ["python", source_code_path]
            with open(input_data_path, "r") as stdin, tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
                process = subprocess.Popen(command, stdin=stdin, stdout=stdout, stderr=stderr, cwd=self.sandbox_dir)
                try:
                    process.wait(timeout=self.execution_timeout)
                except subprocess.TimeoutExpired:
                    process.kill()
                    result["error"] = "Execution timed out."
                    return result

                stdout.seek(0)
                stderr.seek(0)
                result["output"] = stdout.read().decode()
                result["error"] = stderr.read().decode()

            result["success"] = process.returncode == 0 and not result["error"]

        except Exception as e:
            result["error"] = str(e)

        return result

    def cleanup_environment(self):
        """
        Cleans up the sandbox environment after code execution.
        Deletes temporary files and directories if they were created for the evaluation.
        """
        if self.cleanup_required:
            self._clean_sandbox()
            os.rmdir(self.sandbox_dir)

    def _clean_sandbox(self):
        """
        Removes all files in the sandbox directory.
        """
        for filename in os.listdir(self.sandbox_dir):
            file_path = os.path.join(self.sandbox_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")

    def __del__(self):
        """
        Destructor to ensure the sandbox environment is cleaned up.
        """
        self.cleanup_environment()