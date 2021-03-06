from dummy_ast import *
from dummy_cfg import *
import networkx as nx
import matplotlib.pyplot as plt
main = EntryNode("main", [branch_free_code(1,.9), branch_free_code(1,.9)], 2)
a_loop = loop_node([branch_free_code(1,.9)],[boundary_node(12), branch_free_code(1,.9)], 1)
an_if = if_node([branch_free_code(1,.9)],[branch_free_code(2,.9)],[branch_free_code(3,.9),  a_loop])
a_second_if = if_node([branch_free_code(1,.9)],[an_if],[branch_free_code(3,.9), branch_free_code(3,.9), boundary_node(42)])
#main = EntryNode("main", [a_loop], 2)
main = EntryNode("main", [a_second_if], 1)
f_graph = FunctionGraph(main)
f_graph.draw_and_display()

