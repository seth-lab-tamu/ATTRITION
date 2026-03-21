# -*- coding: utf-8 -*-
"""
Created on Wed Nov 10 02:04:43 2021

@author: gohil.vasudev
"""

'''
This script is for evaluating different patterns on TGRL benchmarks, i.e., TRIT-TC designs
'''

import networkx as nx
import random
import time
import numpy as np
import pickle
from tqdm import tqdm
from multiprocessing import Process, Lock, Value, Array
import sys
import os
mutex = Lock()

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
def and6s(a):
    return a[0]&a[1]&a[2]&a[3]&a[4]&a[5]
def and7s(a):
    return a[0]&a[1]&a[2]&a[3]&a[4]&a[5]&a[6]
def and8s(a):
    return a[0]&a[1]&a[2]&a[3]&a[4]&a[5]&a[6]&a[7]
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

def BUF_X1(a):
    return a[0]
def BUF_X2(a):
    return a[0]
def BUF_X4(a):
    return a[0]
def INV_X1(a):
    return int(abs(1-a[0]))
def INV_X2(a):
    return int(abs(1-a[0]))
def INV_X4(a):
    return int(abs(1-a[0]))
def INV_X8(a):
    return int(abs(1-a[0]))
def XOR2_X1(a):
    return a[0]^a[1]
def XOR2_X2(a):
    return a[0]^a[1]
def AND2_X1(a):
    return a[0]&a[1]
def AND3_X1(a):
    return a[0]&a[1]&a[2]
def AND4_X1(a):
    return a[0]&a[1]&a[2]&a[3]
def AND2_X2(a):
    return a[0]&a[1]
def OR2_X1(a):
    return a[0]|a[1]
def OR3_X1(a):
    return a[0]|a[1]|a[2]
def OR4_X1(a):
    return a[0]|a[1]|a[2]|a[3]
def OR2_X2(a):
    return a[0]|a[1]
def NAND2_X1(a):
    return int(not(AND2_X1(a)))
def NAND3_X1(a):
    return int(not(AND3_X1(a)))
def NAND4_X1(a):
    return int(not(AND4_X1(a)))
def NAND2_X2(a):
    return int(not(AND2_X1(a)))
def NOR2_X1(a):
    return int(not(OR2_X1(a)))
def NOR3_X1(a):
    return int(not(OR3_X1(a)))
def NOR4_X1(a):
    return int(not(OR4_X1(a)))
def NOR2_X2(a):
    return int(not(OR2_X1(a)))
def XNOR2_X1(a):
    return int(not(XOR2_X1(a)))
def XNOR2_X2(a):
    return int(not(XOR2_X1(a)))


def func(n,orig_data,red,t_wid):
    if v_file == 'mips':
        with open("../Trojan_inserted_netlists_width_"+str(t_wid)+"/"+v_file+"/T_"+str(n)+"/T_"+str(n)+".v", 'r') as f:
            file_contents = f.read()
    else:
        with open("../Trojan_inserted_netlists_width_"+str(t_wid)+"/"+v_file+"/"+v_file+"_T_"+str(n)+".v", 'r') as f:
            file_contents = f.read()
    #    with open("../del/"+v_file+"_no_line_breaks/"+v_file.split("_")[0]+"/"+v_file.split("_")[0]+"_T"+"{0:03}".format(n)+".v", 'r') as f:
    #        file_contents = f.read()

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


    G = nx.DiGraph()
    G.add_nodes_from(inputs)
    G.add_nodes_from(outputs)
    G.add_nodes_from(wires)
    G.add_nodes_from(list(Components_Dict.keys()))

    for node in Components_Dict:
        if v_file == 'mips':
            ips = Components_Dict[node][1:-1]
        else:
            ips = Components_Dict[node][2:]
        if v_file == 'mips':
            output = Components_Dict[node][-1]
        else:
            output = Components_Dict[node][1]
        for i in ips:
            G.add_edge(i,node)
        G.add_edge(node,output)

    top_sort = nx.topological_sort(G)
    top_sort_filtered = []
    for node in top_sort:
        if node in Components_Dict:
            top_sort_filtered.append(node)

    print("For Trojan netlist number "+str(n))
    data = np.zeros((len(red),len(outputs)))
    trig_data = np.zeros((len(red),1))
    for k in range(len(red)):
    #    if k%1000 == 0:
    #        print(k)
        inp_vec = red[k]
#            for i in range(len(new_c6288[0])):
#                inp_vec+=str(int(new_c6288[k][i]))
    #    inp_vec = ''.join(random.choice('01') for i in range(len(inputs)))

    #    for i in range(len(inputs)):
    #        inp_vec += str(random.randint(0,1))
        values = {}
        for i in range(len(inputs)):
            values[inputs[i]] = int(inp_vec[i])

        for node in top_sort_filtered:
#            if node in inputs:
#                pass
#            elif node in Components_Dict:
            if v_file == 'mips':
                ips = Components_Dict[node][1:-1]
                op = Components_Dict[node][-1]
                values[op] = globals()[Components_Dict[node][0]]([values[i] for i in ips])
            else:
                ips = Components_Dict[node][2:]
                op = Components_Dict[node][1]
                values[op] = globals()[Components_Dict[node][0][:-1]]([values[i] for i in ips])
#                if v_file == 'mips':
#                    op = Components_Dict[node][-1]
#                else:
#                    op = Components_Dict[node][1]
#                if v_file == 'mips':
#                    values[op] = globals()[Components_Dict[node][0]]([values[i] for i in ips])
#                else:
#                    #values[op] = locals()[Components_Dict[node][0][:-1]]([values[i] for i in ips])
#                    values[op] = globals()[Components_Dict[node][0][:-1]]([values[i] for i in ips])

    #    if len(inputs)+len(output)+len(wires) != len(values):
    #        print("Mismatch in simulation!!")
        data[k] = [values[o] for o in outputs]
        trig_data[k] = values['tmp_trig_en']
#        trig_data[k] = values['Trigger_en'+str(n)+'_0']


    #pats_that_trigerred[n] = np.where(trig_data==1)[0]
    if not os.path.exists("../for_plots/"+v_file+"/"):
        os.mkdir("../for_plots/"+v_file+"/")
    #with open("../for_plots/"+v_file+"/"+technique+"_trig_data_T_"+str(n)+".pickle",'wb') as f:
    with open("../for_plots/"+v_file+"/correct_"+technique+"_trig_data_T_"+str(n)+".pickle",'wb') as f:  # For c7552 only
        pickle.dump(trig_data,f)


    #%% For comparing and checking if the there is any mismatch, i.e., if the Trojan can be detected

    # For trigger coverage
    if np.any(np.array(trig_data)):
        with mutex:
            print("For " + str(n)+ " trigger activated!")
        #trig_indicator.append(1)
    else:
        pass
        #trig_indicator.append(0)

    # For trojan detection
    check = np.array(data) == np.array(orig_data)
    if np.all(check):
        #detection_indicator.append(0)
        pass
    else:
        idcs,_ = np.where(check == False)
        with mutex:
            print("For " + str(n) + " Trojan detected!")
        #detection_indicator.append(1)



#v_file = 'c2670'
v_file = 'c7552' #sys.argv[1] #'c5315'
tech = 'TrojRL' #sys.argv[2]
t_wid = 4 #int(sys.argv[3])
#v_file = 'c6288'
#v_file = 'c7552'
start_time = time.time()
for technique in [tech]: #['TGRL']: #['TrojRL']: #['TGRL']:

    if technique == 'TGRL':
        with open("../TGRL_testPatterns/"+v_file+"_N1000_0.1.txt", 'r') as f:
            lns = f.readlines()
            red = []
            for vec in lns:
                if vec.split()[0] not in red:
                    red.append(vec.split()[0])
    elif technique == 'TrojRL':
#        with open("../logs/mask_eoe_rew_PPO_c2670_n_timesteps_2000000_lr_0.0003_max_steps_per_ep_43_dummyvecenv_sq_rew_pid_1_tp.pkl",'rb') as f:
        #with open("../logs/mask_eoe_rew_PPO_c5315_n_timesteps_2000000_lr_0.0003_max_steps_per_ep_75_dummyvecenv_sq_rew_pid_1_tp.pkl",'rb') as f:
        #with open("../logs/mask_eoe_rew_PPO_c5315_n_timesteps_2000000_lr_0.0003_max_steps_per_ep_75_dummyvecenv_sq_rew_pid_1_tp_1116_pats.pkl",'rb') as f:
        #with open("../logs/master_log_tp.pkl",'rb') as f:   # this master_log is for c5315
        #with open("../logs/mask_all_rew_PPO_c2670_n_timesteps_2000000_lr_0.0003_max_steps_per_ep_43_dummyvecenv_sq_rew_pid_1_tp.pkl",'rb') as f:
        #with open("../logs/mask_all_rew_PPO_c6288_n_timesteps_2000000_lr_0.0003_max_steps_per_ep_150_dummyvecenv_sq_rew_pid_1_tp.pkl",'rb') as f:
        #with open("../logs/mask_eoe_rew_PPO_c7552_n_timesteps_5000000_lr_0.0003_max_steps_per_ep_100_dummyvecenv_sq_rew_pid_1_tp.pkl",'rb') as f:
        #with open("../logs/mask_all_rew_PPO_c5315_n_timesteps_2000000_lr_0.0003_max_steps_per_ep_70_dummyvecenv_sq_rew_pid_1_tp.pkl",'rb') as f:
        #with open("../logs/mask_eoe_rew_PPO_c7552_n_timesteps_5000000_lr_0.0003_max_steps_per_ep_100_dummyvecenv_sq_rew_pid_1_tp.pkl",'rb') as f:
        with open("../logs/correct_mask_all_rew_PPO_c7552_n_timesteps_5000000_lr_0.0003_max_steps_per_ep_100_dummyvecenv_sq_rew_pid_1_tp.pkl",'rb') as f:
        #with open("../logs/mask_all_rew_PPO_c6288_n_timesteps_2000000_lr_0.0003_max_steps_per_ep_150_dummyvecenv_sq_rew_pid_1_tp.pkl",'rb') as f:
#        with open("../logs/mask_eoe_rew_PPO_c2670_n_timesteps_2000000_lr_0.0003_max_steps_per_ep_43_ent_coef_0.5_dummyvecenv_sq_rew_pid_1_tp.pkl",'rb') as f:
        #with open("../logs/mask_eoe_rew_PPO_c6288_n_timesteps_2000000_lr_0.0003_max_steps_per_ep_150_dummyvecenv_sq_rew_pid_1_tp.pkl",'rb') as f:
        #with open("../logs/mask_all_rew_PPO_s13207_n_timesteps_5000000_lr_0.0003_max_steps_per_ep_185_dummyvecenv_sq_rew_pid_1_tp.pkl",'rb') as f:
        #with open("../logs/mask_all_rew_PPO_s15850_n_timesteps_5000000_lr_0.0003_max_steps_per_ep_225_dummyvecenv_sq_rew_pid_1_tp.pkl",'rb') as f:
        #with open("../logs/mask_all_rew_PPO_s35932_n_timesteps_5000000_lr_0.0003_max_steps_per_ep_300_dummyvecenv_sq_rew_pid_1_tp.pkl",'rb') as f:
            red = pickle.load(f)
    elif technique == 'TARMAC':
        with open("../TARMAC_test_patterns/patterns_new_tech_parallel_saved_dict_"+v_file+"_all_TPs.pickle", 'rb') as f:
            pats = pickle.load(f)
            red = []
            for vec in pats:
                red.append(''.join(str(int(vec[i])) for i in range(len(vec))))
    elif technique == 'TetraMAX':
        with open("../TetraMAX_patterns/"+v_file+"_patterns.pickle",'rb') as f:
            red = pickle.load(f)

    print("Technique: " + technique)
    print("Benchmark: " + v_file)
    print("Number of test patterns: " + str(len(red)))
    #%% For original netlist
#    red = []
#    for vec in lns:
#        if vec.split()[0] not in red:
#            red.append(vec.split()[0])


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


    G = nx.DiGraph()
    G.add_nodes_from(inputs)
    G.add_nodes_from(outputs)
    G.add_nodes_from(wires)
    G.add_nodes_from(list(Components_Dict.keys()))

    for node in Components_Dict:
        if v_file == 'mips':
            ips = Components_Dict[node][1:-1]
        else:
            ips = Components_Dict[node][2:]
        if v_file == 'mips':
            output = Components_Dict[node][-1]
        else:
            output = Components_Dict[node][1]
        for i in ips:
            G.add_edge(i,node)
        G.add_edge(node,output)

    top_sort = nx.topological_sort(G)
    top_sort_filtered = []
    for node in top_sort:
        if node in Components_Dict:
            top_sort_filtered.append(node)

    cov = []
    with open("../saved_simulations/"+v_file+"_tmp.pickle",'rb') as f:
        tmp = pickle.load(f)
    nets_w_prob_less_than_thresh = []
    tmp_nets_prob = {}
    rare_values = np.array([])
    for i in range(len(tmp)):
        if tmp[i]<0.1 or (tmp[i]>0.9):
            nets_w_prob_less_than_thresh.append((wires+outputs)[i])
            tmp_nets_prob[(wires+outputs)[i]] = tmp[i]
            if tmp[i]<0.5:
                rare_values = np.append(rare_values,1)
            else:
                rare_values = np.append(rare_values,0)

    print("For original netlist")
    orig_data = np.zeros((len(red),len(outputs)))
    for k in range(len(red)):
    #    if k%1000 == 0:
    #        print(k)
        inp_vec = red[k]
#        for i in range(len(new_c6288[0])):
#            inp_vec+=str(int(new_c6288[k][i]))
    #    inp_vec = ''.join(random.choice('01') for i in range(len(inputs)))

    #    for i in range(len(inputs)):
    #        inp_vec += str(random.randint(0,1))
        values = {}
        for i in range(len(inputs)):
            values[inputs[i]] = int(inp_vec[i])

        for node in top_sort_filtered:
#            if node in inputs:
#                pass
#            elif node in Components_Dict:
            if v_file == 'mips':
                ips = Components_Dict[node][1:-1]
                op = Components_Dict[node][-1]
                values[op] = locals()[Components_Dict[node][0]]([values[i] for i in ips])
            else:
                ips = Components_Dict[node][2:]
                op = Components_Dict[node][1]
                values[op] = locals()[Components_Dict[node][0][:-1]]([values[i] for i in ips])
#                if v_file == 'mips':
#                    op = Components_Dict[node][-1]
#                else:
#                    op = Components_Dict[node][1]
#                if v_file == 'mips':
#                    values[op] = locals()[Components_Dict[node][0]]([values[i] for i in ips])
#                else:
#                    values[op] = locals()[Components_Dict[node][0][:-1]]([values[i] for i in ips])

        cov_cnt = 0
        for n in range(len(nets_w_prob_less_than_thresh)):
            if values[nets_w_prob_less_than_thresh[n]] == rare_values[n]:
                cov_cnt+=1
        cov.append(cov_cnt)

    #    if len(inputs)+len(output)+len(wires) != len(values):
    #        print("Mismatch in simulation!!")
        orig_data[k] = [values[o] for o in outputs]


    #%% For Trojan netlist

    #detection_indicator = []
    #trig_indicator = []
    #n = 0
    #v_file = 'c6288_TRIT'
    #v_file = 'c6288_syn'
    #v_file = 'c5315_renamed'
    #pats_that_trigerred = {}

    jobs = []
    for n in range(100):

        jobs.append(Process(target=func,args=(n,orig_data,red,t_wid)))

    for j in jobs:
        j.start()
    for j in jobs:
        j.join()

    total_time_multi = time.time() - start_time
    #print("Took "+ str(total_time_multi) +"s for " + v_file)
    print(f"Took {total_time_multi:.2f}s for {v_file}")

#        with open("./random_Trojans/"+v_file+"/"+v_file+"_T_"+"{0:04}".format(n)+".v", 'r') as f:
#            file_contents = f.read()
#        if v_file == 'c6288':
#            with open("./Trojan_inserted_netlists_width_8/"+v_file+"_110_rare/"+v_file+"_110_rare_T_"+"{0:04}".format(n)+".v", 'r') as f:
#                file_contents = f.read()
#        elif v_file == 'c2670' or v_file == 'c5315' or v_file == 'c7552':
#            with open("./Trojan_inserted_netlists_width_8/"+v_file+"_modified/"+v_file+"_modified_T_"+"{0:04}".format(n)+".v", 'r') as f:
#                file_contents = f.read()
#        else:
#        with open("./random_Trojans/"+v_file+"/"+v_file+"_T_"+"{0:04}".format(n)+".v", 'r') as f:
#        with open("./TRIT-TC/"+v_file+"_T"+"{0:03}".format(n)+"/"+v_file+"_T"+"{0:03}".format(n)+".v", 'r') as f:


#    print("sum(trig_indicator): ", sum(trig_indicator))
#    print("sum(detection_indicator): ", sum(detection_indicator))
#
#    print(np.min(cov))
#    print(np.average(cov))
#    print(np.max(cov))
#    with open("../results/"+v_file+"_"+technique+".txt",'w') as f:
#        f.write("sum(trig_indicator): " + str(sum(trig_indicator)) +"\n")
#        f.write("sum(detection_indicator): " + str(sum(detection_indicator))+"\n")
#        f.write('trig_indicator: ')
#        f.write(str(trig_indicator) +"\n")
#        f.write('detection_indicator: ')
#        f.write(str(detection_indicator)+"\n")
#
