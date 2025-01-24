from toolbox.base_tool import Tool

class ChangeSystemTheme(Tool):
    @property
    def tool_desc(self) -> str:
        return "Changes the system's theme based on user confirmation"

    @property
    def param_desc(self) -> str:
        return ""

    @staticmethod
    def run(**kwargs):
        try:
            # Execute the command to change the system theme to dark
            import subprocess
            subprocess.run(['gsettings', 'set', 'org.gnome.desktop.interface', 'gtk-theme', "'Adwaita-dark'"], check=True)
            result = "System theme changed to dark mode"
        except Exception as e:
            result = f"Failed to change system theme: {str(e)}"
        return result