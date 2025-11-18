"""
Regex to NFA to DFA Converter

This module converts regular expressions to NFAs and then to DFAs using:
- Lexer: Tokenizes the regex string
- Parser: Builds an AST from tokens
- Thompson Construction: Converts AST to NFA
- NFA to DFA Conversion: Converts NFA to DFA
"""

# ============================================================================
# LEXER
# Input: a string
# Output: a list of tokens
# ============================================================================

from enum import Enum, auto

class TokenType(Enum):
    OR = auto()
    STAR = auto()
    PLUS = auto()
    QUESTION_MARK = auto()
    OPEN_PAREN = auto()
    CLOSED_PAREN = auto()
    OPEN_SQUARE_BRACKET = auto()
    CLOSED_SQUARE_BRACKET = auto()
    DASH = auto()
    LITERAL = auto()

def getTypeToken(token):
    if token == '|':
        return TokenType.OR
    elif token == '*':
        return TokenType.STAR
    elif token == '+':
        return TokenType.PLUS
    elif token == '?':
        return TokenType.QUESTION_MARK
    elif token == '(':
        return TokenType.OPEN_PAREN
    elif token == ')':
        return TokenType.CLOSED_PAREN
    elif token == '[':
        return TokenType.OPEN_SQUARE_BRACKET
    elif token == ']':
        return TokenType.CLOSED_SQUARE_BRACKET
    elif token == '-':
        return TokenType.DASH
    else:
        return TokenType.LITERAL

def getTokenValue(token):
    if token==TokenType.OR:
        return '|'
    elif token==TokenType.STAR:
        return '*'
    elif token==TokenType.PLUS:
        return '+'
    elif token==TokenType.QUESTION_MARK:
        return '?'
    elif token==TokenType.OPEN_PAREN:
        return '('
    elif token==TokenType.CLOSED_PAREN:
        return ')'
    elif token==TokenType.OPEN_SQUARE_BRACKET:
        return '['
    elif token==TokenType.CLOSED_SQUARE_BRACKET:
        return ']'
    elif token==TokenType.DASH:
        return '-'
    else:
        return token

class Token:
    ttype: TokenType
    content: str
    def __init__(self, ttype, content):
        self.ttype = ttype
        self.content = content

class regexLexer:
    # input: regex string
    # output: token stream
    def __init__(self, regexStr):
        self.regexStr = regexStr
    def lexer(self):
        tokenStream = []
        for i in range(len(self.regexStr)):
            token = Token(getTypeToken(self.regexStr[i]), self.regexStr[i])
            tokenStream.append(token)
        return tokenStream

# ============================================================================
# PARSER
# Input: a list of tokens
# Output: a list of AST nodes
# ============================================================================

from abc import ABC, abstractmethod

class AstNode(ABC):
    @abstractmethod
    def __init__(self):
        pass

class OrAstNode(AstNode):
    def __init__(self, left, right):
        self.left = left
        self.right = right
    
class SeqAstNode(AstNode):
    def __init__(self, left, right):
        self.left = left
        self.right = right

class StarAstNode(AstNode):
    def __init__(self, left):
        self.left = left

class PlusAstNode(AstNode):
    def __init__(self, left):
        self.left = left

class QuestionMarkAstNode(AstNode):
    def __init__(self, left):
        self.left = left

class LiteralCharacterAstNode(AstNode):
    def __init__(self, char):
        self.char = char

class SquareBracketAstNode(AstNode):
    # clas: set #of strs and pairs
    # for example: [a-z] -> {'a', 'b', 'c', ..., 'z'}
    # [a-z0-9] -> {'a', 'b', 'c', ..., 'z', '0', '1', ..., '9'
    # [a-Z012] -> {'a', 'b', 'c', ..., 'Z', '0', '1', '2'}
    def __init__(self, clas):
        self.clas = clas

def print_ast(node, indent=0):
    if isinstance(node, OrAstNode):
        print(' ' * indent + 'OR')
        print_ast(node.left, indent + 2)
        print_ast(node.right, indent + 2)
    elif isinstance(node, SeqAstNode):
        print(' ' * indent + 'SEQ')
        print_ast(node.left, indent + 2)
        print_ast(node.right, indent + 2)
    elif isinstance(node, StarAstNode):
        print(' ' * indent + 'STAR')
        print_ast(node.left, indent + 2)
    elif isinstance(node, PlusAstNode):
        print(' ' * indent + 'PLUS')
        print_ast(node.left, indent + 2)
    elif isinstance(node, QuestionMarkAstNode):
        print(' ' * indent + 'QUESTION_MARK')
        print_ast(node.left, indent + 2)
    elif isinstance(node, LiteralCharacterAstNode):
        print(' ' * indent + 'LITERAL: ' + node.char)
    elif isinstance(node, SquareBracketAstNode):
        print(' ' * indent + 'SQUARE_BRACKET')
        for char in node.clas:
            if isinstance(char, tuple):
                print(' ' * (indent + 2) + 'RANGE: {}-{}'.format(char[0], char[1]))
            else:
                print(' ' * (indent + 2) + 'CHARACTER: {}'.format(char))
    else:
        raise ValueError('Invalid AST node type')

## let's define a CFG for the language
# S -> E
# E -> T '|' E | T
# T -> C F T | C
# F -> '*' | '+' | '?' | epsilon
# C -> L | '(' E ')' | '[' L DASH L ']' | epsilon
# L -> LITERAL | ESCAPED
# OR -> '|' | epsilon
# STAR -> '*' | epsilon
# PLUS -> '+' | epsilon
# QUESTION_MARK -> '?' | epsilon
# OPEN_PAREN -> '(' | epsilon
# CLOSED_PAREN -> ')' | epsilon
# OPEN_SQUARE_BRACKET -> '[' | epsilon
# CLOSED_SQUARE_BRACKET -> ']' | epsilon
# DASH -> '-' | epsilon
# LITERAL -> any character except '|' '*', '+', '?', '(', ')', '[', ']', '\\', and '-' 

class ParseRegex:
    def __init__(self, tokenStream):
        self.tokenStream = tokenStream
        self.currToken = 0

    
    def parse(self):
        ast = self.parse_E()
        if self.currToken < len(self.tokenStream):
            raise Exception("Unexpected token")
        return ast

    def parse_E(self):
        ast = self.parse_T()
        if self.match(TokenType.OR):
            left = ast
            right = self.parse_E()
            ast = OrAstNode(left, right)
        return ast

    def parse_T(self):
        ast = self.parse_C()
        if self.currToken < len(self.tokenStream):
            ttype = self.tokenStream[self.currToken].ttype
            if ttype in [TokenType.LITERAL, TokenType.OPEN_PAREN, TokenType.OPEN_SQUARE_BRACKET]:
                left = ast
                right = self.parse_T()
                ast = SeqAstNode(left, right)
        return ast

    def parse_C(self):
        if self.match(TokenType.LITERAL):
            ast = LiteralCharacterAstNode(self.tokenStream[self.currToken - 1].content)
        elif self.match(TokenType.OPEN_PAREN):
            ast = self.parse_E()
            self.expect(TokenType.CLOSED_PAREN)
        elif self.match(TokenType.OPEN_SQUARE_BRACKET):
            clas = self.parse_L()
            self.expect(TokenType.CLOSED_SQUARE_BRACKET)
            ast = SquareBracketAstNode(clas)
        else:
            ast = AstNode()
        if self.match(TokenType.STAR):
            ast = StarAstNode(ast)
        elif self.match(TokenType.PLUS):
            ast = PlusAstNode(ast)
        elif self.match(TokenType.QUESTION_MARK):
            ast = QuestionMarkAstNode(ast)
        return ast

    def parse_L(self):
        clas = set()
        que = []
        while self.currToken < len(self.tokenStream):
            ttype = self.tokenStream[self.currToken].ttype
            if ttype == TokenType.CLOSED_SQUARE_BRACKET:
                break
            elif ttype == TokenType.LITERAL:
                clas.add(self.tokenStream[self.currToken].content)
                que.append(self.tokenStream[self.currToken].content)
            elif ttype == TokenType.DASH:
                if len(clas) == 0 or self.currToken + 1 == len(self.tokenStream) or self.tokenStream[self.currToken + 1].ttype == TokenType.CLOSED_SQUARE_BRACKET:
                    clas.add('-')
                else:
                    # get last character in que
                    start = ord(que.pop())
                    end = ord(self.tokenStream[self.currToken + 1].content)
                    # print(chr(start), chr(end))
                    for i in range(start, end + 1):
                        clas.add(chr(i))
                    self.currToken += 1
            self.currToken += 1
        return clas

    def match(self, ttype):
        if self.currToken >= len(self.tokenStream):
            return False
        if self.tokenStream[self.currToken].ttype == ttype:
            self.currToken += 1
            return True
        return False

    def expect(self, ttype):
        if not self.match(ttype):
            raise Exception("Expected token", getTokenValue(ttype))

# ============================================================================
# AST to NFA
# Input: a list of AST nodes
# Output: a NFA
# ============================================================================

from collections import deque

class NFA:
    def __init__(self, starting_state,final_state, states):
        self.starting_state = starting_state
        self.final_state = final_state
        self.states = states
    dect = {}
    index = 0
    def stateToNumber(self, state):
        if state in self.dect:
            return str(self.dect[state])
        else:
            self.dect[state] = self.index
            self.index += 1
            return str(self.dect[state])
        
    
    def to_dict(self):
        nfa_dict = {}
        nfa_dict['startingState'] = self.stateToNumber(self.starting_state)
        for state_name, state in self.states.items():
            transitions = {}
            for symbol, next_states in state.items():
                if symbol == '':
                    symbol = 'epsilon'
                arr = []
                for next_state in next_states:
                    arr.append(self.stateToNumber(next_state))
                transitions[symbol] = arr
            
            nfa_dict[self.stateToNumber(state_name)] = {
                'isTerminatingState': self.stateToNumber(state_name) == self.stateToNumber(self.final_state),
                **transitions
            }
            
        return nfa_dict

class ThompsonConstruction:
    def __init__(self, ast):
        self.ast = ast

    def construct(self):
        starting_state, final_state, states = self._construct_from_ast(self.ast)
        return NFA(starting_state,final_state, states)

    def _construct_from_ast(self, node):
        if isinstance(node, LiteralCharacterAstNode):
            starting_state = object()
            final_state = object()
            states = {
                starting_state: {node.char: {final_state}},
                final_state: {'': set()}
            }
            return starting_state, final_state, states
        
        elif isinstance(node, PlusAstNode):
            # (a|epsilon)+
            # one or more
            sub_start, sub_final, sub_states = self._construct_from_ast(node.left)
            starting_state = object()
            final_state = object()
            states = {
                starting_state: {'': {sub_start}},
                **sub_states,
                sub_final: {'': {starting_state, final_state}},
                final_state: {'': set()}
            }
            
            return starting_state, final_state, states
        
        elif isinstance(node, QuestionMarkAstNode):
            # (a|epsilon)?
            # zero or one
            sub_start, sub_final, sub_states = self._construct_from_ast(node.left)
            starting_state = object()
            final_state = object()
            states = {
                starting_state: {'': {sub_start, final_state}},
                **sub_states,
                sub_final: {'': {final_state}},
                final_state: {'': set()}
                
            }
            return starting_state, final_state, states

        elif isinstance(node, SeqAstNode):
            # a.b

            left_start, left_final, left_states = self._construct_from_ast(node.left)
            right_start, right_final, right_states = self._construct_from_ast(node.right)
            states = {**left_states, **right_states, left_final: {'': {right_start}}}
            starting_state = left_start
            final_state = right_final
            return starting_state, final_state, states

        elif isinstance(node, OrAstNode):
            # a|b
            left_start, left_final, left_states = self._construct_from_ast(node.left)
            right_start, right_final, right_states = self._construct_from_ast(node.right)
            starting_state = object()
            final_state = object()
            states = {
                starting_state: {'': {left_start, right_start}},
                **left_states,
                **right_states,
                left_final: {'': {final_state}},
                right_final: {'': {final_state}},
                final_state: {'': set()},
                final_state: {'': set()}
            }
            return starting_state, final_state, states
        
        elif isinstance(node, StarAstNode):
            # (a|epsilon)*
            # zero or more
            sub_start, sub_final, sub_states = self._construct_from_ast(node.left)
            starting_state = object()
            final_state = object()
            states = {
                starting_state: {'': {sub_start, final_state}},
                **sub_states,
                sub_final: {'': {starting_state, final_state}},
                final_state: {'': set()}
            }
            return starting_state, final_state, states
        
        elif isinstance(node, SquareBracketAstNode):
            starting_state = object()
            final_state = object()
            states = {
                starting_state: {char: {final_state} for char in node.clas},
                final_state: {'': set()}
            }
            return starting_state, final_state, states

# ============================================================================
# Visualization and Utilities
# ============================================================================

import graphviz
from IPython.display import SVG, display
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

def draw_nfa(nfa):
    dot = graphviz.Digraph(comment='NFA')
    dot.attr(rankdir='LR')  # Set graph direction to left-to-right

    # add invisible starting state
    dot.node('startingStateH', 'startingStateH',style='invis')
    # add nodes
    for key in nfa.keys():
        if key == 'startingState':
            continue
        if nfa[key]['isTerminatingState']:
            dot.node(key, key, shape='doublecircle')
        else:
            dot.node(key, key)
    # add edges
    for key in nfa.keys():
        if key == 'startingState':
            continue
        for symbol in nfa[key].keys():
            if symbol == 'isTerminatingState':
                continue
            for next_state in nfa[key][symbol]:
                sy = symbol
                if symbol == 'epsilon':
                    sy = 'ε'
                # Escape special characters for graphviz
                sy = sy.replace('\\', '\\\\').replace('"', '\\"').replace('{', '\\{').replace('}', '\\}')
                dot.edge(key, next_state, label=sy)
    dot.edge('startingStateH',nfa['startingState'])

    return dot

def draw_dfa(dfa):
    dot = graphviz.Digraph(comment='DFA')
    dot.attr(rankdir='LR')  # Set graph direction to left-to-right

    # add invisible starting state
    dot.node('startingStateH', 'startingStateH',style='invis')
    # add nodes
    for key in dfa.keys():
        if key == 'startingState':
            continue
        if dfa[key]['isTerminatingState']:
            dot.node(key, key, shape='doublecircle')
        else:
            dot.node(key, key)
    # add edges
    for key in dfa.keys():
        if key == 'startingState':
            continue
        for symbol in dfa[key].keys():
            if symbol == 'isTerminatingState':
                continue
            next_state= dfa[key][symbol]
            # Escape special characters for graphviz
            label = symbol.replace('\\', '\\\\').replace('"', '\\"').replace('{', '\\{').replace('}', '\\}')
            dot.edge(key, next_state, label=label)
    dot.edge('startingStateH',dfa['startingState'])

    return dot

def save_json(nfa, filename):
    import json 
    # Serializing json  
    json_object = json.dumps(nfa, indent = 4) 
    # save to file
    with open(filename, "w") as outfile:
        outfile.write(json_object)

def display_and_save_image(nfa,fileName):
    if fileName == 'nfa_graph':
        dot = draw_nfa(nfa)
    else:
        dot=draw_dfa(nfa)
    dot.format = 'png'
    dot.render(fileName)
    #svg = SVG(data=dot.pipe())._repr_svg_()
    # display nfa_graph.png
    
    img=mpimg.imread(fileName+'.png')
    imgplot = plt.imshow(img)
    plt.axis('off')
    plt.figure(figsize=(15, 15))
    plt.show()

def draw_token_dfa(token_dfa_dict, live_states=None):
    """
    Draw token-level DFA with colored states.
    - Live states: blue
    - Accept (final) states: red (with double circle)
    - Other states: default (black)
    """
    dot = graphviz.Digraph(comment='Token-Level DFA')
    dot.attr(rankdir='LR')  # Set graph direction to left-to-right
    
    # Add invisible starting state
    dot.node('startingStateH', 'startingStateH', style='invis')
    
    if live_states is None:
        live_states = set()
    else:
        live_states = set(live_states)
    
    # Add nodes with colors
    for key in token_dfa_dict.keys():
        if key in ['startingState', 'vocabulary']:
            continue
        
        state_info = token_dfa_dict[key]
        if not isinstance(state_info, dict):
            continue
            
        is_final = state_info.get('isTerminatingState', False)
        is_live = key in live_states
        
        # Determine node style
        if is_final:
            # Final states: red with double circle
            dot.node(key, key, shape='doublecircle', color='red', fontcolor='red', penwidth='2.0')
        elif is_live:
            # Live states: blue
            dot.node(key, key, color='blue', fontcolor='blue', penwidth='2.0')
        else:
            # Other states: default
            dot.node(key, key)
    
    # Add edges
    for key in token_dfa_dict.keys():
        if key in ['startingState', 'vocabulary']:
            continue
        
        state_info = token_dfa_dict[key]
        if not isinstance(state_info, dict):
            continue
            
        for symbol, next_state in state_info.items():
            if symbol == 'isTerminatingState':
                continue
            
            # Handle [MASK] transitions (next_state is a list)
            if symbol == '[MASK]':
                if isinstance(next_state, list):
                    for mask_next in next_state:
                        # Draw MASK edges with dashed style and gray color
                        dot.edge(key, mask_next, label='[MASK]', style='dashed', color='gray', fontcolor='gray')
            else:
                # Regular transitions
                # Escape special characters for graphviz
                label = str(symbol).replace('\\', '\\\\').replace('"', '\\"').replace('{', '\\{').replace('}', '\\}')
                dot.edge(key, next_state, label=label)
    
    dot.edge('startingStateH', token_dfa_dict['startingState'])
    
    return dot

def display_and_save_token_image(token_dfa_dict, fileName, live_states=None):
    """
    Display and save token-level DFA image with colored states.
    """
    dot = draw_token_dfa(token_dfa_dict, live_states)
    dot.format = 'png'
    dot.render(fileName)
    
    img = mpimg.imread(fileName + '.png')
    imgplot = plt.imshow(img)
    plt.axis('off')
    plt.figure(figsize=(15, 15))
    plt.show()

import re
def is_valid_regex(regex):
    try:
        re.compile(regex)
        return True
    except re.error:
        return False

# ============================================================================
# NFA to DFA
# ============================================================================

class DFA:
    def __init__(self, alphabet, states, start_state, accept_states, transition_function):
        self.alphabet = alphabet
        self.states = states
        self.start_state = start_state
        self.accept_states = accept_states    
        self.transition_function = transition_function
        self.ma = {}
        self.num = 0
    def run(self, input_string):
        current_state = self.start_state
        for symbol in input_string:
            current_state = self.transition_function[current_state][symbol]
        return current_state in self.accept_states
    def get_state_number(self,state):
        if self.ma.get(state) == None:
            self.ma[state] = self.num
            self.num += 1
        return str(self.ma[state])
    def to_dict(self):
        dfa_dict = {}
        dfa_dict['startingState'] = self.get_state_number(self.start_state)
        for state in self.states:
            if state == 'frozenset()':
                continue
            dfa_dict[self.get_state_number(state)] = {
                "isTerminatingState": state in self.accept_states
            }
            for symbol in self.alphabet:
                if symbol == 'isTerminatingState':
                    continue
                if self.transition_function[state][symbol]!="frozenset()": 
                    dfa_dict[self.get_state_number(state)][symbol] = self.get_state_number(self.transition_function[state][symbol])
        return dfa_dict

class NFAtoDFAConverter:
    def __init__(self, nfa):
        self.nfa = nfa
        self.dfa = self.convert()

    def epsilon_closure(self, states):
        closure = set(states)
        queue = list(states)
        while queue:
            state = queue.pop()
            if state in self.nfa:
                for next_state in self.nfa[state].get("epsilon", []):
                    if next_state not in closure:
                        closure.add(next_state)
                        queue.append(next_state)
        return frozenset(closure)

    def move(self, states, symbol):
        move_states = set()
        for state in states:
            if state in self.nfa:
                # handle if isTerminatingState
                if symbol == 'isTerminatingState':
                    continue
                for next_state in self.nfa[state].get(symbol, []):
                    move_states.add(next_state)
        return frozenset(move_states)

    def convert(self):
        alphabet = set(symbol for state in self.nfa.values() for symbol in state if symbol != "epsilon")
        alphabet.discard("isTerminatingState")
        alphabet.discard(self.nfa["startingState"])
        start_state = self.epsilon_closure([self.nfa["startingState"]])
        dfa_states = [start_state]
        dfa_accept_states = []
        dfa_transition_function = {}
        queue = [start_state]

        while queue:
            current_state = queue.pop(0)
            for symbol in alphabet:
                move_states = self.move(current_state, symbol)
                closure_states = self.epsilon_closure(move_states)

                if closure_states not in dfa_states:
                    dfa_states.append(closure_states)
                    queue.append(closure_states)

                dfa_transition_function.setdefault(current_state, {})
                dfa_transition_function[current_state][symbol] = closure_states

            if any(state in self.nfa and self.nfa[state]["isTerminatingState"] for state in current_state):
                dfa_accept_states.append(current_state)

        # remove empty fozenset from dfa_transition_function
        #dfa_transition_function.pop(frozenset(), None)
        dfa_states = [str(state) for state in dfa_states]
        start_state = str(start_state)
        dfa_accept_states = [str(state) for state in dfa_accept_states]
        dfa_transition_function = {str(k): {symbol: str(v) for symbol, v in transitions.items()} for k, transitions in dfa_transition_function.items()}

        return DFA(alphabet, dfa_states, start_state, dfa_accept_states, dfa_transition_function)

# ============================================================================
# Token-Level DFA Conversion
# ============================================================================

class TokenLevelDFA:
    """
    Convert character-level DFA to token-level DFA.
    A token can span across multiple characters.
    """
    def __init__(self, char_dfa, vocabulary):
        """
        Args:
            char_dfa: Character-level DFA dictionary
            vocabulary: Set of tokens (vocabulary), each token can be multi-character
        """
        self.char_dfa = char_dfa
        self.vocabulary = vocabulary  # V \ {⊥}
        self.token_dfa = None
        self.mask_transition = {}  # δ⊥: Q → 2^Q
        
    def build_token_level_dfa(self):
        r"""
        Construct token-level DFA D_t = (Q, (V \ bottom), delta_t, q_0, F)
        """
        Q = set()  # States from character-level DFA
        q_0 = self.char_dfa['startingState']  # Starting state
        F = set()  # Final states
        
        # Collect all states and final states
        for state, transitions in self.char_dfa.items():
            if state == 'startingState':
                continue
            Q.add(state)
            if transitions.get('isTerminatingState', False):
                F.add(state)
        
        # Build token-level transition function δ_t
        delta_t = {}  # δ_t: Q × (V \ ⊥) → Q
        
        for q in Q:
            delta_t[q] = {}
            for token in self.vocabulary:
                # Execute character-level DFA on the token's characters
                resulting_state = self._execute_on_token(q, token)
                if resulting_state is not None:
                    delta_t[q][token] = resulting_state
        
        # Build mask transition function δ⊥: Q → 2^Q
        self._build_mask_transition(Q, delta_t)
        
        self.token_dfa = {
            'startingState': q_0,
            'states': Q,
            'finalStates': F,
            'transitions': delta_t,
            'maskTransitions': self.mask_transition
        }
        
        return self.token_dfa
    
    def _execute_on_token(self, start_state, token):
        """
        Execute character-level DFA on a sequence of characters (token).
        Returns the resulting state after processing all characters in the token.
        """
        current_state = start_state
        
        for char in token:
            # Check if transition exists
            if current_state in self.char_dfa:
                transitions = self.char_dfa[current_state]
                if char in transitions and transitions[char] is not None:
                    current_state = transitions[char]
                else:
                    # No valid transition for this character
                    return None
            else:
                return None
        
        return current_state
    
    def _build_mask_transition(self, Q, delta_t):
        r"""
        Build delta_bottom(q) which returns the set of states reachable via a single token transition.
        delta_bottom(q) = {q' | q' = delta_t(q, t); t in (V \ bottom)}
        """
        for q in Q:
            reachable_states = set()
            if q in delta_t:
                for token, next_state in delta_t[q].items():
                    if next_state is not None:
                        reachable_states.add(next_state)
            self.mask_transition[q] = reachable_states
    
    def get_combined_transition(self, q, t):
        r"""
        Combined transition function delta_tilde: Q × V → 2^Q
        
        delta_tilde(q, t) = {{delta_t(q, t)}  if t in (V \ bottom),
                            {delta_bottom(q)   if t = bottom.
        """
        if t == '⊥' or t == '[MASK]':  # Special mask token
            return self.mask_transition.get(q, set())
        else:
            # Regular token
            if q in self.token_dfa['transitions']:
                next_state = self.token_dfa['transitions'][q].get(t)
                if next_state is not None:
                    return {next_state}
            return set()
    
    def to_dict(self):
        """Convert token-level DFA to dictionary format"""
        if self.token_dfa is None:
            self.build_token_level_dfa()
        
        result = {
            'startingState': self.token_dfa['startingState'],
            'vocabulary': list(self.vocabulary)
        }
        
        for state in self.token_dfa['states']:
            result[state] = {
                'isTerminatingState': state in self.token_dfa['finalStates']
            }
            
            # Add token transitions
            if state in self.token_dfa['transitions']:
                for token, next_state in self.token_dfa['transitions'][state].items():
                    result[state][token] = next_state
            
            # Add mask transitions
            if state in self.mask_transition:
                result[state]['[MASK]'] = list(self.mask_transition[state])
        
        return result


def get_live_states(token_dfa, states):
    """
    Get the set of live states Q_l ⊆ Q.
    A state is live if it can reach a final state.
    """
    final_states = token_dfa['finalStates']
    live_states = set(final_states)
    
    # Backwards reachability from final states
    changed = True
    while changed:
        changed = False
        for state in states:
            if state in live_states:
                continue
            
            # Check if this state can reach any live state
            if state in token_dfa['transitions']:
                for token, next_state in token_dfa['transitions'][state].items():
                    if next_state in live_states:
                        live_states.add(state)
                        changed = True
                        break
    
    return live_states


# ============================================================================
# Main Functions
# ============================================================================

def req2(regex):
    print('Req 2 : NFA to minimized DFA')
    regexlexer = regexLexer(regex)
    tokenStream = regexlexer.lexer()
    print('AST for regex: ', regex)
    parseRegex = ParseRegex(tokenStream)
    ## handle Exception
    throwException = False
    try:
        AST = parseRegex.parse()
    except Exception as e:
        print(e)
        throwException = True
    if throwException:
        print('Invalid regex')

    print_ast(AST)
    nfa = ThompsonConstruction(AST).construct().to_dict()
    converter = NFAtoDFAConverter(nfa)
    dfa = converter.convert().to_dict()
    save_json(dfa, "dfa.json")
    print('DFA for regex: ', regex)
    display_and_save_image(dfa,"dfa_graph")


def convert_to_token_level(regex, vocabulary):
    """
    Convert a regex to character-level DFA, then to token-level DFA.
    
    Args:
        regex: Regular expression string
        vocabulary: List of tokens (e.g., ["age", "name", ":", "{", "}"])
    """
    print('\n' + '='*60)
    print('Converting to Token-Level DFA')
    print('='*60)
    
    # Step 1: Build character-level DFA
    print('\n1. Building character-level DFA from regex...')
    regexlexer = regexLexer(regex)
    tokenStream = regexlexer.lexer()
    parseRegex = ParseRegex(tokenStream)
    
    try:
        AST = parseRegex.parse()
    except Exception as e:
        print(f"Error parsing regex: {e}")
        return None
    
    nfa = ThompsonConstruction(AST).construct().to_dict()
    converter = NFAtoDFAConverter(nfa)
    char_dfa = converter.convert().to_dict()
    
    print(f"   Character-level DFA has {len([k for k in char_dfa.keys() if k != 'startingState'])} states")
    
    # Step 2: Build token-level DFA
    print('\n2. Building token-level DFA...')
    print(f'   Vocabulary: {vocabulary}')
    
    token_converter = TokenLevelDFA(char_dfa, set(vocabulary))
    token_dfa = token_converter.build_token_level_dfa()
    
    print(f'   Token-level DFA has {len(token_dfa["states"])} states')
    print(f'   Final states: {token_dfa["finalStates"]}')
    
    # Step 3: Get live states
    live_states = get_live_states(token_dfa, token_dfa['states'])
    print(f'   Live states: {live_states}')
    
    # Step 4: Save token-level DFA
    token_dfa_dict = token_converter.to_dict()
    save_json(token_dfa_dict, "token_dfa.json")
    print('\n3. Token-level DFA saved to token_dfa.json')
    
    # Step 5: Visualize token-level DFA
    print('\n4. Visualizing token-level DFA...')
    display_and_save_token_image(token_dfa_dict, "token_dfa_graph", live_states)
    print('   Token-level DFA graph saved to token_dfa_graph.png')
    
    # Print some example transitions
    print('\n5. Example token transitions:')
    for state in list(token_dfa['states'])[:3]:  # Show first 3 states
        if state in token_dfa['transitions']:
            print(f'   State {state}:')
            for token, next_state in list(token_dfa['transitions'][state].items())[:5]:
                print(f'      "{token}" → {next_state}')
            if state in token_converter.mask_transition:
                mask_states = token_converter.mask_transition[state]
                if mask_states:
                    print(f'      [MASK] → {mask_states}')
    
    return token_dfa_dict

# ============================================================================
# Run
# ============================================================================

if __name__ == "__main__":
    # Example 1: Character-level DFA
    # regex = r'{"age":(0|[1-9][0-9]?|100)}'
    # if not is_valid_regex(regex):
    #     print('invalid regex compilation failed')
    # else:
    #     req2(regex)
    
    # Example 2: Token-level DFA
    regex = r'{"age":(0|[1-9][0-9]?|100)}'
    
    # Define vocabulary (tokens)
    vocabulary = [
        '{', '}', '"', ':', ',',  # Structural tokens
        'age', 'name', 'email',    # Field names
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',  # Digits
    ]
    
    print("Testing Token-Level DFA Conversion")
    print("="*60)
    print(f"Regex: {regex}")
    
    if not is_valid_regex(regex):
        print('Invalid regex compilation failed')
    else:
        token_dfa = convert_to_token_level(regex, vocabulary)
        
        if token_dfa:
            print('\n' + '='*60)
            print('Token-Level DFA conversion completed successfully!')
            print('='*60)
