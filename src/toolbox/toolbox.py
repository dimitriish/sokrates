import os
import json
from typing import Optional, Dict, Type
from .base_tool import Tool
import sys


# Ensure the 'tools' directory exists
TOOLS_DIR = "./generated_tools"
os.makedirs(TOOLS_DIR, exist_ok=True)

class ToolManager:
    def __init__(self, tools_dir: str = TOOLS_DIR):
        self.tools_dir = tools_dir
        # Ensure tools directory is in sys.path to allow imports
        if self.tools_dir not in sys.path:
            sys.path.append(self.tools_dir)

    def _tool_filename(self, tool_name: str) -> str:
        """Get the .py file name for a given tool name."""
        return os.path.join(self.tools_dir, f"{tool_name}.py")

    def add_tool(self, tool_name: str, tool_code: str) -> bool:
        """
        Saves the generated tool code to a .py file.
        
        Returns True if successful, False otherwise.
        """
        output_file = self._tool_filename(tool_name)
        if os.path.exists(output_file):
            print(f"Tool '{tool_name}' already exists at {output_file}.")
            return False
        try:
            with open(output_file, 'w') as file:
                file.write(tool_code)
            print(f"Tool '{tool_name}' has been created at {output_file}.")
            return True
        except Exception as e:
            print(f"Error saving tool '{tool_name}': {e}")
            return False

    def delete_tool(self, tool_name: str) -> bool:
        """
        Deletes the .py file for the specified tool.
        Returns True if successful, False if tool doesn't exist.
        """
        py_path = self._tool_filename(tool_name)
        if os.path.exists(py_path):
            os.remove(py_path)
            print(f'{tool_name} deleted')
            return True
        return False

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """
        Imports the tool_name.py module, finds a class inheriting from Tool, 
        instantiates it, and returns it.
        Returns None if not found.
        """
        import importlib.util
        import sys

        py_path = self._tool_filename(tool_name)
        if not os.path.exists(py_path):
            print(f"Tool file for {tool_name} not found at {py_path}.")
            return None

        # Remove cached module if already imported
        module_name = f"{tool_name}"
        if module_name in sys.modules:
            del sys.modules[module_name]

        try:
            # Dynamically import the tool module
            spec = importlib.util.spec_from_file_location(module_name, py_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore

            # Find a class inheriting from Tool
            tool_class = self._find_tool_class(module)
            if tool_class is None:
                print(f"No valid Tool class found in {tool_name}.py.")
                return None

            # Instantiate and return
            return tool_class()
        except Exception as e:
            print(f"Error loading tool {tool_name}: {e}")
            return None

    def list_tools(self) -> Dict[str, str]:
        """
        Lists all tool .py files in the tools directory, imports them, 
        and retrieves their name and description.
        Returns a dict {tool_name: description}.
        """
        tools = {}
        for filename in os.listdir(self.tools_dir):
            if filename.endswith(".py"):
                tool_name = filename[:-3]  # Remove the .py extension
                try:
                    tool_obj = self.get_tool(tool_name)
                    if tool_obj is not None:
                        tools[tool_name] = f"{tool_obj.tool_desc}. Params: {tool_obj.param_desc}"
                except Exception as e:
                    print(f"Error loading tool {tool_name}: {e}")
        if len(tools.keys()) == 0:
            return "There are no tools yet"
        return tools

    def _find_tool_class(self, module) -> Optional[Type[Tool]]:
        """
        Find a class in the given module that inherits from Tool.
        Return that class type or None if not found.
        """
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, Tool) and attr is not Tool:
                return attr
        return None
