# reading in from command line , queries
# compile att format into a graph
# read in att files, walk through input/output, give input string (eg aaab) - walk that string through FST, saving its output as we go
# if we finish that walk, see if we're at an accepting state or not
# if we aren't at an accepting state, reject output, otherwise save the output

import os 

att_file_path = os.getenv("ATT_FILE")

#with opens scope for open function, stays in open/editing state - with automatically closes it for us
def file_test():

    with open(att_file_path) as att_file: 
        test = att_file.readlines()
        print(test)
        
if __name__ == "__main__":
    file_test()
