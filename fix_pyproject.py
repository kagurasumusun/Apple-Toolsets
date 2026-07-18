with open("pyproject.toml", "r") as f:
    lines = f.readlines()

has_pkg_data = any("package-data" in line for line in lines)
if not has_pkg_data:
    lines.append("\\n[tool.setuptools.package-data]\\n")
    lines.append("\"*\" = [\"*.json\"]\\n")

with open("pyproject.toml", "w") as f:
    f.writelines(lines)
