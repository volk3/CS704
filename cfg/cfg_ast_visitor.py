import sys, os

thisdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,  os.path.join(thisdir, 'pycparser'))
#sys.path.insert(0,  os.path.join(thisdir, 'networkx-1.11'))

from pycparser import c_parser, c_ast
import networkx as nx
#import matplotlib.pyplot as plt

from cfg_nodes import CFGNodeType
from cfg_nodes import CFGEntryNode
from cfg_nodes import CFGNode

#CHANGED.  Added compound and visit as parameters for all visit functions.
class CFGAstVisitor(object):
    """ CFG is made of a list of entry nodes that represents
        all functions defined in the source code. Each entry
        node has the function name and its start node. Given
        the start node, everyone can be achieved.

        All visit functions must always return an CFGNode.
        However, when a function definitions is being visited,
        an CFGEntryNode should be returned.

        PS1: It is helpful to look to pycparser/_c_ast.cfg at
        the same time, because of nodes structures.

        PS2: This code was strictly based on pycparser/c_ast.py.
        This class is not a subclass of c_ast.NodeVisitor,
        because generic_visit() should have some changes.
    """

    def __init__(self):
        self._entry_nodes = []
        self._init_vars()
	self._DG = nx.DiGraph()

    def _init_vars(self):
        self._current_func_name = None
        self._current_node = None
        self._create_new_node = False
        self._is_first_node = True

    def _add_entry_node(self, entry_node):
        self._entry_nodes.append(entry_node)

    def _get_entry_nodes(self):
        return self._entry_nodes

    def make_cfg_from_ast(self, ast):
        if isinstance(ast, c_ast.FileAST):
            self.visit(ast)
            self._update_call()
            self._clean_graph()

	#nx.draw(self._DG)
	#print(self._DG.nodes())
	#print(self._DG.edges())
        return self._get_entry_nodes()

    def get_DG(self):
        return self._DG

    ####### AST visit algorithm #######

    def visit(self, n, compound = None, index = 0):
        """ Visit a node.
        """
        method = 'visit_' + n.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(n, compound, index)

    def visit_FileAST(self, n, compound = None, index = 0):
        """ Visit only function definitions
        """
        for ext in n.ext:
            if isinstance(ext, c_ast.FuncDef):
                self._init_vars()
                self.visit(ext, compound, index)
                self._add_last_node()

    def visit_FuncDef(self, n, compound = None, index = 0):
        """ Get function name and explore its statements
        """
        if isinstance(n.decl, c_ast.Decl):
            self._current_func_name = n.decl.name
        self.visit(n.body, compound, index)

    def visit_Compound(self, n, compound = None, index = 0):
        """ A new block was found and must be created a node for it
        """
        self._create_new_node = True
#CHANGED.  Each element is now visited with info about its place in the compound.
        #for stmt in n.block_items:
        #    self.visit(stmt)
	for i in range(len(n.block_items)):
             self.visit(n.block_items[i], n, i)
    def visit_If(self, n, compound = None, index = 0):
        if n.cond is None: return

        cond_node = CFGNode(CFGNodeType.IF)
        cond_node.set_func_owner(self._current_func_name)
        cond_node.add_ast_elem(n.cond, compound, index)
        self._add_new_node(cond_node)
        self._current_node = cond_node
        self._create_new_node = False
        self.visit(n.cond, compound, index) # a function call can be presented in condition

        # then
        self._current_node = cond_node
        self._create_new_node = True
        iftrue_last_node = None
        if n.iftrue is not None:
            self.visit(n.iftrue, compound, index)
            iftrue_last_node = self._current_node

        # else
        self._current_node = cond_node
        self._create_new_node = True
        iffalse_last_node = None
        if n.iffalse is not None:
            self.visit(n.iffalse, compound, index)
            iffalse_last_node = self._current_node

        # add end node
        end_node = CFGNode(CFGNodeType.END_IF)
        end_node.set_func_owner(self._current_func_name)
        self._add_child_case_if(cond_node, iftrue_last_node,
                iffalse_last_node, end_node)

        self._current_node = end_node
        self._create_new_node = True

    def visit_FuncCall(self, n, compound = None, index = 0):
        call_node = CFGNode(CFGNodeType.CALL)
        call_node.set_func_owner(self._current_func_name)
        if isinstance(n.name, c_ast.ID):
            call_node.set_call_func_name(n.name.name)
        else:
            call_node.set_call_func_name(None)
        call_node.add_ast_elem(n, compound, index)
        self._add_new_node(call_node)
        self._current_node = call_node
        self._create_new_node = True

    def visit_While(self, n, compound = None, index = 0):
        if n.cond is None: return

        pseudo = CFGNode(CFGNodeType.PSEUDO)
        pseudo.set_func_owner(self._current_func_name)
        pseudo.add_ast_elem(n.cond, compound, index)
        self._add_new_node(pseudo)

        # while-cond
        cond = CFGNode(CFGNodeType.WHILE)
        cond.set_func_owner(self._current_func_name)
        self._current_node = cond
        self._create_new_node = False
        self.visit(n.cond, compound, index) # a function call can be presented in condition

        # while-stmt
        self._current_node = cond
        self._create_new_node = True
        if n.stmt is not None: self.visit(n.stmt, compound, index)

        # get all stmt nodes without child and point them to while-cond
        self._make_loop_cycle(cond, cond, {})

        # pseudo:   reference -> while-cond
        #           child -> other CFG nodes
        pseudo.set_refnode(cond)
        self._current_node = pseudo
        self._create_new_node = True

    def generic_visit(self, n, compound = None, index = 0):
        """ Called if no explicit visitor function exists for a
            node. Implements preorder visiting of the node.
        """
        self._add_ast_elem(n, compound, index)
        for c_name, c in n.children():
            self.visit(c, compound, index)

    def _add_ast_elem(self, ast_elem, compound = None, index = 0):
        if self._create_new_node:
            new_node = CFGNode(CFGNodeType.COMMON)
            new_node.set_func_owner(self._current_func_name)
            self._add_new_node(new_node)
            self._current_node = new_node
            self._create_new_node = False

        # an AST element should be added
        # only when there is a valid node
        if isinstance(self._current_node, CFGNode):
            self._current_node.add_ast_elem(ast_elem, compound, index)

    def _add_new_node(self, new):
        # there is a previous node being updated
	
        if isinstance(self._current_node, CFGNode):
	    self._DG.add_node(self._current_node)
            self._DG.add_node(new)
	    self._DG.add_edge(self._current_node, new)
            self._current_node.add_child(new)

        if self._is_first_node:
            entry_node = CFGEntryNode(self._current_func_name, new)
	    #self._DG.add_node(entry_node)
            self._add_entry_node(entry_node)
            self._is_first_node = False

    def _add_child_case_if(self, cond_node, iftrue_last_node,
            iffalse_last_node, end_node):

        children = cond_node.get_children()

        # if-then or if-then-else stmt:
        #    last then node -> end if node
        if isinstance(iftrue_last_node, CFGNode):
            self._DG.add_node(iftrue_last_node)
	    self._DG.add_node(end_node)
            self._DG.add_edge(iftrue_last_node, end_node)
            iftrue_last_node.add_child(end_node)
	    
        # if-then stmt:
        #   if cond -> end if node
        if len(children) == 1:
            self._DG.add_node(cond_node)
            self._DG.add_node(end_node)
            self._DG.add_edge(cond_node, end_node)
            cond_node.add_child(end_node)

        # if-then-else stmt:
        #   last else node -> end if node
        elif len(children) == 2 and isinstance(iffalse_last_node, CFGNode):
            self._DG.add_node(iffalse_last_node)
	    self._DG.add_node(end_node)
            self._DG.add_edge(iffalse_last_node, end_node)
            iffalse_last_node.add_child(end_node)

    def _make_loop_cycle(self, cond, child, visited):
        visited[child] = True
        if child.get_children() == []:
	    self._DG.add_node(child)
	    self._DG.add_node(cond)
            self._DG.add_edge(child, cond)
            child.add_child(cond)
        else:
            for c in child.get_children():
                if c not in visited:
                    self._make_loop_cycle(cond, c, visited)

    def _update_call(self):
        """ Explore all functions graphs to find CALL nodes and set its
            reference node to the function that is being called.
        """
        for entry in self._entry_nodes:
            self._update_call_visit(entry.get_func_first_node(), {})

    def _update_call_visit(self, n, visited):
        """ Explore graph to find CALL nodes to set its reference node.

            n:
                CFGNode

            visited:
                Dictionary which keeps all nodes that were already visited
        """
        visited[n] = True

        if n.get_type() == CFGNodeType.PSEUDO:
            self._update_call_visit(n.get_refnode(), visited)

        elif n.get_type() == CFGNodeType.CALL:
            # update reference node to the right entry node
            for entry in self._entry_nodes:
                if n.get_call_func_name() == entry.get_func_name():
		    #MIGHT NEED IF THERE ARE FUNCTION 
		    #self._DG.add_node(n)
	    	    #self._DG.add_node(entry)
                    #self._DG.add_edge(n, entry)
                    n.set_refnode(entry)
                    break

        for child in n.get_children():
            if child not in visited:
                self._update_call_visit(child, visited)

    def _clean_graph(self):
        """ Search for unnecessary nodes and remove them.
        """
        for entry_node in self._entry_nodes:
            self._clean_graph_visit(entry_node.get_func_first_node(), {})

    def _clean_graph_visit(self, node, visited):
        """ Remove only END_IF nodes from the graph

            node:
                CFGNode

            visited:
                Dictionary of which nodes have already been visited
        """
        visited[node] = True

        while True:
            rp_node = None
            rp_id = -1
            for n_id, n in enumerate(node.get_children()):
                if n.get_type() == CFGNodeType.END_IF:
                    rp_node = n
                    rp_id = n_id
                    break

            # end node points to only one child,
            # so replace it
            if rp_node is not None and rp_node.get_children() != []:
                node.get_children()[rp_id] = rp_node.get_children()[0]

            # END-IF can be replaced by another, so continue until there's none
            if rp_node == None:
                break

        if node.get_type() == CFGNodeType.PSEUDO:
            self._clean_graph_visit(node.get_refnode(), visited)

        for child in node.get_children():
            if child not in visited:
                self._clean_graph_visit(child, visited)

    def _add_last_node(self):
        """ Add last node to the function graph.
        """
        for entry in self._entry_nodes:
            last_node = CFGNode(CFGNodeType.END)
            self._DG.add_node(last_node)
            last_node.set_func_owner(entry.get_func_name())
            self._add_last_node_visit(entry.get_func_first_node(), last_node, {})

    def _add_last_node_visit(self, n, last_node, visited):
        """ Search for each node (except reference node) that does not have
            children and add to it function last node. In this way, all
            functions will always have one start and one end points.

            n:
                CFGNode

            last_node:
                CFGNode

            visited:
                Dictionary of which nodes have already been visited
        """
        visited[n] = True

        for child in n.get_children():
            if child not in visited:
                self._add_last_node_visit(child, last_node, visited)

        if n.get_type() != CFGNodeType.END and n.get_children() == []:
            self._DG.add_node(n)
	    self._DG.add_node(last_node)
            self._DG.add_edge(n, last_node)
            n.add_child(last_node)
