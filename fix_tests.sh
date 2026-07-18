#!/bin/bash
find tests -type f -name "*.py" -exec sed -i 's/from actool_linux/from actool_linux.stable/g' {} +
find tests -type f -name "*.py" -exec sed -i 's/import actool_linux/import actool_linux.stable/g' {} +
