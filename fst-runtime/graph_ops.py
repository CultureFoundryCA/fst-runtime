# reading in from command line , queries
# compile att format into a graph
# read in att files, walk through input/output, give input string (eg aaab) - walk that string through FST, saving its output as we go
# if we finish that walk, see if we're at an accepting state or not
# if we aren't at an accepting state, reject output, otherwise save the output

import os 
from collections import defaultdict
import pprint

class Fst:
    STARTING_STATE = "0"
    def __init__(self, file_path):
        self.file_path = file_path
        self.state = Fst.STARTING_STATE
        # Add empty dictionary if source node doesn't exist.
        self.transitions = defaultdict(dict) 
        self.accepting_states = set()
        self.multichar_symbols = set()
        self._create_transitions()
    
    # Constructing the graph
    def _create_transitions(self):
        lines = [] 
        with open(att_file_path) as att_file: 
            # test = att_file.readlines()
            lines = att_file.readlines()
            # close file

        for line in lines:
            line = line.strip().split("\t")
            if len(line) == 1:
                accepting_state = line[0]
                self.accepting_states.add(accepting_state)
            else:
                current_state, next_state, input_symbol, output_symbol = line
                if len(input_symbol) > 1:
                    self.multichar_symbols.add(input_symbol)

                self.transitions[current_state][input_symbol] = (next_state, output_symbol)    
        
        print(self.accepting_states)
        pprint.pprint(self.transitions)

    def _tokenize_input_string(self, input_string):
        multichar_lengths = list({len(symbol) for symbol in self.multichar_symbols})
        multichar_lengths.sort(reverse=True)
        tokens = []

        while len(input_string) > 0:
            if multichar_lengths:
                for symbol_length in multichar_lengths:
                    try:
                        substring = input_string[0:symbol_length]
                    except IndexError:
                        continue

                    multichar_symbol_match = substring in self.multichar_symbols

                    if multichar_symbol_match:
                        tokens.append(substring)
                        input_string = input_string[symbol_length:]
                        continue
                        
            tokens.append(input_string[0])
            input_string = input_string[1:]
        
        return tokens

    # walk    
    def traverse(self, input_string):
        input_tokens = self._tokenize_input_string(input_string)
        output_string = ""
        print(input_tokens)
        print(self.multichar_symbols)

        for token in input_tokens:
            graph = self.transitions[self.state] 
            try:
                next_state , output_symbol = graph[token] 
            except KeyError:
                return
            output_string += output_symbol
            self.state = next_state
        
        # at this poinit, self.state is not going to change anymore
        # if self.state is in accepting state, save it 
        if self.state in self.accepting_states:
            with open(f"{self.file_path}_result.att", "a+") as text_file:
                text_file.write(output_string + "\n")
            return output_string
        else:
            return ""
        

# TODO figure out os.getenv - not working
# TODO ask how to handle more complicated inputs/outputs - currently reading input character by character,
# how can we handle phrases / multiple characters that map to one character?
# TODO how exactly should we save - currently writing into new .att file



    

if __name__ == "__main__":
    att_file_path = os.getenv("ATT_FILE")
    # att_file_path = "../tests/examples/fst2.att"
    fst = Fst(file_path=att_file_path)
    print(fst.traverse("wal+VERB+GER")) #need to be changed to command line
