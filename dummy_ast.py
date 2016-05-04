class Program():
    def __init__(self, main_entry, nv_vars, functions):
        self.main_entry = main_entry
        self.nv_vars = nv_vars
        self.functions = functions

entry_type = "Entry"
branch_free_type = "Branch Free"
if_type = "If"
boundary_type = "Task Boundary"
loop_type = "Loop"
func_call_type = "Func Call"

control_color = "#F5F5F5"
#Function entry.
#the name of the function
#the first node of the function
#the function body
#the number of parameters to the function.
def list_deep_copy(to_copy):
    return [n.deep_copy() for n in to_copy]

def pretty_print_list(lst, depth):
    out_str = ""
    for node in lst:       
        out_str = out_str + node.pretty_print(depth)
    return out_str

def make_indent(depth):
    return "  " * depth

class EntryNode():
    def __init__(self, name, body, n_params, color = "#FF0000"):
        self.func_name = name
        self.body = body
        self.n_params = n_params
        self.color = color 

    def node_type(self):
        return entry_type

    def deep_copy(self):
        return EntryNode(self.func_name, list_deep_copy(self.body), self.n_params, color = self.color)

    def pretty_print(self, depth):
        out_str = self.func_name + "(" + str(self.n_params) + "args ){\n"
        out_str += pretty_print_list(self.body, depth + 1)
        out_str += "}"
        return out_str


#represents a non-branching sequence of instructions
class branch_free_code():
    def __init__(self, n_instrs, success_prob, color = "#FF0000"):
        self.n_instrs = n_instrs
        self.success_prob = success_prob
        self.live_vars = 0
        self.color = color

    def node_type(self):
        return branch_free_type

    def deep_copy(self):
        new_node = branch_free_code(self.n_instrs, self.success_prob, color = self.color)
        new_node.live_vars = self.live_vars
        return new_node

    def pretty_print(self, depth):
        return make_indent(depth) + "code: " + str(self.n_instrs) + " instrs, p: " + str(self.success_prob) + "\n"


#TODO: make else optional.
#cond is a list of branch_free_code and calls.
#true_branch is a list of nodes
#false_branch is a list of nodes
class if_node():
    def __init__(self, cond, true_branch, false_branch, color = "#FF0000"):
        self.cond = cond
        self.true_branch = true_branch
        self.false_branch = false_branch
        self.live_vars = 0
        self.color = color

    def node_type(self):
        return if_type

    def deep_copy(self):
        new_cond = list_deep_copy(self.cond)
        new_true = list_deep_copy(self.true_branch)
        new_false = list_deep_copy(self.false_branch)
        new_node = if_node(new_cond, new_true, new_false, color = self.color)
        new_node.live_vars = self.live_vars
        return new_node

    def pretty_print(self, depth):
        out_str = make_indent(depth) + "if{\n"
        out_str += pretty_print_list(self.cond, depth + 1)
        out_str += make_indent(depth) + "}then{\n"
        out_str += pretty_print_list(self.true_branch, depth + 1)
        out_str += make_indent(depth) + "}else{\n"
        out_str += pretty_print_list(self.false_branch, depth + 1)
        out_str += make_indent(depth) + "}\n"
        return out_str

#represents a task boundary
class boundary_node():
    def __init__(self, id_info, color = "#00FF00"):
        self.id_info = id_info
        self.live_vars = 0
        self.color = color
        
    def node_type(self):
        return boundary_type

    def deep_copy(self):
        new_node = boundary_node(self.id_info, color = self.color)
        new_node.live_vars = self.live_vars
        return new_node

    def pretty_print(self, depth):
        return make_indent(depth) + "BOUNDARY\n"
    
#represents a loop
#cond is a list of branch_free_code and calls
#body is a list of nodes
class loop_node():
    def __init__(self, cond, body, iter_count, color = "#FF0000"):
        self.cond = cond
        self.body = body
        self.iter_count = iter_count
        self.live_vars = 0
        #TODO: set this
        self.final_node = None #Points forward to last node in body. Set in CFG construction
        self.color = color

    def node_type(self):
        return loop_type

    def deep_copy(self):
        new_cond = list_deep_copy(self.cond)
        new_body = list_deep_copy(self.body)
        new_node = loop_node(new_cond, new_body, self.iter_count, color = self.color)
        new_node.live_vars = self.live_vars
        return new_node

    def pretty_print(self, depth):
        out_str = make_indent(depth) + "while{\n"
        out_str += pretty_print_list(self.cond, depth + 1)
        out_str += make_indent(depth) + "}do{\n"
        out_str += pretty_print_list(self.body, depth + 1)
        out_str += make_indent(depth) + "}\n"
        return out_str

class func_call():
    def __init__(self, func_name, color = "#FF0000"):
        self.func_name = func_name
        self.live_vars = 0
        self.color = color

    def node_type(self):
        return func_call_type

    def deep_copy(self):
        new_node = func_call(self.func_name, color = self.color)
        new_node.live_vars = self.live_vars
        return new_node

    def pretty_print(self, depth):
        return make_indent(depth) + "call: " + self.func_name + "\n"
