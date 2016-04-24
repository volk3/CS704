import sys, os

from cfg import cfg, cfg2graphml, cfg_cdvfs_generator

thisdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,  os.path.join(thisdir, 'cfg/pycparser'))
sys.path.insert(0,  os.path.join(thisdir, 'cfg'))
sys.path.insert(0,  os.path.join(thisdir, 'cfg/networkx-1.11'))

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
    graphml.make_graphml(graph, 2, file_name='', yed_output=True)

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
    sources = [node for node, indegree in DG.in_degree(DG.nodes()).items() if indegree == 0]
    for source in sources:
        source.add_count(1,1)
    total = 0
    denom = 0
    avgs = []
    for node in nodes:
        if node.get_place_boundary():
            for pred in DG.predecessors(node):
                for pair in pred.get_counts():
                    node.add_count(pair[0]+2,pair[1])
        else:
            for pred in DG.predecessors(node):
                for pair in pred.get_counts():
                    node.add_count(pair[0]+1,pair[1])
        if node.get_type() == CFGNodeType.END:
            avgs.append(node.get_counts()[:])

#DOESN'T WORK.
#    for source in sources:
#        visited = []
#        Q = [source]
#        source.add_count(1,1)
#	while not len(Q) is 0:
#	    node = Q[0]
#            Q.remove(node)
#            if node.get_type() == CFGNodeType.END:
#                avgs.append(node.get_counts()[:])
#            else:
#                for succ in DG.successors(node):
#                    print(node.get_counts())
#                    for pair in node.get_counts():
#                        print(pair)
#                        succ.add_count(pair[0]+1, pair[1])
#                    print(succ.get_counts())
#                    if not succ in visited:
#                        Q.append(succ)
#			visited.append(succ)

    for avg in avgs:
        for pair in avg:
            total += pair[0]*pair[1]
            denom += pair[1]

    return total/float(denom)

def p_DFS(F, p, node, pi, prob, t, DG):
    if(node.get_place_boundary()):
        new_prob = prob*F(p(1),pi)*F(p(2),pi+[None])
        if(node.get_type() == CFGNodeType.END):
            return [1-new_prob]
        res = []
        for child in DG.successors(node):
            res.append(p_DFS(F, p, child, pi+[None]+[node], new_prob, 3, DG))
        return max(res)
    else:
        new_prob = prob*F(p(t),pi)
        if(node.get_type() == CFGNodeType.END):
            return [1-new_prob]
        res = []
        for child in DG.successors(node):
            res.append(p_DFS(F, p, child, pi+[node], new_prob, t+1, DG))
        return max(res)

def prob_DFS(F, p, DG):
    sources = [node for node, indegree in DG.in_degree(DG.nodes()).items() if indegree == 0]
    res = []
    for source in sources:
        res.append(p_DFS(F, p, source, [], 1, 1, DG))
    return max(res)[0]  

def F(p, pi):
    return 0.99*p

def p(t):
    prob = 0.99
    for i in range(t-1):
        prob *= 0.99
    return prob

if __name__ == '__main__':

    if len(sys.argv) < 2:
        print('Too few arguments')
    else:
        res = run_cfg(sys.argv[1])
        print(avg_BFS(res[2]))
        print(prob_DFS(F, p, res[2]))
