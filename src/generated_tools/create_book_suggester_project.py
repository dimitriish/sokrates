from toolbox.base_tool import Tool
import os

class CreateBookSuggesterProject(Tool):
    @property
    def tool_desc(self) -> str:
        return "Creates a new directory for the BookSuggester project and sets up a basic Python script file within it."

    @property
    def param_desc(self) -> str:
        return ""

    @staticmethod
    def run(**kwargs):
        project_name = "BookSuggester"
        script_name = "main.py"

        # Create the project directory
        if not os.path.exists(project_name):
            os.makedirs(project_name)

        # Create the main Python script file
        with open(os.path.join(project_name, script_name), 'w') as file:
            file.write("#!/usr/bin/env python\n")
            file.write("import argparse\n")
            file.write("\n")
            file.write("def main():\n")
            file.write("    parser = argparse.ArgumentParser(description='BookSuggester CLI')\n")
            file.write("    args = parser.parse_args()\n")
            file.write("    print('Welcome to the BookSuggester project!')\n")
            file.write("\n")
            file.write("if __name__ == '__main__':\n")
            file.write("    main()")

        result = f"Project '{project_name}' created with script '{script_name}'."
        return result