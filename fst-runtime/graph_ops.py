# reading in from command line , queries
# compile att format into a graph
# read in att files, walk through input/output, give input string (eg aaab) - walk that string through FST, saving its output as we go
# if we finish that walk, see if we're at an accepting state or not
# if we aren't at an accepting state, reject output, otherwise save the output

import os 
from collections import defaultdict
import pprint

class FST:
    def __init__(self, file_path):
        self.file_path = file_path
        self.state = "0"
        self.transitions = defaultdict(dict) #add empty list if source node doesn't exist
        self.accepting_states = set()
    
    # constructing the graph
    def create_transitions(self):
        lines = [] 
        with open(att_file_path) as att_file: 
            # test = att_file.readlines()
            lines = att_file.readlines()
            # close file

        for line in lines:
            line = line.replace("\n", "")
            line = line.split("\t")
            if len(line) == 1:
                # do something with accepting state
                self.accepting_states.add(line[0])
            else:
                current_state, next_state, inp, outp = line

                self.transitions[current_state][inp] = (next_state, outp)    
        
        print(self.accepting_states)
        pprint.pprint(self.transitions)

    # walk    
    def traverse(self, input_string):
        res = ""
        for char in input_string:
            graph = self.transitions[self.state] 
            next_state , outp = graph[char] 
            res += outp
            self.state = next_state
        
        # at this poinit, self.state is not going to change anymore
        # if self.state is in accepting state, save it 
        if self.state in self.accepting_states:
            with open("{}_result.att".format(self.file_path), "a+") as text_file:
                text_file.write(res + "\n")
            return res
        else:
            return ""
        

# TODO figure out os.getenv - not working
# TODO ask how to handle more complicated inputs/outputs - currently reading input character by character,
# how can we handle phrases / multiple characters that map to one character?
# TODO how exactly should we save - currently writing into new .att file


# att_file_path = os.getenv("ATT_FILE")
att_file_path = "../tests/examples/fst2.att"
    

if __name__ == "__main__":
    fst = FST(file_path=att_file_path)
    fst.create_transitions()
    print(fst.traverse("ad")) #need to be changed to command line
