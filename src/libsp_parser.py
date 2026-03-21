"""
SPICE Cells library parser.
Author: Tri Minh Cao
Email: tricao@utdallas.edu
Date: February 2017
"""


class SubCkt:
    """
    Represents a subckt description in the SPICE cells library.
    """
    # order of pins: gnd vdd A, B, C, ...
    # probably don't need to differentiate inputs from outputs?
    # (but I can use LEF file to recognize input and output)
    # each subckt has a a list of transistors
    def __init__(self, name):
        self.name = name
        self.pins = [] # a list of pins, order is important
        self.trans = [] # a list of Tran objects

    def parse_next(self, info):
        if info[0].lower()[0] == 'm':
            # create new transistor
            new_tran = Tran(info[0])
            new_tran.drain_net = info[1]
            new_tran.gate_net = info[2]
            new_tran.source_net = info[3]
            new_tran.bulk_net = info[4]
            new_tran.type = info[5]
            new_tran.width = info[6]
            new_tran.length = info[7]
            if len(info) > 8:
                new_tran.others.extend(info[8:])
            self.trans.append(new_tran)
        elif info[0] == '+':
            last_tran = self.trans[-1]
            last_tran.others.extend(info[1:])
        elif info[0] == '.ends':
            return 1
        # if continue, return 0
        return 0


class Tran:
    """
    Represents a transistor nmos/pmos.
    """
    def __init__(self, name):
        # gate net
        # source net
        # drain net
        # bulk net
        # width
        # length
        # other parameters
        self.name = name
        self.type = None
        self.drain_net = None
        self.gate_net = None
        self.source_net = None
        self.bulk_net = None
        self.width = None
        self.length = None
        # other parameters will be a list of parameters (each is a str)
        self.others = []

    def __str__(self):
        info = []
        info.append(self.name)
        info.append(self.drain_net)
        info.append(self.gate_net)
        info.append(self.source_net)
        info.append(self.bulk_net)
        info.append(self.type)
        info.append(self.width)
        info.append(self.length)
        info.extend(self.others)
        return ' '.join(info)


class LibSPParser:
    """
    Parser for the SPICE standard cells libary.
    """
    # parse each subckt
    # put them in a dict
    def __init__(self, sp_path):
        self.sp_path = sp_path
        self.cells = []
        self.cell_dict = {}
        self.stack = [] # to keep track of ongoing sections
        self.parse()

    def parse(self):
        f = open(self.sp_path, 'r')
        for line in f:
            info = line.split()
            if len(info) > 0:
                # print(info)
                if info[0] == '.subckt':
                    new_cell = SubCkt(info[1])
                    new_cell.pins = info[2:]
                    self.cells.append(new_cell)
                    self.cell_dict[info[1]] = new_cell
#                    if "X" in info[1]:
#                        x_idx = info[1].index("X")
#                        self.cell_dict[info[1][:x_idx]+"_"+info[1][x_idx:]] = new_cell
#                    else:
#                        self.cell_dict[info[1]] = new_cell
                    self.stack.append(new_cell)
                else:
                    current = self.stack[-1]
                    if current.parse_next(info):
                        self.stack.pop()


class NetlistParser:
    """
    Parser for a SPICE netlist (only consider transistor-level).
    """
    def __init__(self, sp_path):
        self.sp_path = sp_path
        self.trans = []
        self.tran_dict = {}
        self.parse()

    def parse(self):
        f = open(self.sp_path, 'r')
        for line in f:
            info = line.split()
            if len(info) > 0:
                # print(info)
                if info[0][0].lower() == 'm':
                    # create new transistor
                    tran_name = info[0].lower()
                    new_tran = Tran(tran_name)
                    new_tran.drain_net = info[1]
                    new_tran.gate_net = info[2]
                    new_tran.source_net = info[3]
                    new_tran.bulk_net = info[4]
                    new_tran.type = info[5]
                    new_tran.width = info[6]
                    new_tran.length = info[7]
                    if len(info) > 8:
                        new_tran.others.extend(info[8:])
                    self.trans.append(new_tran)
                    self.tran_dict[tran_name] = new_tran
                if len(self.trans) > 0:
                    if info[0] == '+':
                        last_tran = self.trans[-1]
                        last_tran.others.extend(info[1:])
                    elif info[0][0] == '+':
                        last_tran = self.trans[-1]
                        last_tran.append(info[0][1:])
                        last_tran.others.extend(info[1:])


# main method
if __name__ == '__main__':
    sp_file = './lib/freepdk45_cells.sp'
    libsp_parser = LibSPParser(sp_file)
    libsp_parser.parse()
    # print(libsp_parser.cell_dict.keys())
    # for each in libsp_parser.cell_dict['OAI22X1'].trans:
    #     print(each)
#    netlist_parser = NetlistParser('./spice/adder_2bit_all_gates_expanded.sp')
#    netlist_parser.parse()
#    print(netlist_parser.tran_dict.keys())
#    print(netlist_parser.tran_dict['M10'])

