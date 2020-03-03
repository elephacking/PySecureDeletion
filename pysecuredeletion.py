#!/usr/bin/python
from __future__ import print_function
#from argparse import ArgumentParser
import re
from secure_delete import secure_delete
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import platform
import os
import hashlib
import pdfkit
import datetime
import shutil


#parser = ArgumentParser()
#parser.add_argument("pos1", help="positional argument 1")
#parser.add_argument("-o", "--optional-arg", help="optional argument", dest="opt", default="default")
#args = parser.parse_args()
#print("positional arg:", args.pos1)
#print("optional arg:", args.opt)


template = r'''<h2><strong>PySecureDeletion v1.0</strong></h2>
<p><strong>Hostname</strong>:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {%hostname%}</p>
<p><strong>Timestamp</strong>:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {%timestamp%}</p>
<p><strong>Directory</strong>:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {%directory%}</p>
<p><strong>Deleted File</strong>:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {%deleted_file%}</p>
<table width="100%">
<tbody>
<tr>
<td width="27%">
<p><strong>File Name</strong></p>
</td>
<td width="33%">
<p><strong>SHA256 Hash</strong></p>
</td>
<td width="21%">
<p><strong>Path</strong></p>
</td>
<td width="17%">
<p><strong>Status</strong></p>
</td>
</tr>
{%log_start%}
<tr>
<td width="27%">
<p><strong>{%log_filename%}</strong></p>
</td>
<td width="33%">
<p>{%log_hash%}</p>
</td>
<td width="21%">
<p>{%log_path%}</p>
</td>
<td width="17%">
<p>{%log_status%}</p>
</td>
</tr>
{%log_end%}
</tbody>
</table>
'''

log_row_template = re.search('{%log_start%}(.*?){%log_end%}', template, re.S).groups()[0]
template = re.sub(log_row_template, '', template)
report = template

def sha256sum(filename):
    h  = hashlib.sha256()
    b  = bytearray(128*1024)
    mv = memoryview(b)
    with open(filename, 'rb', buffering=0) as f:
        for n in iter(lambda : f.readinto(mv), 0):
            h.update(mv[:n])
    return h.hexdigest()

def add_to_report(arg, value):
    global report
    if arg in ['hostname', 'timestamp', 'directory', 'deleted_file']:
        report = report.replace('{%'+arg+'%}', value)
    elif arg == 'log':
        log_row_template_temp = log_row_template
        for arg2, value2 in value.items():
            log_row_template_temp = log_row_template_temp.replace('{%'+arg2+'%}', value2)
        idx = report.index('{%log_end%}')
        report = report[:idx] + log_row_template_temp + report[idx:]
    return report

def finalize_report():
    global report
    add_to_report('timestamp', str(datetime.datetime.now()))
    final_report = report
    final_report = re.sub('{%log_start%}', '', final_report)
    final_report = re.sub('{%log_end%}', '', final_report)
    return final_report

def delete_main(base_dir):
    print('Start Deleting')
    secure_delete.secure_random_seed_init()
    add_to_report('directory', base_dir)
    list_paths = secure_delete.enum_paths(base_dir)
    deleted_file_count = 0
    for file in list_paths:
        log = {'log_filename': os.path.basename(file), 'log_hash': sha256sum(file), 'log_path': file, 'log_status': ''}
        try:
            secure_delete.secure_delete(file)
            log['log_status'] = 'Cleaned'
            deleted_file_count = deleted_file_count + 1
        except Exception as e:
            log['log_status'] = e.message
        add_to_report('log', log)
    #delete the folder
    shutil.rmtree(base_dir, ignore_errors=True)
    add_to_report('deleted_file', '%d/%d' % (deleted_file_count, len(list_paths)))
    #print(list_paths)
    
    
def main():
    add_to_report('hostname', platform.node())
    root = tk.Tk()
    root.withdraw()
    dirname = filedialog.askdirectory(parent=root,initialdir="/",title='Select a folder to erase')
    msgbox = tk.messagebox.askquestion ('Erase Confirmation','Are you sure you want to erase the folder: ' + dirname, icon = 'warning')
    if msgbox == 'yes':
        delete_main(dirname)
        log_file = filedialog.asksaveasfile(mode='wb', filetypes = [('PDF', '*.pdf')], defaultextension='.pdf', title='Log file path')
        if log_file is not None:
            final_report = finalize_report()
            log_file.write(pdfkit.from_string(final_report, False))
            log_file.close()
        print('Deletion Completed')
    #file_path = filedialog.askopenfilename()

    
if __name__ == "__main__":
    main()