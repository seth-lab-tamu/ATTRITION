# -*- coding: utf-8 -*-
"""
Created on Thu Sep  2 14:17:04 2021

@author: gohil.vasudev
"""

'''
This script is for inserting Trojans in rare nodes for a given verilog netlist
'''


import networkx as nx
import numpy as np
import pickle
import random
import copy
#import math
import os
import pycosat
from libsp_parser import *
import time
import sys


def gate_sub_cnf(gate_name, inputs, output):
    """
    Generate a list of cnf-sub-expressions for a gate.
    :param gate_name:
    :param inputs:
    :param output:
    :return:
    """
    exps = []
    if gate_name[:3] == 'and':
        fanin = int(gate_name[3])
        l = [output]
        for k in range(fanin):
            l.append(-inputs[k])
        exps.append(l)
        for k in range(fanin):
            exps.append([inputs[k], -output])
    elif gate_name[:3] == 'nnd':
        fanin = int(gate_name[3])
        l = [-output]
        for k in range(fanin):
            l.append(-inputs[k])
        exps.append(l)
        for k in range(fanin):
            exps.append([inputs[k], output])
    elif gate_name[:2] == 'or':
        fanin = int(gate_name[2])
        l = [-output]
        for k in range(fanin):
            l.append(inputs[k])
        exps.append(l)
        for k in range(fanin):
            exps.append([-inputs[k], output])
    elif gate_name[:3] == 'nor':
        fanin = int(gate_name[3])
        l = [output]
        for k in range(fanin):
            l.append(inputs[k])
        exps.append(l)
        for k in range(fanin):
            exps.append([-inputs[k], -output])
    elif gate_name[:3] == 'hi1':
        exps.append([-inputs[0], -output])
        exps.append([inputs[0], output])
    elif gate_name[:3] == 'nb1':
        exps.append([inputs[0], -output])
        exps.append([-inputs[0], output])
    elif gate_name[:4] == 'xor2':
        exps.append([-inputs[0], -inputs[1], -output])
        exps.append([inputs[0], inputs[1], -output])
        exps.append([inputs[0], -inputs[1], output])
        exps.append([-inputs[0], inputs[1], output])
    else:
        print("ERROR!! Found unknown gate in SAT formulation")
    return exps


def verilog_to_sat(vfile, libsp):
    """
    Convert a gate-level verilog file to a SAT-CNF problem.
    :param vfile:
    :param libsp:
    :return:
    """
    # approach: parse the verilog file and build the SAT problem in parallel
    global cntt1
    clauses = []
    net2int_dict = {}
    int2net_dict = {}
    net_idx = 1
    for line in vfile:
        line = line.strip()
        info = line.split()
#        print("info: ", info)
        if len(info) > 0:
            if info[0] in libsp.cell_dict:
#                print("Yes")
                gate_name = info[0]
#                print(gate_name)
                output = None
                inputs = []
                for i in range(2, len(info)):
                    if info[i][0] == '.':
                        pin_name, net_name = net_from_pin(info[i])
                        # check if the pin is an output
#                        if pin_name == 'Y':
#                        if "Z" in pin_name:
                        if "Q" in pin_name:
                            # check if the net is already has an index
                            if net_name in net2int_dict:
                                output = net2int_dict[net_name]
                            else:
                                output = net_idx
                                net2int_dict[net_name] = net_idx
                                int2net_dict[net_idx] = net_name
                                net_idx += 1
                        else:
                            if net_name in net2int_dict:
                                inputs.append(net2int_dict[net_name])
                            else:
                                inputs.append(net_idx)
                                net2int_dict[net_name] = net_idx
                                int2net_dict[net_idx] = net_name
                                net_idx += 1
#                print(inputs)
#                print(output)
                new_clauses = gate_sub_cnf(gate_name, inputs, output)
                cntt1 += 1
                clauses.extend(new_clauses)
            elif info[0] == 'input':
                i = 1
                while i < len(info):
                    if info[i][0] == '[':
                        nets = get_io_nets(info[i+1][:-1], info[i])   # Unrolls the nets of the inpur bus
                        i += 2										# eg nets = in_0[0], in_0[1]. etc
                    else:
                        nets = get_io_nets(info[i][:-1])
                        i += 1
                    for each in nets:
                        net2int_dict[each] = net_idx
                        int2net_dict[net_idx] = each
                        net_idx += 1
            elif info[0] == 'output':
                i = 1
                while i < len(info):
                    if info[i][0] == '[':
                        nets = get_io_nets(info[i+1][:-1], info[i])
                        i += 2
                    else:
                        nets = get_io_nets(info[i][:-1])
                        i += 1
                    for each in nets:
                        net2int_dict[each] = net_idx
                        int2net_dict[net_idx] = each
                        # add each output to the clauses list
                        # clauses.append([net_idx])
                        net_idx += 1
    return clauses, net2int_dict, int2net_dict


def get_io_nets(io_name, array_str=None):
    if array_str:
        ends = array_str[1:-1].split(':')
        ends = [int(ends[0]), int(ends[1])]
        ends.sort()
        net_list = []
        for i in range(ends[0], ends[1] + 1):
            net_list.append(io_name + '[' + str(i) + ']')
        return net_list
    else:
        return [io_name]


def net_from_pin(pin):
    """
    Get the net from a pin assignment.
    For example: .A(n47) will return n47
    :param pin: pin assignment
    :return: tuple (pin_name, net_name)
    """
    start_net_idx = 0 # starting str index of the net name
    str_len = len(pin)
    pin_name = ''
    for i in range(1, str_len):
        if pin[i] == '(':
            start_net_idx = i
            break
        else:
            pin_name += pin[i]
    # get the net name
    net_name = ''
    for i in range(start_net_idx + 1, str_len):
        if pin[i] == ')':
            break
        else:
            net_name += pin[i]
    return pin_name, net_name

def nb1s(a):
    return a[0]
def hi1s(a):
    return int(abs(1-a[0]))
def and2s(a):
    return a[0]&a[1]
def and3s(a):
    return a[0]&a[1]&a[2]
def and4s(a):
    return a[0]&a[1]&a[2]&a[3]
def and5s(a):
    return a[0]&a[1]&a[2]&a[3]&a[4]
def and9s(a):
    return a[0]&a[1]&a[2]&a[3]&a[4]&a[5]&a[6]&a[7]&a[8]
def or2s(a):
    return a[0]|a[1]
def or3s(a):
    return a[0]|a[1]|a[2]
def or4s(a):
    return a[0]|a[1]|a[2]|a[3]
def or5s(a):
    return a[0]|a[1]|a[2]|a[3]|a[4]
def nor2s(a):
    return int(not(or2s(a)))
def nor3s(a):
    return int(not(or3s(a)))
def nor4s(a):
    return int(not(or4s(a)))
def nor5s(a):
    return int(not(or5s(a)))
def nnd2s(a):
    return int(not(and2s(a)))
def nnd3s(a):
    return int(not(and3s(a)))
def nnd4s(a):
    return int(not(and4s(a)))
def nnd5s(a):
    return int(not(and5s(a)))
def xor2s(a):
    return a[0]^a[1]


def v_file_to_graph(v_file):
    with open(v_file, 'r') as f:
        file_contents = f.read()
    
    lines = file_contents.split(";")
    for i in range(len(lines)):
        lines[i] = lines[i].strip()
    
    
    for i in range(len(lines)):
        if "input" in lines[i]:
            inp_ln = i
        if "output" in lines[i]:
            op_ln = i
        if "wire" in lines[i]:
            wire_ln = i
        if "endmodule" in lines[i]:
            end_ln = i
    
    inputs = [i.strip() for i in lines[inp_ln].split("input")[1].split(",")]
    outputs = [i.strip() for i in lines[op_ln].split("output")[1].split(",")]
    wires = [i.strip() for i in lines[wire_ln].split("wire")[1].split(",")]
    
    Components_Dict = {}
    for i in range(wire_ln+1,end_ln):
        num_ports = lines[i].count(".")
        Components_Dict[lines[i].split(" ")[1]] = [lines[i].split(" ")[0]]
        for j in range(num_ports):
            Components_Dict[lines[i].split(" ")[1]].append(lines[i].split(" ")[j+3][lines[i].split(" ")[j+3].index("(")+1:lines[i].split(" ")[j+3].index(")")])
    gate_types = list(set([list(Components_Dict.values())[i][0] for i in range(len(Components_Dict))]))
    libsp_gate_types = []
    for gt in gate_types:
    #    gt = gt.replace("_X","X")
        if gt not in libsp_gate_types:
            libsp_gate_types.append(gt)
#    gate_types = list(set([list(Components_Dict.values())[i][0] for i in range(len(Components_Dict))]))
    
    G = nx.DiGraph()
    G.add_nodes_from(inputs)
    G.add_nodes_from(outputs)
    G.add_nodes_from(wires)
    G.add_nodes_from(list(Components_Dict.keys()))
    
    for node in Components_Dict:
#        ips = Components_Dict[node][1:-1]
        ips = Components_Dict[node][2:]
#        output = Components_Dict[node][-1]
        output = Components_Dict[node][1]
        for i in ips:
            G.add_edge(i,node)
        G.add_edge(node,output)
#    top_sort = nx.topological_sort(G)
    return G

#lines = open("../original_files/c880.v").readlines()
#v_file = "c3540"
#v_file = 'c6288_syn'
#v_file = 'c5315_renamed'
#v_file = 'c1908'
#v_file = 'c1355'
#v_file = 'c880'
#v_file = 'c432'
#v_file = 'c3540'
#v_file = 'c5315'
#v_file = 'c6288'
#v_file = 'c7552'
#v_file = 'c7552_modified'
#v_file = 'c2670_syn_modified'
#v_file = 'mips'
#v_file = 'mips_full_lib'

v_file = 'c2670'
#v_file = 'c5315'
#v_file = 'c6288'
#v_file = 'c7552'
#v_file = 's13207'
#v_file = 's15850'
#v_file = 's35932'

for v_file in [sys.argv[1]]:
    #trig_width = 12 #4  # 2 or 4 or 8
    
    for trig_width in [int(sys.argv[2])]:
        #depth_of_trig = [0]*100
        
        with open("../original_files/"+v_file+".v", 'r') as f:
        #    file_contents = f.read()
        #with open("../del/"+v_file+".v", 'r') as f:
            file_contents = f.read()
        
        lines = file_contents.split(";")
        for i in range(len(lines)):
            lines[i] = lines[i].strip()
        
        
        for i in range(len(lines)):
            if "input" in lines[i]:
                inp_ln = i
            if "output" in lines[i]:
                op_ln = i
            if "wire" in lines[i]:
                wire_ln = i
            if "endmodule" in lines[i]:
                end_ln = i
        
        inputs = [i.strip() for i in lines[inp_ln].split("input")[1].split(",")]
        outputs = [i.strip() for i in lines[op_ln].split("output")[1].split(",")]
        wires = [i.strip() for i in lines[wire_ln].split("wire")[1].split(",")]
        
        Components_Dict = {}
        for i in range(wire_ln+1,end_ln):
            num_ports = lines[i].count(".")
            Components_Dict[lines[i].split(" ")[1]] = [lines[i].split(" ")[0]]
            for j in range(num_ports):
                Components_Dict[lines[i].split(" ")[1]].append(lines[i].split(" ")[j+3][lines[i].split(" ")[j+3].index("(")+1:lines[i].split(" ")[j+3].index(")")])
        
        gate_types = list(set([list(Components_Dict.values())[i][0] for i in range(len(Components_Dict))]))
        libsp_gate_types = []
        for gt in gate_types:
        #    gt = gt.replace("_X","X")
            if gt not in libsp_gate_types:
                libsp_gate_types.append(gt)
        
        
        G = nx.DiGraph()
        G.add_nodes_from(inputs)
        G.add_nodes_from(outputs)
        G.add_nodes_from(wires)
        G.add_nodes_from(list(Components_Dict.keys()))
        
        for node in Components_Dict:
        #    ips = Components_Dict[node][1:-1]
            ips = Components_Dict[node][2:]
        #    output = Components_Dict[node][-1]
            output = Components_Dict[node][1]
            for i in ips:
                G.add_edge(i,node)
            G.add_edge(node,output)
        top_sort = nx.topological_sort(G)
        
        with open("../saved_simulations/"+v_file+"_tmp.pickle",'rb') as f:
            tmp = pickle.load(f)
        
        #tmp = np.sum(data,0)
        #tmp = tmp/50000
        #cnt = 0
        
        thresh_low = 0.1 #0.1 #0.0009 #0.1
        thresh_high = 1-thresh_low
        #rare_idcs = []
        rare_nets = []
        rare_values = np.array([])
        for i in range(len(tmp)):
            if (tmp[i]<thresh_low) or (tmp[i]>thresh_high):
        #        cnt+=1
        #        rare_idcs.append(i)
                rare_nets.append((wires+outputs)[i])
                if tmp[i]<0.5:
                    rare_values = np.append(rare_values,1)
                else:
                    rare_values = np.append(rare_values,0)
        #        rare_values = np.append(rare_values,tmp[i])
        
        orig_lines = open("../original_files/"+v_file+".v", 'r').readlines()
        #orig_lines = open("../del/"+v_file+".v", 'r').readlines()
        
        
        #with open("../rare_nets_compatibility/"+v_file+"/big_dict.pickle",'rb') as f:
        #    big_dict = pickle.load(f)
        #comp_dict = {}
        #for key1 in big_dict:
        #    if key1 not in comp_dict:
        #        comp_dict[key1] = []
        #    for key2 in big_dict[key1]:
        #        if big_dict[key1][key2] == 1:
        #            if key2 not in comp_dict:
        #                comp_dict[key2] = []
        #            if key2 not in comp_dict[key1]:
        #                comp_dict[key1].append(key2)
        #            if key1 not in comp_dict[key2]:
        #                comp_dict[key2].append(key1)
        #
        #
        #for key1 in big_dict:
        #    for key2 in big_dict[key1]:
        #        if key2 not in comp_dict:
        #            comp_dict[key2] = []
        #        if big_dict[key1][key2] == 1:
        #            if key1 not in comp_dict[key2]:
        #                comp_dict[key2].append(key1)
        
        
        
        
        num_Trojan_infested_files = 100
        n = 0
        #for n in range(num_Trojan_infested_files):
        while n<num_Trojan_infested_files:
            print(n)
            new_lines = copy.deepcopy(orig_lines)
            for endmodule_idx in range(len(new_lines)-1,0,-1):
                if 'endmodule' in new_lines[endmodule_idx]:
                    break
            
            
        #    trig_target_nets = random.sample(rare_nets,k=trig_width+1)
        #    target_net = trig_target_nets[-1] # str
        #    trig_nets = trig_target_nets[:-1] # list
            try_sample = True
            
        #    print("Started trying for n = " + str(n))
        #    trig_nets = []
        #    sw=True
        #    while sw == True:
        #        first_trig_net = random.sample(rare_nets,k=1)[0]
        #        trig_nets.append(first_trig_net)
        #        ix = top_sort.index(first_trig_net)
        #        if ix == len(top_sort)-1:
        #            sw = True
        #        else:
        #            sw = False
        #    cntr = 1
        #    S = set(comp_dict[trig_nets[0]])
        #    max_idx = 0
        #    while try_sample == True:
        #        for t in trig_nets:
        #            S = S.intersection(set(comp_dict[t]))
        #        curr_comp_lst = list(S)
        #        if len(curr_comp_lst) >0:
        #            curr_trig_net = random.sample(curr_comp_lst,k=1)[0]
        #            trig_nets.append(curr_trig_net)
        #            cntr += 1
        #            if cntr == trig_width:
        #                for net in trig_nets:
        #                    if top_sort.index(net)> max_idx:
        #                        max_idx = top_sort.index(net)
        #                if max_idx == len(top_sort) - 1:
        #                    try_sample = True
        #                else:
        #                    try_sample = False
        #    print("passed for n = " + str(n))
                    
              
            while try_sample == True:
                max_idx = 0
                trig_nets = random.sample(rare_nets,k=trig_width)
                for net in trig_nets:
                    if top_sort.index(net)> max_idx:
                        max_idx = top_sort.index(net)
            #    target_net = random.sample(wires+outputs,k=1)[0]
                if max_idx == len(top_sort)-1:
                    try_sample = True
                else:
                    try_sample = False
            
        #    dpth = 999999999
        #    for i in inputs:
        #        if nx.has_path(G,i,top_sort[max_idx]):
        #            d = nx.shortest_path_length(G,source=i,target=top_sort[max_idx])
        #            if d<dpth:
        #                dpth = copy.deepcopy(d)
                    
        #    depth_of_trig[n] = dpth
            target_net = random.sample(top_sort[max_idx+1:],k=1)[0]
            
            try_targ = True
        #    while target_net not in wires+outputs:
            while try_targ:
                target_net = random.sample(top_sort[max_idx+1:],k=1)[0]
                if target_net in wires+outputs:
                    if target_net not in inputs:
                        try_targ = False
            rare_values_of_trig_nets = []
            for net in trig_nets:
                rare_values_of_trig_nets.append(rare_values[rare_nets.index(net)])
            
            new_and_gates_nets = []
            add_to_wires = []
            maxx_cnt = 0
            for comp in Components_Dict:
                if comp[0] == 'U':
                    if maxx_cnt < int(comp[1:]):
                        maxx_cnt = int(comp[1:])
            cnt = maxx_cnt+1
        #    cnt = int(list(Components_Dict.keys())[-1].split("U")[-1]) + 1
            cntt = 0
            if trig_width == 2:
                if rare_values_of_trig_nets[0] == 0:
                    if rare_values_of_trig_nets[1] == 0:
            #            gt1 = "NOR2_X1"
        #                new_lines[endmodule_idx-1] += "  NOR2_X1 U"+str(cnt)+ " ( .A1("+trig_nets[0]+"), .A2("+trig_nets[1]+"), .ZN(tmp_"+str(cntt)+") );\n"
        #                new_lines[endmodule_idx-1] += "  nor2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1("+trig_nets[0]+"), .DIN2("+trig_nets[1]+") );\n"
                        new_lines[endmodule_idx-1] += "  nor2s1 U"+str(cnt)+ " ( .Q(tmp_trig_en), .DIN1("+trig_nets[0]+"), .DIN2("+trig_nets[1]+") );\n"
                        new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
                    elif rare_values_of_trig_nets[1] == 1:
        #                new_lines[endmodule_idx-1] += "  INV_X1 U"+str(cnt)+ " ( .A("+trig_nets[1]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  hi1s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN("+trig_nets[1]+") );\n"
            #            new_and_gates_nets.append(cntt)
        #                add_to_wires.append("tmp_"+str(cntt))
                        add_to_wires.append("tmp_trig_en")
                        cnt+=1
                        cntt+=1
        #                new_lines[endmodule_idx-1] += "  NOR2_X1 U"+str(cnt)+ " ( .A1(tmp_"+str(cntt-1)+"), .A2("+trig_nets[0]+"), .ZN(tmp_"+str(cntt)+") );\n"
        #                new_lines[endmodule_idx-1] += "  nor2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1(tmp_"+str(cntt-1)+"), .DIN2("+trig_nets[0]+") );\n"
                        new_lines[endmodule_idx-1] += "  nor2s1 U"+str(cnt)+ " ( .Q(tmp_trig_en), .DIN1(tmp_"+str(cntt-1)+"), .DIN2("+trig_nets[0]+") );\n"
                        new_and_gates_nets.append(cntt)
        #                add_to_wires.append("tmp_"+str(cntt))
                        add_to_wires.append("tmp_trig_en")
                        cnt+=1
                        cntt+=1
                elif rare_values_of_trig_nets[0] == 1:
                    if rare_values_of_trig_nets[1] == 0:
        #                new_lines[endmodule_idx-1] += "  INV_X1 U"+str(cnt)+ " ( .A("+trig_nets[0]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  hi1s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN("+trig_nets[0]+") );\n"
            #            new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
        #                new_lines[endmodule_idx-1] += "  NOR2_X1 U"+str(cnt)+ " ( .A1(tmp_"+str(cntt-1)+"), .A2("+trig_nets[1]+"), .ZN(tmp_"+str(cntt)+") );\n"
        #                new_lines[endmodule_idx-1] += "  nor2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1(tmp_"+str(cntt-1)+"), .DIN2("+trig_nets[1]+") );\n"
                        new_lines[endmodule_idx-1] += "  nor2s1 U"+str(cnt)+ " ( .Q(tmp_trig_en), .DIN1(tmp_"+str(cntt-1)+"), .DIN2("+trig_nets[1]+") );\n"
                        new_and_gates_nets.append(cntt)
        #                add_to_wires.append("tmp_"+str(cntt))
                        add_to_wires.append("tmp_trig_en")
                        cnt+=1
                        cntt+=1
                    elif rare_values_of_trig_nets[1] == 1:
        #                new_lines[endmodule_idx-1] += "  AND2_X1 U"+str(cnt)+ " ( .A1("+trig_nets[0]+"), .A2("+trig_nets[1]+"), .ZN(tmp_"+str(cntt)+") );\n"
        #                new_lines[endmodule_idx-1] += "  and2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1("+trig_nets[0]+"), .DIN2("+trig_nets[1]+") );\n"
                        new_lines[endmodule_idx-1] += "  and2s1 U"+str(cnt)+ " ( .Q(tmp_trig_en), .DIN1("+trig_nets[0]+"), .DIN2("+trig_nets[1]+") );\n"
                        new_and_gates_nets.append(cntt)
        #                add_to_wires.append("tmp_"+str(cntt))
                        add_to_wires.append("tmp_trig_en")
                        cnt+=1
                        cntt+=1
                
            
            elif trig_width == 4:
                if rare_values_of_trig_nets[0] == 0:
                    if rare_values_of_trig_nets[1] == 0:
            #            gt1 = "NOR2_X1"
        #                new_lines[endmodule_idx-1] += "  NOR2_X1 U"+str(cnt)+ " ( .A1("+trig_nets[0]+"), .A2("+trig_nets[1]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  nor2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1("+trig_nets[0]+"), .DIN2("+trig_nets[1]+") );\n"
                        new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
                    elif rare_values_of_trig_nets[1] == 1:
        #                new_lines[endmodule_idx-1] += "  INV_X1 U"+str(cnt)+ " ( .A("+trig_nets[1]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  hi1s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN("+trig_nets[1]+") );\n"
            #            new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
        #                new_lines[endmodule_idx-1] += "  NOR2_X1 U"+str(cnt)+ " ( .A1(tmp_"+str(cntt-1)+"), .A2("+trig_nets[0]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  nor2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1(tmp_"+str(cntt-1)+"), .DIN2("+trig_nets[0]+") );\n"
                        new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
                elif rare_values_of_trig_nets[0] == 1:
                    if rare_values_of_trig_nets[1] == 0:
        #                new_lines[endmodule_idx-1] += "  INV_X1 U"+str(cnt)+ " ( .A("+trig_nets[0]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  hi1s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN("+trig_nets[0]+") );\n"
            #            new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
        #                new_lines[endmodule_idx-1] += "  NOR2_X1 U"+str(cnt)+ " ( .A1(tmp_"+str(cntt-1)+"), .A2("+trig_nets[1]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  nor2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1(tmp_"+str(cntt-1)+"), .DIN2("+trig_nets[1]+") );\n"
                        new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
                    elif rare_values_of_trig_nets[1] == 1:
        #                new_lines[endmodule_idx-1] += "  AND2_X1 U"+str(cnt)+ " ( .A1("+trig_nets[0]+"), .A2("+trig_nets[1]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  and2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1("+trig_nets[0]+"), .DIN2("+trig_nets[1]+") );\n"
                        new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
                
                if rare_values_of_trig_nets[2] == 0:
                    if rare_values_of_trig_nets[3] == 0:
            #            gt1 = "NOR2_X1"
        #                new_lines[endmodule_idx-1] += "  NOR2_X1 U"+str(cnt)+ " ( .A1("+trig_nets[2]+"), .A2("+trig_nets[3]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  nor2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1("+trig_nets[2]+"), .DIN2("+trig_nets[3]+") );\n"
                        new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
                    elif rare_values_of_trig_nets[3] == 1:
        #                new_lines[endmodule_idx-1] += "  INV_X1 U"+str(cnt)+ " ( .A("+trig_nets[3]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  hi1s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN("+trig_nets[3]+") );\n"
            #            new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
        #                new_lines[endmodule_idx-1] += "  NOR2_X1 U"+str(cnt)+ " ( .A1(tmp_"+str(cntt-1)+"), .A2("+trig_nets[2]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  nor2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1(tmp_"+str(cntt-1)+"), .DIN2("+trig_nets[2]+") );\n"
                        new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
                elif rare_values_of_trig_nets[2] == 1:
                    if rare_values_of_trig_nets[3] == 0:
        #                new_lines[endmodule_idx-1] += "  INV_X1 U"+str(cnt)+ " ( .A("+trig_nets[2]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  hi1s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN("+trig_nets[2]+") );\n"
            #            new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
        #                new_lines[endmodule_idx-1] += "  NOR2_X1 U"+str(cnt)+ " ( .A1(tmp_"+str(cntt-1)+"), .A2("+trig_nets[3]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  nor2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1(tmp_"+str(cntt-1)+"), .DIN2("+trig_nets[3]+") );\n"
                        new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
                    elif rare_values_of_trig_nets[3] == 1:
        #                new_lines[endmodule_idx-1] += "  AND2_X1 U"+str(cnt)+ " ( .A1("+trig_nets[2]+"), .A2("+trig_nets[3]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  and2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1("+trig_nets[2]+"), .DIN2("+trig_nets[3]+") );\n"
                        new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
            
            elif trig_width in [6,10,12,14,16]:
                
                for l in range(0,trig_width,2):
                    # For l and l+1
                    if rare_values_of_trig_nets[l+0] == 0:
                        if rare_values_of_trig_nets[l+1] == 0:
                #            gt1 = "NOR2_X1"
            #                new_lines[endmodule_idx-1] += "  NOR2_X1 U"+str(cnt)+ " ( .A1("+trig_nets[0]+"), .A2("+trig_nets[1]+"), .ZN(tmp_"+str(cntt)+") );\n"
                            new_lines[endmodule_idx-1] += "  nor2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1("+trig_nets[l+0]+"), .DIN2("+trig_nets[l+1]+") );\n"
                            new_and_gates_nets.append(cntt)
                            add_to_wires.append("tmp_"+str(cntt))
                            cnt+=1
                            cntt+=1
                        elif rare_values_of_trig_nets[l+1] == 1:
            #                new_lines[endmodule_idx-1] += "  INV_X1 U"+str(cnt)+ " ( .A("+trig_nets[1]+"), .ZN(tmp_"+str(cntt)+") );\n"
                            new_lines[endmodule_idx-1] += "  hi1s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN("+trig_nets[l+1]+") );\n"
                #            new_and_gates_nets.append(cntt)
                            add_to_wires.append("tmp_"+str(cntt))
                            cnt+=1
                            cntt+=1
            #                new_lines[endmodule_idx-1] += "  NOR2_X1 U"+str(cnt)+ " ( .A1(tmp_"+str(cntt-1)+"), .A2("+trig_nets[0]+"), .ZN(tmp_"+str(cntt)+") );\n"
                            new_lines[endmodule_idx-1] += "  nor2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1(tmp_"+str(cntt-1)+"), .DIN2("+trig_nets[l+0]+") );\n"
                            new_and_gates_nets.append(cntt)
                            add_to_wires.append("tmp_"+str(cntt))
                            cnt+=1
                            cntt+=1
                    elif rare_values_of_trig_nets[l+0] == 1:
                        if rare_values_of_trig_nets[l+1] == 0:
            #                new_lines[endmodule_idx-1] += "  INV_X1 U"+str(cnt)+ " ( .A("+trig_nets[0]+"), .ZN(tmp_"+str(cntt)+") );\n"
                            new_lines[endmodule_idx-1] += "  hi1s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN("+trig_nets[l+0]+") );\n"
                #            new_and_gates_nets.append(cntt)
                            add_to_wires.append("tmp_"+str(cntt))
                            cnt+=1
                            cntt+=1
            #                new_lines[endmodule_idx-1] += "  NOR2_X1 U"+str(cnt)+ " ( .A1(tmp_"+str(cntt-1)+"), .A2("+trig_nets[1]+"), .ZN(tmp_"+str(cntt)+") );\n"
                            new_lines[endmodule_idx-1] += "  nor2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1(tmp_"+str(cntt-1)+"), .DIN2("+trig_nets[l+1]+") );\n"
                            new_and_gates_nets.append(cntt)
                            add_to_wires.append("tmp_"+str(cntt))
                            cnt+=1
                            cntt+=1
                        elif rare_values_of_trig_nets[l+1] == 1:
            #                new_lines[endmodule_idx-1] += "  AND2_X1 U"+str(cnt)+ " ( .A1("+trig_nets[0]+"), .A2("+trig_nets[1]+"), .ZN(tmp_"+str(cntt)+") );\n"
                            new_lines[endmodule_idx-1] += "  and2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1("+trig_nets[l+0]+"), .DIN2("+trig_nets[l+1]+") );\n"
                            new_and_gates_nets.append(cntt)
                            add_to_wires.append("tmp_"+str(cntt))
                            cnt+=1
                            cntt+=1
            
            elif trig_width == 8:
                
                # For 0 and 1
                if rare_values_of_trig_nets[0] == 0:
                    if rare_values_of_trig_nets[1] == 0:
            #            gt1 = "NOR2_X1"
        #                new_lines[endmodule_idx-1] += "  NOR2_X1 U"+str(cnt)+ " ( .A1("+trig_nets[0]+"), .A2("+trig_nets[1]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  nor2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1("+trig_nets[0]+"), .DIN2("+trig_nets[1]+") );\n"
                        new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
                    elif rare_values_of_trig_nets[1] == 1:
        #                new_lines[endmodule_idx-1] += "  INV_X1 U"+str(cnt)+ " ( .A("+trig_nets[1]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  hi1s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN("+trig_nets[1]+") );\n"
            #            new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
        #                new_lines[endmodule_idx-1] += "  NOR2_X1 U"+str(cnt)+ " ( .A1(tmp_"+str(cntt-1)+"), .A2("+trig_nets[0]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  nor2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1(tmp_"+str(cntt-1)+"), .DIN2("+trig_nets[0]+") );\n"
                        new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
                elif rare_values_of_trig_nets[0] == 1:
                    if rare_values_of_trig_nets[1] == 0:
        #                new_lines[endmodule_idx-1] += "  INV_X1 U"+str(cnt)+ " ( .A("+trig_nets[0]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  hi1s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN("+trig_nets[0]+") );\n"
            #            new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
        #                new_lines[endmodule_idx-1] += "  NOR2_X1 U"+str(cnt)+ " ( .A1(tmp_"+str(cntt-1)+"), .A2("+trig_nets[1]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  nor2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1(tmp_"+str(cntt-1)+"), .DIN2("+trig_nets[1]+") );\n"
                        new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
                    elif rare_values_of_trig_nets[1] == 1:
        #                new_lines[endmodule_idx-1] += "  AND2_X1 U"+str(cnt)+ " ( .A1("+trig_nets[0]+"), .A2("+trig_nets[1]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  and2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1("+trig_nets[0]+"), .DIN2("+trig_nets[1]+") );\n"
                        new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
                
                # For 2 and 3
                if rare_values_of_trig_nets[2] == 0:
                    if rare_values_of_trig_nets[3] == 0:
            #            gt1 = "NOR2_X1"
        #                new_lines[endmodule_idx-1] += "  NOR2_X1 U"+str(cnt)+ " ( .A1("+trig_nets[2]+"), .A2("+trig_nets[3]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  nor2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1("+trig_nets[2]+"), .DIN2("+trig_nets[3]+") );\n"
                        new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
                    elif rare_values_of_trig_nets[3] == 1:
        #                new_lines[endmodule_idx-1] += "  INV_X1 U"+str(cnt)+ " ( .A("+trig_nets[3]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  hi1s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN("+trig_nets[3]+") );\n"
            #            new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
        #                new_lines[endmodule_idx-1] += "  NOR2_X1 U"+str(cnt)+ " ( .A1(tmp_"+str(cntt-1)+"), .A2("+trig_nets[2]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  nor2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1(tmp_"+str(cntt-1)+"), .DIN2("+trig_nets[2]+") );\n"
                        new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
                elif rare_values_of_trig_nets[2] == 1:
                    if rare_values_of_trig_nets[3] == 0:
        #                new_lines[endmodule_idx-1] += "  INV_X1 U"+str(cnt)+ " ( .A("+trig_nets[2]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  hi1s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN("+trig_nets[2]+") );\n"
            #            new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
        #                new_lines[endmodule_idx-1] += "  NOR2_X1 U"+str(cnt)+ " ( .A1(tmp_"+str(cntt-1)+"), .A2("+trig_nets[3]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  nor2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1(tmp_"+str(cntt-1)+"), .DIN2("+trig_nets[3]+") );\n"
                        new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
                    elif rare_values_of_trig_nets[3] == 1:
        #                new_lines[endmodule_idx-1] += "  AND2_X1 U"+str(cnt)+ " ( .A1("+trig_nets[2]+"), .A2("+trig_nets[3]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  and2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1("+trig_nets[2]+"), .DIN2("+trig_nets[3]+") );\n"
                        new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
                
                ### For 4 and 5
                if rare_values_of_trig_nets[4] == 0:
                    if rare_values_of_trig_nets[5] == 0:
            #            gt1 = "NOR2_X1"
        #                new_lines[endmodule_idx-1] += "  NOR2_X1 U"+str(cnt)+ " ( .A1("+trig_nets[4]+"), .A2("+trig_nets[5]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  nor2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1("+trig_nets[4]+"), .DIN2("+trig_nets[5]+") );\n"
                        new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
                    elif rare_values_of_trig_nets[5] == 1:
        #                new_lines[endmodule_idx-1] += "  INV_X1 U"+str(cnt)+ " ( .A("+trig_nets[5]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  hi1s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN("+trig_nets[5]+") );\n"
            #            new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
        #                new_lines[endmodule_idx-1] += "  NOR2_X1 U"+str(cnt)+ " ( .A1(tmp_"+str(cntt-1)+"), .A2("+trig_nets[4]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  nor2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1(tmp_"+str(cntt-1)+"), .DIN2("+trig_nets[4]+") );\n"
                        new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
                elif rare_values_of_trig_nets[4] == 1:
                    if rare_values_of_trig_nets[5] == 0:
        #                new_lines[endmodule_idx-1] += "  INV_X1 U"+str(cnt)+ " ( .A("+trig_nets[4]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  hi1s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN("+trig_nets[4]+") );\n"
            #            new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
        #                new_lines[endmodule_idx-1] += "  NOR2_X1 U"+str(cnt)+ " ( .A1(tmp_"+str(cntt-1)+"), .A2("+trig_nets[5]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  nor2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1(tmp_"+str(cntt-1)+"), .DIN2("+trig_nets[5]+") );\n"
                        new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
                    elif rare_values_of_trig_nets[5] == 1:
        #                new_lines[endmodule_idx-1] += "  AND2_X1 U"+str(cnt)+ " ( .A1("+trig_nets[4]+"), .A2("+trig_nets[5]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  and2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1("+trig_nets[4]+"), .DIN2("+trig_nets[5]+") );\n"
                        new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
                
                # For 6 and 7
                if rare_values_of_trig_nets[6] == 0:
                    if rare_values_of_trig_nets[7] == 0:
            #            gt1 = "NOR2_X1"
        #                new_lines[endmodule_idx-1] += "  NOR2_X1 U"+str(cnt)+ " ( .A1("+trig_nets[6]+"), .A2("+trig_nets[7]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  nor2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1("+trig_nets[6]+"), .DIN2("+trig_nets[7]+") );\n"
                        new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
                    elif rare_values_of_trig_nets[7] == 1:
        #                new_lines[endmodule_idx-1] += "  INV_X1 U"+str(cnt)+ " ( .A("+trig_nets[7]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  hi1s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN("+trig_nets[7]+") );\n"
            #            new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
        #                new_lines[endmodule_idx-1] += "  NOR2_X1 U"+str(cnt)+ " ( .A1(tmp_"+str(cntt-1)+"), .A2("+trig_nets[6]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  nor2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1(tmp_"+str(cntt-1)+"), .DIN2("+trig_nets[6]+") );\n"
                        new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
                elif rare_values_of_trig_nets[6] == 1:
                    if rare_values_of_trig_nets[7] == 0:
        #                new_lines[endmodule_idx-1] += "  INV_X1 U"+str(cnt)+ " ( .A("+trig_nets[6]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  hi1s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN("+trig_nets[6]+") );\n"
            #            new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
        #                new_lines[endmodule_idx-1] += "  NOR2_X1 U"+str(cnt)+ " ( .A1(tmp_"+str(cntt-1)+"), .A2("+trig_nets[7]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  nor2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1(tmp_"+str(cntt-1)+"), .DIN2("+trig_nets[7]+") );\n"
                        new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
                    elif rare_values_of_trig_nets[7] == 1:
        #                new_lines[endmodule_idx-1] += "  AND2_X1 U"+str(cnt)+ " ( .A1("+trig_nets[6]+"), .A2("+trig_nets[7]+"), .ZN(tmp_"+str(cntt)+") );\n"
                        new_lines[endmodule_idx-1] += "  and2s1 U"+str(cnt)+ " ( .Q(tmp_"+str(cntt)+ "), .DIN1("+trig_nets[6]+"), .DIN2("+trig_nets[7]+") );\n"
                        new_and_gates_nets.append(cntt)
                        add_to_wires.append("tmp_"+str(cntt))
                        cnt+=1
                        cntt+=1
                
            
            
        #    add_to_wires = []
        #    cnt = int(list(Components_Dict.keys())[-1].split("U")[-1]) + 1
        #    cntt = 0
        #    new_and_gates_nets = []
        #    for i in range(int(len(trig_nets)/2)):
        #    #    new_lines[endmodule_idx-1].append("  AND2_X1 U"+str(cnt)+ " ( .A1("+trig_nets[2*i]+"), .A2("+trig_nets[(2*i)+1]+"), .ZN(tmp_"+str(cntt)+") );\n")
        #        new_lines[endmodule_idx-1] += "  AND2_X1 U"+str(cnt)+ " ( .A1("+trig_nets[2*i]+"), .A2("+trig_nets[(2*i)+1]+"), .ZN(tmp_"+str(cntt)+") );\n"
        #        new_and_gates_nets.append(cntt)
        #        add_to_wires.append("tmp_"+str(cntt))
        #        cnt+=1
        #        cntt+=1
            if trig_width == 2:
                # To replace the target_net at the appropriate location with tmp_ target_net
                for key in Components_Dict:
        #            if Components_Dict[key][-1] == target_net:
                    if Components_Dict[key][1] == target_net:
                        renaming_gate = key
                        break
                for i in range(len(new_lines)):
                    if " "+ renaming_gate +" " in new_lines[i]:
                        new_lines[i] = new_lines[i].replace(target_net,"tmp_"+target_net)
                        break
                add_to_wires.append("tmp_"+target_net)
                
                #new_lines[endmodule_idx-1].append("  XOR2_X1 U"+str(cnt)+ " ( .A1(tmp_"+target_net+"), .A2(tmp_trig_en), .ZN("+target_net+") );\n") # adding the XOR gate, i.e., payload
        #        new_lines[endmodule_idx-1] += "  XOR2_X1 U"+str(cnt)+ " ( .A1(tmp_"+target_net+"), .A2(tmp_trig_en), .ZN("+target_net+") );\n"
        #        new_lines[endmodule_idx-1] += "  XOR2_X1 U"+str(cnt)+ " ( .A(tmp_"+target_net+"), .B(tmp_trig_en), .Z("+target_net+") );\n"
                new_lines[endmodule_idx-1] += "  xor2s1 U"+str(cnt)+ " ( .Q("+target_net+"), .DIN1(tmp_"+target_net+"), .DIN2(tmp_trig_en) );\n"
                #Adding the extra nets to wires
                for i in range(len(new_lines)):
                    if "wire" in new_lines[i] and "//" not in new_lines[i]:
                        break
                tmp = ''
                for j in range(len(add_to_wires)):
                    tmp+= add_to_wires[j]+", "
        #        new_lines[i] += "\t\t"+tmp + "\n"
                new_lines[i] = "wire " + tmp + new_lines[i][5:]
                
                
            elif trig_width == 4:
                #new_lines[endmodule_idx-1].append("  AND2_X1 U"+str(cnt)+ " ( .A1(tmp_"+new_and_gates_nets[0]+"), .A2(tmp_"+new_and_gates_nets[1]+"), .ZN(tmp_"+"trig_en"+") );\n")  # adding the final and gate to create the trigger signal
        #        new_lines[endmodule_idx-1] += "  AND2_X1 U"+str(cnt)+ " ( .A1(tmp_"+str(new_and_gates_nets[0])+"), .A2(tmp_"+str(new_and_gates_nets[1])+"), .ZN(tmp_"+"trig_en"+") );\n"
                new_lines[endmodule_idx-1] += "  and2s1 U"+str(cnt)+ " ( .Q(tmp_"+"trig_en"+"), .DIN1(tmp_"+str(new_and_gates_nets[0])+"), .DIN2(tmp_"+str(new_and_gates_nets[1])+") );\n"
                add_to_wires.append("tmp_trig_en")
                cnt+=1
                
                # To replace the target_net at the appropriate location with tmp_ target_net
                for key in Components_Dict:
        #            if Components_Dict[key][-1] == target_net:
                    if Components_Dict[key][1] == target_net:
                        renaming_gate = key
                        break
                for i in range(len(new_lines)):
                    if " "+ renaming_gate +" " in new_lines[i]:
                        new_lines[i] = new_lines[i].replace(target_net,"tmp_"+target_net)
                        break
                add_to_wires.append("tmp_"+target_net)
                
                #new_lines[endmodule_idx-1].append("  XOR2_X1 U"+str(cnt)+ " ( .A1(tmp_"+target_net+"), .A2(tmp_trig_en), .ZN("+target_net+") );\n") # adding the XOR gate, i.e., payload
        #        new_lines[endmodule_idx-1] += "  XOR2_X1 U"+str(cnt)+ " ( .A1(tmp_"+target_net+"), .A2(tmp_trig_en), .ZN("+target_net+") );\n"
        #        new_lines[endmodule_idx-1] += "  XOR2_X1 U"+str(cnt)+ " ( .A(tmp_"+target_net+"), .B(tmp_trig_en), .Z("+target_net+") );\n"
                new_lines[endmodule_idx-1] += "  xor2s1 U"+str(cnt)+ " ( .Q("+target_net+"), .DIN1(tmp_"+target_net+"), .DIN2(tmp_trig_en) );\n"
                #Adding the extra nets to wires
                for i in range(len(new_lines)):
                    if "wire" in new_lines[i] and "//" not in new_lines[i]:
                        break
                tmp = ''
                for j in range(len(add_to_wires)):
                    tmp+= add_to_wires[j]+", "
        #        new_lines[i] += "\t\t"+tmp + "\n"
                new_lines[i] = "wire " + tmp + new_lines[i][5:]
            
            
            elif trig_width in [6,10,12,14,16]:
                
                pins_str = ''
                for k in range(int(trig_width/2)):
                    pins_str += " .DIN"+str(k+1)+"(tmp_"+str(new_and_gates_nets[k])+"),"
                pins_str = pins_str[:-1]
                
        #        new_lines[endmodule_idx-1] += "  and2s1 U"+str(cnt)+ " ( .Q(tmp_"+"trig_en"+"), .DIN1(tmp_mid_trig_1), .DIN2(tmp_mid_trig_2) );\n"
                new_lines[endmodule_idx-1] += "  and"+str(int(trig_width/2))+"s1 U"+str(cnt)+ " ( .Q(tmp_"+"trig_en"+"),"+ pins_str + " );\n"
                add_to_wires.append("tmp_trig_en")
                cnt+=1
                
                # To replace the target_net at the appropriate location with tmp_ target_net
                for key in Components_Dict:
        #            if Components_Dict[key][-1] == target_net:
                    if Components_Dict[key][1] == target_net:
                        renaming_gate = key
                        break
                for i in range(len(new_lines)):
                    if " "+renaming_gate+" " in new_lines[i]:
                        new_lines[i] = new_lines[i].replace(target_net,"tmp_"+target_net)
                        break
                add_to_wires.append("tmp_"+target_net)
                
                #new_lines[endmodule_idx-1].append("  XOR2_X1 U"+str(cnt)+ " ( .A1(tmp_"+target_net+"), .A2(tmp_trig_en), .ZN("+target_net+") );\n") # adding the XOR gate, i.e., payload
        #        new_lines[endmodule_idx-1] += "  XOR2_X1 U"+str(cnt)+ " ( .A1(tmp_"+target_net+"), .A2(tmp_trig_en), .ZN("+target_net+") );\n"
                new_lines[endmodule_idx-1] += "  xor2s1 U"+str(cnt)+ " ( .Q("+target_net+"), .DIN1(tmp_"+target_net+"), .DIN2(tmp_trig_en) );\n"
                #Adding the extra nets to wires
                for i in range(len(new_lines)):
                    if "wire" in new_lines[i] and "//" not in new_lines[i]:
                        break
                tmp = ''
                for j in range(len(add_to_wires)):
                    tmp+= add_to_wires[j]+", "
        #        new_lines[i] += "\t\t"+tmp + "\n"
                new_lines[i] = "wire " + tmp + new_lines[i][5:]
                
                
            elif trig_width == 8:
                #new_lines[endmodule_idx-1].append("  AND2_X1 U"+str(cnt)+ " ( .A1(tmp_"+new_and_gates_nets[0]+"), .A2(tmp_"+new_and_gates_nets[1]+"), .ZN(tmp_"+"trig_en"+") );\n")  # adding the final and gate to create the trigger signal
        #        new_lines[endmodule_idx-1] += "  AND2_X1 U"+str(cnt)+ " ( .A1(tmp_"+str(new_and_gates_nets[0])+"), .A2(tmp_"+str(new_and_gates_nets[1])+"), .ZN(tmp_mid_"+"trig_1"+") );\n"
                new_lines[endmodule_idx-1] += "  and2s1 U"+str(cnt)+ " ( .Q(tmp_mid_"+"trig_1"+"), .DIN1(tmp_"+str(new_and_gates_nets[0])+"), .DIN2(tmp_"+str(new_and_gates_nets[1])+") );\n"
                add_to_wires.append("tmp_mid_trig_1")
                cnt+=1
                
        #        new_lines[endmodule_idx-1] += "  AND2_X1 U"+str(cnt)+ " ( .A1(tmp_"+str(new_and_gates_nets[2])+"), .A2(tmp_"+str(new_and_gates_nets[3])+"), .ZN(tmp_mid_"+"trig_2"+") );\n"
                new_lines[endmodule_idx-1] += "  and2s1 U"+str(cnt)+ " ( .Q(tmp_mid_"+"trig_2"+"), .DIN1(tmp_"+str(new_and_gates_nets[2])+"), .DIN2(tmp_"+str(new_and_gates_nets[3])+") );\n"
                add_to_wires.append("tmp_mid_trig_2")
                cnt+=1
                
        #        new_lines[endmodule_idx-1] += "  AND2_X1 U"+str(cnt)+ " ( .A1(tmp_mid_trig_1), .A2(tmp_mid_trig_2), .ZN(tmp_trig_en"+") );\n"
                new_lines[endmodule_idx-1] += "  and2s1 U"+str(cnt)+ " ( .Q(tmp_"+"trig_en"+"), .DIN1(tmp_mid_trig_1), .DIN2(tmp_mid_trig_2) );\n"
                add_to_wires.append("tmp_trig_en")
                cnt+=1
                
                
                # To replace the target_net at the appropriate location with tmp_ target_net
                for key in Components_Dict:
        #            if Components_Dict[key][-1] == target_net:
                    if Components_Dict[key][1] == target_net:
                        renaming_gate = key
                        break
                for i in range(len(new_lines)):
                    if " "+renaming_gate+" " in new_lines[i]:
                        new_lines[i] = new_lines[i].replace(target_net,"tmp_"+target_net)
                        break
                add_to_wires.append("tmp_"+target_net)
                
                #new_lines[endmodule_idx-1].append("  XOR2_X1 U"+str(cnt)+ " ( .A1(tmp_"+target_net+"), .A2(tmp_trig_en), .ZN("+target_net+") );\n") # adding the XOR gate, i.e., payload
        #        new_lines[endmodule_idx-1] += "  XOR2_X1 U"+str(cnt)+ " ( .A1(tmp_"+target_net+"), .A2(tmp_trig_en), .ZN("+target_net+") );\n"
                new_lines[endmodule_idx-1] += "  xor2s1 U"+str(cnt)+ " ( .Q("+target_net+"), .DIN1(tmp_"+target_net+"), .DIN2(tmp_trig_en) );\n"
                #Adding the extra nets to wires
                for i in range(len(new_lines)):
                    if "wire" in new_lines[i] and "//" not in new_lines[i]:
                        break
                tmp = ''
                for j in range(len(add_to_wires)):
                    tmp+= add_to_wires[j]+", "
        #        new_lines[i] += "\t\t"+tmp + "\n"
                new_lines[i] = "wire " + tmp + new_lines[i][5:]
                
            
            
        #    if not os.path.exists("../Trojan_inserted_netlists_width_"+str(trig_width)+"_thresh_"+str(thresh_low)+"/"):
        #        os.mkdir("../Trojan_inserted_netlists_width_"+str(trig_width)+"_thresh_"+str(thresh_low)+"/")
            
        #    if not os.path.exists("../Trojan_inserted_netlists_width_"+str(trig_width)+"_thresh_"+str(thresh_low)+"/"+v_file+"/"):
        #        os.mkdir("../Trojan_inserted_netlists_width_"+str(trig_width)+"_thresh_"+str(thresh_low)+"/"+v_file+"/")
            if not os.path.exists("../Trojan_inserted_netlists_width_"+str(trig_width)+"/"+v_file+"/"):
                os.mkdir("../Trojan_inserted_netlists_width_"+str(trig_width)+"/"+v_file+"/")
                
            open("../Trojan_inserted_netlists_width_"+str(trig_width)+"/"+v_file+"/"+v_file+"_T_"+str(n)+".v", 'w').writelines(new_lines)
        #    open("../Trojan_inserted_netlists_width_"+str(trig_width)+"_thresh_"+str(thresh_low)+"/"+v_file+"/"+v_file+"_T_"+str(n)+ ".v", 'w').writelines(new_lines)
            
            for gts in ['and2s1', 'nor2s1', 'xor2s1', 'hi1s1','and3s1','and4s1','and5s1','and6s1','and7s1','and8s1']:
                if gts not in libsp_gate_types:
                    libsp_gate_types.append(gts)
            sp_file = './lib/freepdk45_cells.sp'
            libsp_parser = LibSPParser(sp_file)
            libsp_parser.parse()
            for gt in libsp_gate_types:
                if gt not in libsp_parser.cell_dict:
                    libsp_parser.cell_dict[gt] = []
            
        #    with open("./Trojan_inserted_netlists_width_"+str(trig_width)+"/"+v_file+"/"+v_file+"_T_"+"{0:04}".format(n)+".v", 'r') as f:
        #    with open("../Trojan_inserted_netlists_width_"+str(trig_width)+"/"+v_file+"/T_"+str(n)+"/" + "T_"+str(n)+".v", 'r') as f:
        #        file_contents = f.read()
        #    file_contents = file_contents.replace("_X","X")
        #    with open("../Trojan_inserted_netlists_width_"+str(trig_width)+"/"+v_file+"/"+v_file+"_tmp_libsp_format.v", 'w') as f:
        #        f.write(file_contents)
            SAT_check_v_file = open("../Trojan_inserted_netlists_width_"+str(trig_width)+"/"+v_file+"/"+v_file+"_T_"+str(n)+ ".v", 'r').readlines()
        #    SAT_check_v_file = open("../Trojan_inserted_netlists_width_"+str(trig_width)+"_thresh_"+str(thresh_low)+"/"+v_file+"/"+v_file+"_T_"+str(n)+ ".v", 'r').readlines()
            cntt1 = 0
            clauses, net2int, int2net = verilog_to_sat(SAT_check_v_file, libsp_parser)
            base_clauses = copy.deepcopy(clauses)
            clauses.append([net2int["tmp_trig_en"]])
            answer = pycosat.solve(clauses)
            if answer == 'UNSAT':
        #        SAT.append(0)
                try_again = True
            else:
        #        SAT.append(1)
                try_again = False
        #    os.system("del "+ "../Trojan_inserted_netlists/"+v_file+"/"+v_file+"_T_"+"{0:04}".format(n)+"_libsp_format.v")
            
            if try_again == False:
                n+=1
            else:
                pass
        #    if nx.is_directed_acyclic_graph(v_file_to_graph("../Trojan_inserted_netlists/"+v_file+"/"+v_file+"_T_"+"{0:04}".format(n)+".v")):
        #        n+=1
        ###        pass
        #    else:
        ##        pass
        #        os.system("del "+ "../Trojan_inserted_netlists/"+v_file+"/"+v_file+"_T_"+"{0:04}".format(n)+".v")
            
