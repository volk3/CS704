#Builds a DAG version of CFG
import dummy_ast as ast
import networkx as nx

#Just to ensure that if nodes have a single exit point
class IfJoinNode():
    def node_type(self):
        return "If Join"

    def deep_copy(self):
        return IfJoinNode()

class ProgramGraph():
    def __init__(self, program_ast):        
        self.function_map = dict([(f.name, FunctionGraph(f)) for f in program_ast.functions])
        self.entry_node = function_map[program_ast.main_entry.name]


def make_edge_costs(from_node, to_node, live_vars):
    return (1,1)


        
class FunctionGraph():
    def __init__(self, f_entry_node, function_map):
        self.graph = nx.DiGraph()
        self.back_map = {} #map backwards from a node to a previous insertion point
        self.boundaries = [] #boundary nodes
        self.insertion_points = [] #places to insert boundaries
        self.function_map = function_map
                

    #returns (start, end) nodes
    def handle_node_list(self, node_list, live_vars):
        list_start_node = None
        prev_end = None
        curr_start = None
        curr_end = None
        for node in node_list:
            node.live_vars = live_vars
            if not list_start_node:
                list_start_node = node
                
            if node.node_type() == ast.if_type:
                curr_start, curr_end = self.handle_if(node, live_vars)
            elif node.node_type() == ast.loop_type:
                curr_start, curr_end = self.handle_loop(node, live_vars)
            elif node.node_type == ast.func_call_type:
                curr_start, curr_end = self.handle_function_call(node, live_vars)
            elif node.node_type == ast.branch_free_type or  node.node_type == ast.boundary_type:
                curr_start = node
                curr_end = node
                
                
            self.graph.add_node(curr_start)
            if prev_end:
                self.add_edge_make_cost(prev_end, curr_start, live_vars)
            prev_end = curr_end
        return (list_start_node, curr_end)

    def handle_loop(self, loop_node, live_vars):
        return self.handle_loop_unroll(loop_node, live_vars)

    def handle_function_call(self, func_call_node, live_vars):
        entry_node = self.function_map[func_call_node.name]
        func_copy = entry_node.deep_copy()
        #TODO: function prologue/epilogue costs
        new_live_var_count = live_vars + entry_node.n_params
        body_start, body_end = self.handle_node_list(func_copy.body, new_live_var_count)
        return body_start, body_end

    def handle_loop_unroll(self, loop_node, live_vars):
        unroll_start = None
        curr_start = None
        curr_end = None
        prev_end = None
        
        for i in range(0, loop_node.iter_count):
            loop_copy = loop_node.deep_copy()
            curr_start, curr_end = self.handle_loop_linear(loop_copy, live_vars)
            if not unroll_start:
                self.insertion_points.append(curr_start)
                unroll_start = curr_start
            if prev_end:
                self.add_edge_make_cost(prev_end, curr_start, live_vars)
            prev_end = curr_end
        return (unroll_start, curr_end)
            
            
    #returns (start, end) nodes
    def handle_loop_linear(self, loop_node, live_vars):
        cond_start, cond_end = self.handle_node_list(loop_node.cond, live_vars)
        
        body_start, body_end = self.handle_node_list(loop_node.body, live_vars)
        self.add_edge_make_cost(cond_end, body_start, live_vars)
        return (cond_start, body_end)
                
    #returns (start, end) nodes
    def handle_if(self, if_node, live_vars):
        cond_start, cond_end = self.handle_node_list(if_node.cond, live_vars)
        self.insertion_points.append(cond_start)
        true_start, true_end = self.handle_node_list(if_node.true_branch, live_vars)
        false_start, false_end = self.handle_node_list(if_node.false_branch, live_vars)
        self.add_edge_make_cost(cond_end, true_start, live_vars)
        self.add_edge_make_cost(cond_end, false_start, live_vars)
        exit_node = IfJoinNode()
        self.add_edge_make_cost(true_end, exit_node, live_vars)
        self.add_edge_make_cost(false_end, exit_node, live_vars)
        return cond_start, exit_node
    

    def add_edge_with_cost(self, from_node, to_node, cost):
        self.graph.add_edge(from_node, to_node, cost)
        
    def add_edge_make_cost(self, from_node, to_node, live_vars):
        self.graph.add_edge(from_node, to_node, make_edge_costs(from_node, to_node, live_vars))
