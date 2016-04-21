import sys, os

from cfg import cfg, cfg2graphml, cfg_cdvfs_generator

thisdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,  os.path.join(thisdir, 'cfg/pycparser'))

from pycparser import parse_file, c_parser, c_generator

def run_cfg(filename):
    # create CFG
    graph = cfg.CFG(filename)
    ast = graph.make_cfg()
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


if __name__ == '__main__':

    if len(sys.argv) < 2:
        print('Too few arguments')
    else:
        run_cfg(sys.argv[1])
