import os
import re
from glob import glob

import pandas as pd

files_name = [y for x in os.walk('./data') for y in glob(os.path.join(x[0], '*.xlsx'))]
lines_name = [re.search('L.{1}', name).group(0) for name in files_name]

# df_arr = {}
# for x in files_name:
#     arr = []
#     for y in range(10):
#         arr.append(pd.read_excel(x, sheet_name=y, parse_dates=["Createtime"], index_col="Createtime"))
#     line_name = re.search('L.{1}', x).group(0)
#     df_arr[line_name] = arr

