class Program():
    def __init__(self, main_entry, nv_vars, functions):
        self.main_entry = main_entry
        self.nv_vars = nv_vars
        self.functions = functions

entry_type = "Entry"
branch_free_type = "Branch Free"
if_type = "if"
boundary_type = "Task Boundary"
loop_type = "Loop"
func_call_type = "Func Call"
#Function entry.
#the name of the function
#the first node of the function
#the function body
#the number of parameters to the function.
def list_deep_copy(to_copy):
    return [n.deep_copy() for n in to_copy]

class EntryNode():
    def __init__(self, name, body, n_params):
        self.func_name = name
        self.body = body
        self.n_params = n_params

    def node_type(self):
        return "Entry"

    def deep_copy(self):
        return EntryNode(self.func_name, list_deep_copy(self.body), self.n_params)


#represents a non-branching sequence of instructions
class branch_free_code():
    def __init__(self, n_instrs, success_prob):
        self.n_instrs = n_instrs
        self.success_prob = success_prob
        self.live_vars = 0

    def node_type(self):
        return "Branch Free"

    def deep_copy(self):
        new_node = branch_free_code(self.n_instrs, self.success_prob)
        new_node.live_vars = self.live_vars
        return new_node


#cond is a list of branch_free_code and calls.
#true_branch is a list of nodes
#false_branch is a list of nodes
class if_node():
    def __init__(self, cond, true_branch, false_branch):
        self.cond = cond
        self.true_branch = true_branch
        self.false_branch = false_branch
        self.live_vars = 0

    def node_type(self):
        return "If"

    def deep_copy(self):
        new_cond = list_deep_copy(self.cond)
        new_true = list_deep_copy(self.true_branch)
        new_false = list_deep_copy(self.false_branch)
        new_node = if_node(new_cond, new_true, new_false)
        new_node.live_vars = self.live_vars
        return new_node
 

#represents a task boundary
class boundary_node():
    def __init__(self, id_info):
        self.id_info = id_info
        self.live_vars = 0
        
    def node_type(self):
        return "Task Boundary"

    def deep_copy(self):
        new_node = boundary_node(self.id_info)
        new_node.live_vars = self.live_vars
        return new_node
    
#represents a loop
#cond is a list of branch_free_code and calls
#body is a list of nodes
class loop_node():
    def __init__(self, cond, body, iter_count):
        self.cond = cond
        self.body = body
        self.iter_count = iter_count
        self.live_vars = 0

    def node_type(self):
        return "Loop"

    def deep_copy(self):
        new_cond = list_deep_copy(self.cond)
        new_body = list_deep_copy(self.body)
        new_node = loop_node(new_cond, new_body, self.iter_count)
        new_node.live_vars = self.live_vars
        return new_node


class func_call():
    def __init__(self, func_name):
        self.func_name = func_name
        self.live_vars = 0

    def node_type(self):
        return "Func Call"

    def deep_copy(self):
        new_node = func_call(self.func_name)
        new_node.live_vars = self.live_vars
        return new_node
