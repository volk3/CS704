
import dummy_ast as ast
import networkx as nx
import matplotlib.pyplot as plt

global_prob = .99 #TODO: adjust this. Maybe make non-global
instrs_to_save_var = 5
instructions_key = "instrs"
probability_key = "prob"
nil_cost = {instructions_key : 0, probability_key : 0}
if_join_type = "If Join"
#Just to ensure that if nodes have a single exit point
class IfJoinNode():
    def __init__(self, color = "#FF0000"):
        self.color = color
    def node_type(self):
        return if_join_type

    def deep_copy(self):
        return IfJoinNode()

class SimpleProgramGraph():
    def __init__(self, program_ast):
        main_entry = None
        for fxn in program_ast.functions:
            if fxn.name == program_ast.main_entry_name:
                main_entry = fxn
        assert main_entry
        SimpleFunctionGraph(main_entry)
        self.function_map = dict([(f.name, SimpleFunctionGraph(f, main_entry.graph)) for f in program_ast.functions if f is not main_entry])
        self.entry_node = main_entry


class ExpandedProgramGraph():
    def __init__(self, SimpleProgramGraph):
        self.entry_node, self.terminal_node = ExpandedFunctionGraph(SimpleProgramGraph.entry_node, function_map)
        

def make_edge_costs_dummy(from_node, to_node, live_vars):
    return {instructions_key : 1, probability_key : 2}

def make_edge_costs(from_node, to_node, live_vars):
    cost_dict = None
    if from_node.node_type() == if_join_type:
        return {instructions_key: 0, probability_key: 0}
    if from_node.node_type() == ast.if_type:
        return {instructions_key: 0, probability_key: 0}
    if from_node.node_type() == ast.loop_type:
        return {instructions_key: 0, probability_key: 0}
    if from_node.node_type() == ast.branch_free_type:
        return {instructions_key: node.n_instrs, probability_key: n_instrs * global_prob}
    if from_node.node_type() == ast.boundary_type:
        num_instrs = instrs_to_save_var * live_vars
        return {instructions_key: num_instrs, num_instrs * global_prob}
    if from_node.node_type() == ast.func_call_type:
        assert(False) #This should not happen - func calls should be expanded.
    assert cost_dict
    return cost_dict
        
        

#TODO: remove this
test_indentation = 0
        
class SimpleFunctionGraph():
    def __init__(self, f_entry_node, graph = nx.DiGraph()):
        self.entry_node = f_entry_node
        self.graph = graph
        self.back_map = {} #map backwards from a node to a previous insertion point
        self.boundaries = [] #boundary nodes
        self.insertion_points = [] #places to insert boundaries
        #TODO: change how live_vars is handled.
        self.handle_node_list(f_entry_node.body, f_entry_node.n_params)
        #TODO: function_map setup
        self.function_map = {}

    #returns (start, end) nodes
    def handle_node_list(self, node_list, live_vars):
        list_start_node = None
        prev_end = None
        curr_start = None
        curr_end = None
        for node in node_list:
            #TODO remove this
            node.live_vars = live_vars
            if not list_start_node:
                list_start_node = node                
            if node.node_type() == ast.if_type:
                curr_start, curr_end = self.handle_if(node, live_vars)
            elif node.node_type() == ast.loop_type:
                curr_start, curr_end = self.handle_loop(node, live_vars)
            elif node.node_type() == ast.branch_free_type or  node.node_type() == ast.boundary_type or node.node_type() == ast.func_call_type:
                curr_start, curr_end = self.handle_linear(node, live_vars)
                
            if prev_end:
                self.add_edge_make_cost(prev_end, curr_start, live_vars)
            prev_end = curr_end
        return (list_start_node, curr_end)
    
    def handle_linear(self, node, live_vars):
        self.graph.add_node(node)
        return node, node

    def handle_branch_free(self, node, live_vars):
        self.graph.add_node(node)
        return node, node
    
    #generate loop gadget
    def handle_loop(self, loop_node, live_vars):
        return self.handle_loop_linear(loop_node, live_vars)            
            
    #returns (start, end) nodes
    def handle_loop_linear(self, loop_node, live_vars):
        head_start = loop_node
        self.graph.add_node(loop_node)        
        cond_start, cond_end = self.handle_node_list(loop_node.cond, live_vars)
        self.add_edge_with_cost(head_start, cond_start, nil_cost)
        body_start, body_end = self.handle_node_list(loop_node.body, live_vars)
        self.add_edge_make_cost(cond_end, body_start, live_vars)
        loop_node.final_node = body_end
        return (head_start, body_end)
                
    #returns (start, end) nodes
    #Generate an if gadget
    def handle_if(self, if_node, live_vars):
        #TODO - abstract into handle_loop_head?
        head_start = if_node
        self.graph.add_node(if_node)
        cond_start, cond_end = self.handle_node_list(if_node.cond, live_vars)
        self.add_edge_with_cost(head_start, cond_start, nil_cost)
        self.insertion_points.append(cond_start)
        true_start, true_end = self.handle_node_list(if_node.true_branch, live_vars)
        false_start, false_end = self.handle_node_list(if_node.false_branch, live_vars)
        self.add_edge_make_cost(cond_end, true_start, live_vars)
        self.add_edge_make_cost(cond_end, false_start, live_vars)
        exit_node = IfJoinNode()
        self.graph.add_node(exit_node)
        self.add_edge_make_cost(true_end, exit_node, live_vars)
        self.add_edge_make_cost(false_end, exit_node, live_vars)
        return if_node, exit_node
    

    def add_edge_with_cost(self, from_node, to_node, cost):
        self.graph.add_edge(from_node, to_node, cost)
        
    def add_edge_make_cost(self, from_node, to_node, live_vars):
        self.graph.add_edge(from_node, to_node, make_edge_costs_dummy(from_node, to_node, live_vars))

    def get_color_list(self):
        return [self.get_node_color(node) for node in self.graph]

    def get_node_color(self, node):
        return node.color

    def draw_and_display(self):
        nx.nx_pydot.write_dot(self.graph, self.entry_node.func_name + 'graph.dot')
        plt.title("Control Flow Graph")
        pos = nx.nx_pydot.graphviz_layout(self.graph, prog='dot')
        nx.draw(self.graph, pos, node_color = self.get_color_list())
        plt.show()
        
#Expand an AST for a non-recursive function into a full graph, with unrolled loops.
#TODO: pass live vars down
class ExpandedFunctionGraph():
    def __init__(self, f_entry_node, live_vars, function_map, graph = nx.DiGraph())
        self.entry_node = f_entry_node
        self.graph = graph #Lets us pass the graph downwards
        self.back_map = {} #map backwards from a node to a previous insertion point
        self.boundaries = [] #boundary nodes
        self.insertion_points = [] #places to insert boundaries
        #TODO: change how live_vars is handled.
        self.initial, self.terminal = self.handle_node_list(f_entry_node.body, f_entry_node.n_params, function_map, f_entry_node)

    #returns (start, end) nodes
    #TODO: pass down function map
    def handle_node_list(self, node_list, live_vars, function_map, parent_fxn):
        list_start_node = None
        prev_end = None
        curr_start = None
        curr_end = None
        for node in node_list:
            #TODO remove this
            node.live_vars = live_vars
            if not list_start_node:
                list_start_node = node                
            if node.node_type() == ast.if_type:
                #TODO: Parent fxn
                curr_start, curr_end = self.handle_if(node, live_vars, function_map, parent_fxn)
            elif node.node_type() == ast.loop_type:
                curr_start, curr_end = self.handle_loop(node, live_vars, function_map, parent_fxn)
            elif node.node_type() == ast.func_call_type:
                curr_start, curr_end = self.expand_function_call(node, live_vars, function_map, parent_fxn)
            elif node.node_type() == ast.boundary_type:
                curr_start, curr_end = self.handle_boundary(node, live_vars, parent_fxn)
            elif node.node_type() == ast.branch_free_type:
                curr_start, curr_end = self.handle_linear(node, live_vars, parent_fxn)                
            if prev_end:
                self.add_edge_make_cost(prev_end, curr_start, live_vars)
            prev_end = curr_end
        return (list_start_node, curr_end)
    
    def handle_linear(self, node, live_vars, parent_fxn):
        node.color = parent_fxn.color
        self.graph.add_node(node)
        return node, node

    def handle_boundary(self, node, live_vars, parent_fxn):
        #Keep boundaries green
        self.graph.add_node(node)
        return node, node
    
    #generate loop gadget
    def handle_loop(self, loop_node, live_vars, parent_fxn):
        return self.handle_loop_unroll(loop_node, live_vars, parent_fxn)

    def expand_function_call(self, func_call_node, live_vars, function_map, parent_fxn):
        #Discard parent_fxn - ExpandedFunctionGraph will pass it's node down.
        entry_node = self.function_map[func_call_node.name]
        func_copy = entry_node.deep_copy()
        #TODO: function prologue/epilogue costs
        new_live_var_count = live_vars + entry_node.n_params
        callee_graph = ExpandedFunctionGraph(func_copy, new_live_var_count, function_map, graph = self.graph)
        return callee_graph.initial, callee_graph.terminal

    def handle_loop_unroll(self, loop_node, live_vars, parent_fxn):
        unroll_start = None
        curr_start = None
        curr_end = None
        prev_end = None
        
        for i in range(0, loop_node.iter_count):
            loop_copy = loop_node.deep_copy()
            #TODO: parent_fxn
            curr_start, curr_end = self.handle_loop_linear(loop_copy, live_vars, parent_fxn)
            if not unroll_start:             
                unroll_start = curr_start
            if prev_end:
                self.add_edge_make_cost(prev_end, curr_start, live_vars)
            prev_end = curr_end
        return (unroll_start, curr_end)
            
    #returns (start, end) nodes
    def handle_loop_linear(self, loop_node, live_vars, parent_fxn):
        head_start = loop_node
        loop_node.color = parent_fxn.color
        self.graph.add_node(loop_node)        
        cond_start, cond_end = self.handle_node_list(loop_node.cond, live_vars, parent_fxn)
        self.add_edge_with_cost(head_start, cond_start, nil_cost)
        body_start, body_end = self.handle_node_list(loop_node.body, live_vars, parent_fxn)
        self.add_edge_make_cost(cond_end, body_start, live_vars)
        loop_node.final_node = body_end
        return (head_start, body_end)
                
    #returns (start, end) nodes
    #Generate an if gadget
    def handle_if(self, if_node, live_vars, parent_fxn):
        #TODO - abstract into handle_loop_head?
        head_start = if_node
        if_node.color = parent_fxn.color
        self.graph.add_node(if_node)
        cond_start, cond_end = self.handle_node_list(if_node.cond, live_vars, parent_fxn)
        self.add_edge_with_cost(head_start, cond_start, nil_cost)
        self.insertion_points.append(cond_start)
        true_start, true_end = self.handle_node_list(if_node.true_branch, live_vars, parent_fxn)
        false_start, false_end = self.handle_node_list(if_node.false_branch, live_vars, parent_fxn)
        self.add_edge_make_cost(cond_end, true_start, live_vars)
        self.add_edge_make_cost(cond_end, false_start, live_vars)
        exit_node = IfJoinNode()
        exit_node.color = parent_fxn.color
        self.graph.add_node(exit_node)
        self.add_edge_make_cost(true_end, exit_node, live_vars)
        self.add_edge_make_cost(false_end, exit_node, live_vars)
        return if_node, exit_node
    

    def add_edge_with_cost(self, from_node, to_node, cost):
        self.graph.add_edge(from_node, to_node, cost)
        
    def add_edge_make_cost(self, from_node, to_node, live_vars):
        self.graph.add_edge(from_node, to_node, make_edge_costs(from_node, to_node, live_vars))

    def get_color_list(self):
        return [self.get_node_color(node) for node in self.graph]

    def get_node_color(self, node):
        return node.color

    def draw_and_display(self):
        nx.nx_pydot.write_dot(self.graph, self.entry_node.func_name + 'graph.dot')
        plt.title("Control Flow Graph")
        pos = nx.nx_pydot.graphviz_layout(self.graph, prog='dot')
        nx.draw(self.graph, pos, node_color = self.get_color_list())
        plt.show()
        
