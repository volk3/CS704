import sys, os

from cfg import cfg, cfg2graphml, cfg_cdvfs_generator

thisdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,  os.path.join(thisdir, 'cfg/pycparser'))
sys.path.insert(0,  os.path.join(thisdir, 'cfg'))
#sys.path.insert(0,  os.path.join(thisdir, 'cfg/networkx-1.11'))

from cfg_nodes import CFGNodeType
from cfg_nodes import CFGEntryNode
from cfg_nodes import CFGNode

import networkx as nx

from pycparser import parse_file, c_parser, c_generator

def run_cfg(filename):
    # create CFG
    graph = cfg.CFG(filename)
    ast = graph.make_cfg()
    DG = graph.get_DG()
    #cfg.show()

    # create graphml
    graphml = cfg2graphml.CFG2Graphml()
    #graphml.add_boundaries(graph, file_name='', yed_output=True, 1)
    graphml.make_graphml(graph, 1, file_name='', yed_output=True)

    # generate DVFS-aware code
    cdvfs = cfg_cdvfs_generator.CFG_CDVFS()
    #cdvfs.gen(graph)

#CHANGED.  Added a print for the results.
    generator = c_generator.CGenerator()
    print(generator.visit(ast))
    return (cfg, ast, DG)

#Assumes DAG.
def avg_BFS(DG):
    nodes = nx.topological_sort(DG)
    list_o_lists = [(0,0)]*len(nodes)
    sources = [node for node, indegree in DG.in_degree(DG.nodes()).items() if indegree == 0]
    for source in sources:
	list_o_lists[nodes.index(source)] = (1,1)
    total = 0
    denom = 0
    avgs = []
    for node in nodes:
	node_total = 0
        node_denom = 0
        for pred in DG.predecessors(node):
            pair = list_o_lists[nodes.index(pred)]
	    node_total += (pair[0]+1)*pair[1]
	    node_denom += pair[1]
            list_o_lists[nodes.index(node)] = (node_total/float(node_denom),node_denom)
        if(DG.out_degree(node) == 0):
	    pair = list_o_lists[nodes.index(node)]
            total += pair[0]*pair[1]
	    denom += pair[1]
    return total/float(denom)

def p_DFS(node, cur_list, DG):
    if(DG.out_degree(node) == 0):
	cur_list.append(node)
        yield cur_list[:]
	cur_list.pop()
    else:
	cur_list.append(node)
        for child in DG.successors(node):
	    for path in p_DFS(child, cur_list, DG):
                yield path
	cur_list.pop()

def prob_DFS(DG):
    sources = [node for node, indegree in DG.in_degree(DG.nodes()).items() if indegree == 0]
    for source in sources:
	for path in p_DFS(source, [], DG):
	    yield path

def Dijkstras(DG):
    nodes = nx.topological_sort(DG)
    dist = [float('inf')]*len(nodes)
    sources = [node for node, indegree in DG.in_degree(DG.nodes()).items() if indegree == 0]
    for source in sources:
	dist[nodes.index(source)] = 0
    for node in nodes:
        for child in DG.successors(node):
            if dist[nodes.index(child)] > dist[nodes.index(node)]+DG[node][child]['weight']:
                dist[nodes.index(child)] = dist[nodes.index(node)]+DG[node][child]['weight']
    return (nodes, dist)

if __name__ == '__main__':

    if len(sys.argv) < 2:
        print('Too few arguments')
    else:
        res = run_cfg(sys.argv[1])
	DG = nx.DiGraph()
	for (u, v) in res[2].edges():
	    DG.add_edge(u, v, weight=1)
        print(avg_BFS(DG))
        for element in prob_DFS(DG):
            print(element)
	print(Dijkstras(DG))
