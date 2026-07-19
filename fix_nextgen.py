with open("actool_linux/nextgen/smart_cbck.py", "r") as f:
    lines = f.readlines()
for i in range(len(lines)):
    if "from ..stable import lzfse_compat as lzfse" in lines[i]:
        lines[i] = "    from actool_linux.stable import lzfse_compat as lzfse\n"

with open("actool_linux/nextgen/smart_cbck.py", "w") as f:
    f.writelines(lines)
