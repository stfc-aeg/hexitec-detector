import sys
import re
import os
import time

if len(sys.argv) < 3:
    print("You must specify input and output files")
    sys.exit(1)
    
input_file = sys.argv[1]
output_file = sys.argv[2]

define_re = re.compile('#define')
continuation_re = re.compile(r'\+\\$')

param_count = 0

with open(output_file, 'w') as out_fd:
    
    output_file_basename = os.path.basename(output_file)
    out_fd.write('"""{} - EXCALIBUR FEM API parameter definitions\n\n'.format(output_file_basename))
    out_fd.write('Automatically generated on: {} by {} - do not edit manually!\n\n'.format(time.strftime('%c'), sys.argv[0]))
    out_fd.write('"""\n\n')
    
    with open(input_file, 'r') as in_fd:
        for line in in_fd:
            line = line.rstrip()
            param_matched = False

            if define_re.match(line):
                elems = line.split()
                if continuation_re.search(line):
                    param_matched = True
                    param = elems[1]
                    val = ' '.join(elems[2:-1]) + ' + '
                    while True:
                        next_line = in_fd.next().rstrip()
                        next_elems = next_line.split()
                        if continuation_re.search(next_line):
                            val = val + ' '.join(next_elems[:-1]) + ' + '
                        else:
                            val = val + ' '.join(next_elems)
                            break
                        
                else:
                    if len(elems) > 2 and elems[0] == '#define':
                        param_matched = True
                        param = elems[1]
                        val = elems[2]
                        

                if param_matched:
                    param_count += 1
                    out_fd.write("{} = {}\n".format(param, val))
                    
                    
print("Matched {:d} API parameters in file".format(param_count))