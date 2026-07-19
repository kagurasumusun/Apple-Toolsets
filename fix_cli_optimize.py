with open("actool_linux/nextgen/cli.py", "r") as f:
    cl_lines = f.readlines()
for i in range(len(cl_lines)):
    if "p.add_argument(\"--capabilities\", action=\"store_true\")" in cl_lines[i]:
        cl_lines.insert(i+1, "    p.add_argument(\"--optimize\", choices=(\"smart\", \"astc\"), default=None)\n")
        break
with open("actool_linux/nextgen/cli.py", "w") as f:
    f.writelines(cl_lines)
