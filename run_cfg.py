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
import dummy_ast as ast
import dummy_cfg as cfg

from pycparser import parse_file, c_parser, c_generator
from collections import deque

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
    print generator.visit(ast)
    return (graph, ast, DG)

#Assumes DAG.
def avg_BFS(DG):
    nodes = nx.topological_sort(DG)
    list_o_lists = [(0, 0)]*len(nodes)
    sources = [node for node, indegree in DG.in_degree(DG.nodes()).items() if indegree == 0]
    for source in sources:
        list_o_lists[nodes.index(source)] = (1, 1)
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
            list_o_lists[nodes.index(node)] = (node_total/float(node_denom), node_denom)
        if DG.out_degree(node) == 0:
            pair = list_o_lists[nodes.index(node)]
            total += pair[0]*pair[1]
            denom += pair[1]
    return total/float(denom)

def p_DFS(node, cur_list, DG):
    if DG.out_degree(node) == 0:
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


def path_exists_from_node_to_exit(DG, start_node):
    visited = set()
    to_visit = deque([start_node])
    while to_visit:
        curr = to_visit.popleft()
        visited.add(curr)
        if curr.node_type() == ast.boundary_type:
            continue
        if curr.node_type() == cfg.return_type:
            return True
        for succ in DG.successors(curr):
            if succ not in visited:
                to_visit.append(succ)
    return False

#Precondition: start_node is program entry node
#Find lowest cost path from start node to boundary - this corresponds to the path with the lowest prob of success
#count the program's return node as a boundary
#Since we have directed graph, multiplication is fine, since there can't be loops.
#TODO: find a numeric type with good stability properties, etc
def get_shortest_path_to_each_boundary(DG, start_node, exit_node, initial_cost):
    node_to_in_degree = {node: in_degree for node, in_degree in (n, DG.in_degree(n) in DG.nodes())}
    node_to_lowest_cost = {start_node: initial_cost}
    #TODO: tweak numerics
    boundary_to_cost = {node: float('inf') for node in DG.nodes if node.node_type() == ast.boundary_type}
    boundary_to_cost[exit_node] = float('inf')
    to_visit = deque([start_node])
    while to_visit:
        curr = to_visit.popleft()
        for succ in DG.successors(curr):
            edge_cost = DG[curr][succ][cfg.probability_key]
            new_cost = edge_cost * node_to_lowest_cost(curr) #TODO: better numerics?
            if succ in (node_to_lowest_cost && new_cost < node_to_lowest_cost[succ]) or succ not in node_to_lowest_cost:
                node_to_lowest_cost[succ] = new_cost
            node_to_in_degree[succ] -= 1
            if node_to_in_degree[succ] == 0:
                to_visit.append(succ)
                if succ.node_type == ast.boundary_type or succ is exit_node:
                    boundary_to_cost[succ] = node_to_lowest_cost[succ]
                    node_to_lowest_cost[succ] = float('inf') #TODO: tweak numerics

    return boundary_to_cost

def get_average_path_instr_counts(DG, start_node):
    node_to_in_degree = {node: in_degree for node, in_degree in (n, DG.in_degree(n) in DG.nodes())}
    node_to_path_info = {start_node: (0, 1)}
    to_visit = deque([start_node])
    while to_visit:
        curr = to_visit.popleft()
        for succ in DG.successors(curr):
            instr_sum, paths = node_to_path_info[succ]
            edge_instrs = DG[curr][succ][cfg.insructions_key]
            node_to_path_info[succ] = (instr_sum + edge_instrs, paths + 1)
            node_to_in_degree[succ] -= 1
            if node_to_in_degree[succ] == 0:
                to_visit.append(succ)
    return node_to_path_info

#Precondition - every path through CFG is checkpointed
def find_lowest_success_prob(DG, start_node, exit_node):
    costs = get_shortest_path_to_each_boundary(DG, start_node, exit_node 0)
    exit_cost = costs[exit_node]
    overlapped_costs = get_shortest_path_to_each_boundary(DG, start_node, exit_node, exit_cost)
    minimum_prob = float('inf') #TODO: tweak numerics
    for node in exit_cost:
        node_cost = min(costs[node], overlapped_costs[node])
        minimum_prob = min(minimum_prob, node_cost)
    return minimum_prob

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
        print 'Too few arguments'
    else:
        res = run_cfg(sys.argv[1])
        DG = nx.DiGraph()
        for (u, v) in res[2].edges():
            DG.add_edge(u, v, weight=1)
        print avg_BFS(DG)
        for element in prob_DFS(DG):
            print element
        print Dijkstras(DG)
