# -*- coding: utf-8 -*-
"""
Created on Sat Dec 11 19:19:29 2021

@author: gohil.vasudev
"""

'''
For analyzing the TGRL patterns for HD trend
'''

import numpy as np
#import matplotlib.pyplot as plt
from tqdm import tqdm
import networkx as nx
import pickle
import random, copy
import os
import time
from multiprocessing import Process, Lock, Value, Array, Queue, Manager
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
def BUF_X8(a):
    return a[0]
def BUF_X16(a):
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
def AND2_X4(a):
    return a[0]&a[1]
def OR2_X1(a):
    return a[0]|a[1]
def OR3_X1(a):
    return a[0]|a[1]|a[2]
def OR4_X1(a):
    return a[0]|a[1]|a[2]|a[3]
def OR2_X2(a):
    return a[0]|a[1]
def OR2_X4(a):
    return a[0]|a[1]
def NAND2_X1(a):
    return int(not(AND2_X1(a)))
def NAND3_X1(a):
    return int(not(AND3_X1(a)))
def NAND4_X1(a):
    return int(not(AND4_X1(a)))
def NAND2_X2(a):
    return int(not(AND2_X1(a)))
def NAND2_X4(a):
    return int(not(AND2_X4(a)))
def NOR2_X1(a):
    return int(not(OR2_X1(a)))
def NOR3_X1(a):
    return int(not(OR3_X1(a)))
def NOR4_X1(a):
    return int(not(OR4_X1(a)))
def NOR2_X2(a):
    return int(not(OR2_X1(a)))
def NOR2_X4(a):
    return int(not(OR2_X4(a)))
def XNOR2_X1(a):
    return int(not(XOR2_X1(a)))
def XNOR2_X2(a):
    return int(not(XOR2_X1(a)))
   
def HD_calculator(s1,s2):
    return sum(c1 != c2 for c1, c2 in zip(s1, s2))


def obtain_trigger_nets_from_v_file(file_contents,t_wid,n):
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
    
    target_net = None
    if v_file in ['mips','aes_final','mor1kx_final','gps_final','ibex_final']:
        xor_name = 'XOR'
    else:
        xor_name = 'xor2s1'
    for i in range(end_ln-5,end_ln):
        if ("tmp_trig_en" in lines[i]) and (xor_name in lines[i]):
            num_ports = lines[i].count(".")
            for j in range(num_ports):
                net_name = lines[i].split(" ")[j+3][lines[i].split(" ")[j+3].index("(")+1:lines[i].split(" ")[j+3].index(")")]
                if ("tmp_trig_en" not in net_name) and ("tmp_" in net_name):
                    target_net = net_name
    if target_net == None:
        print("Target net not found for " + str(n) + ". Please fix the code.")
        time.sleep(10)
    trig_nets = []
    for i in range(end_ln-20,end_ln):
        if ("tmp_" in lines[i]) and ("tmp_trig_en" not in lines[i]) and (target_net not in lines[i]):
            num_ports = lines[i].count(".")
            #Components_Dict[lines[i].split(" ")[1]] = [lines[i].split(" ")[0]]
            #pin_names = []
            for j in range(num_ports):
                #pin_names.append(lines[i].split(" ")[j+3][lines[i].split(" ")[j+3].index("(")+1:lines[i].split(" ")[j+3].index(")")])
                net_name = lines[i].split(" ")[j+3][lines[i].split(" ")[j+3].index("(")+1:lines[i].split(" ")[j+3].index(")")]
                if "tmp_" not in net_name:
                    trig_nets.append(net_name)
    if len(trig_nets) != t_wid:
        print("Number of trigger nets not " + str(t_wid) + " for " + str(n) + ". Please fix the code.")
        print(trig_nets)
        time.sleep(10)
    return trig_nets 


def fun(pid, idx_0, idx_1):
    with mutex:
        print("Entered pid " + str(pid))
    start_time = time.time()
    
    for k in range(idx_0,idx_1):
        inp_vec = red[k]
        
        coverage_info = np.zeros(len(rare_nets))
        
        values = {}
        for i in range(len(inputs)):
            values[inputs[i]] = int(inp_vec[i])
        
        if v_file in ['mips','aes_final','mor1kx_final','gps_final','ibex_final']:
            for node in top_sort_filtered:
                ips = Components_Dict[node][1:-1]
                op = Components_Dict[node][-1]
                values[op] = globals()[Components_Dict[node][0]]([values[i] for i in ips])
        else:
            for node in top_sort_filtered:
                ips = Components_Dict[node][2:]
                op = Components_Dict[node][1]
                values[op] = globals()[Components_Dict[node][0][:-1]]([values[i] for i in ips])
        
        for n in range(len(rare_nets)):
            if values[rare_nets[n]] == rare_values[n]:
                coverage_info[n] = 1
        
        master_list[pid].append(coverage_info)
    
    stop_time = time.time()
    with mutex:
        print("Runtime for pid " + str(pid) +" : ", stop_time - start_time, " seconds")
    

if __name__ == '__main__':
    
    global_start_time = time.time()
    v_file = os.environ['v_file'] #sys.argv[1]
    
    thresh_low = 0.1
    if v_file == 'mips':
        thresh_low = 0.0009
    if v_file == 'aes_final':
        thresh_low = 0.0072
    if v_file == 'mor1kx_final':
        thresh_low = 0.0001
    if v_file == 'gps_final':
        thresh_low = 0.004
    if v_file == 'ibex_final':
        thresh_low = 0.00001
    
    technique = os.environ['technique'] #sys.argv[2] #'TARMAC'
    
    Trojan_source = os.environ['trojan_source'] #'random'
    t_wid = int(os.environ['trigger_width']) #4
    
    already_present = False
    if technique in ["MERS","MERSh","MERSs"]:
        if os.path.exists("../final_test_patterns/MERS/"+v_file+"_"+technique+"_testing_pats_coverage_info.pickle"):
            already_present = True
    else:
        if technique == 'TGRL':
            if os.path.exists("../TGRL_testPatterns/"+v_file+"_testing_pats_coverage_info.pickle"):
                already_present = True
        elif technique == 'TARMAC':
            if os.path.exists("../TARMAC_test_patterns/"+v_file+"_testing_pats_coverage_info.pickle"):
                already_present = True
        elif technique == 'MERO':
            if os.path.exists("../MERO_patterns_for_journal/"+v_file+"/"+v_file+"_testing_pats_coverage_info.pickle"):
                already_present = True
        elif technique == 'GA_SAT':
            if os.path.exists("../GA_SAT_patterns_for_journal/"+v_file+"_testing_pats_coverage_info.pickle"):
                already_present = True
        elif technique == 'random_LT':
            if os.path.exists("../random_LT/"+v_file+"_testing_pats_coverage_info.pickle"):
                already_present = True
        elif technique == 'TetraMAX':
            if os.path.exists("../TetraMAX_patterns/"+v_file+"_testing_pats_coverage_info.pickle"):
                already_present = True
        elif technique == 'DETERRENT':
            if os.path.exists("../logs/"+v_file+"_testing_pats_coverage_info.pickle"):
                already_present = True
    
    if not already_present:
        if technique == 'TGRL':
            with open("../TGRL_testPatterns/"+v_file+"_N1000_0.1.txt", 'r') as f:
                lns = f.readlines()
                red = []
                for vec in lns:
                    if vec.split()[0] not in red:
                        red.append(vec.split()[0])
        elif technique == 'TARMAC':
            with open("../TARMAC_test_patterns/patterns_new_tech_parallel_saved_dict_"+v_file+"_all_TPs.pickle",'rb') as f:
                pats = pickle.load(f)
                red = pats
        elif technique == 'MERO':
            with open("../MERO_patterns_for_journal/"+v_file+"/MERO_reduced_pattern_set_N_1000_thresh_"+str(thresh_low)+"_"+v_file+".pickle",'rb') as f:
                red = pickle.load(f)
        elif technique == 'GA_SAT':
            with open("../GA_SAT_patterns_for_journal/"+v_file+"_GA_SAT.test", 'r') as f:
                lns = f.readlines()
                red = []
                for vec in lns:
                    if vec.split()[0] not in red:
                        red.append(vec.split()[0])
        elif technique == 'random_LT':
            with open("../random_LT/"+v_file+"_random_patterns.pickle",'rb') as f:
                red = pickle.load(f)
        elif technique == 'TetraMAX':
            with open("../TetraMAX_patterns/"+v_file+"_patterns.pickle",'rb') as f:
                red = pickle.load(f)
        elif technique == 'DETERRENT':
            log_name = None
            if v_file == 'c2670':
                log_name = "../logs/mask_all_rew_PPO_c2670_n_timesteps_2000000_lr_0.0003_max_steps_per_ep_43_dummyvecenv_sq_rew_pid_1_tp.pkl"
            elif v_file == 'c5315':
                log_name = "../logs/correct_mask_all_rew_PPO_c5315_n_timesteps_2000000_lr_0.0003_max_steps_per_ep_70_dummyvecenv_sq_rew_pid_1_tp.pkl"
            elif v_file == 'c6288':
                log_name = "../logs/mask_all_rew_PPO_c6288_n_timesteps_2000000_lr_0.0003_max_steps_per_ep_150_dummyvecenv_sq_rew_pid_1_tp.pkl"
            elif v_file == 'c7552':
                log_name = "../logs/correct_mask_all_rew_PPO_c7552_n_timesteps_5000000_lr_0.0003_max_steps_per_ep_100_dummyvecenv_sq_rew_pid_1_tp.pkl"
            with open(log_name,'rb') as f:
                red = pickle.load(f)
#        elif technique == 'TMAX':
#            with open("../final_test_patterns/TMAX/final_test_patterns_"+v_file,'r') as f:
#                lns = f.readlines()
#            red = []
#            for vec in lns:
#                if len(vec)>2:
#                    if vec.split()[0] not in red:
#                        red.append(vec.split()[0])
    
    with open("../original_files/"+v_file+".v", 'r') as f:
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
    
    gate_types = []
    Components_Dict = {}
    for i in range(wire_ln+1,end_ln):
        num_ports = lines[i].count(".")
        Components_Dict[lines[i].split(" ")[1]] = [lines[i].split(" ")[0]]
        if lines[i].split(" ")[0] not in gate_types:
            gate_types.append(lines[i].split(" ")[0])
        for j in range(num_ports):
            Components_Dict[lines[i].split(" ")[1]].append(lines[i].split(" ")[j+3][lines[i].split(" ")[j+3].index("(")+1:lines[i].split(" ")[j+3].index(")")])
    
    
    G = nx.DiGraph()
    G.add_nodes_from(inputs)
    G.add_nodes_from(outputs)
    G.add_nodes_from(wires)
    G.add_nodes_from(list(Components_Dict.keys()))
    
    for node in Components_Dict:
        if v_file in ['mips','aes_final','mor1kx_final','gps_final','ibex_final']:
            ips = Components_Dict[node][1:-1]
            output = Components_Dict[node][-1]
        else:
            ips = Components_Dict[node][2:]
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
    rare_nets = []
    tmp_nets_prob = {}
    rare_values = np.array([])
    thresh_high= 1-thresh_low
    for i in range(len(tmp)):
        if (tmp[i]<thresh_low) or (tmp[i]>thresh_high):
            rare_nets.append((wires+outputs)[i])
            tmp_nets_prob[(wires+outputs)[i]] = tmp[i]
            if tmp[i]<0.5:
                rare_values = np.append(rare_values,1)
            else:
                rare_values = np.append(rare_values,0)
    
    if v_file in ['ibex_final']:
        rare_nets = rare_nets[:1000]
        rare_values = rare_values[:1000]
    
    if v_file in ['aes_final','mor1kx_final','gps_final']:
        select_idcs = np.where( (tmp!=0) & (tmp!=1) & ( (tmp<thresh_low) | (tmp>thresh_high) ) )[0]
        rare_nets = []
        rare_values = np.array([])
        for i in select_idcs:
            rare_nets.append((wires+outputs)[i])
            if tmp[i]<0.5:
                rare_values = np.append(rare_values,1)
            else:
                rare_values = np.append(rare_values,0)
    
    print("For testing set patterns")
    
    if not already_present:
        total_N = len(red)
        runn_sum = 0
        jobs = []
        chunk_size = int(total_N/64)
        master_list = {}
        manager = Manager()
        for pid in range(64):
            master_list[pid] = manager.list()
        for pid in range(64):
            if pid <63:
                idx_0 = list(range(total_N))[(chunk_size*pid)]
                idx_1 = list(range(total_N))[(chunk_size*pid)+chunk_size]
            elif pid == 63:
                idx_0 = list(range(total_N))[(chunk_size*pid)]
                idx_1 = total_N
        
            jobs.append(Process(target=fun, args=(pid, idx_0, idx_1)))
        
        for j in jobs:
            j.start()
        for j in jobs:
            j.join()
        
        cntr = 0
        coverage_info = np.zeros((len(red),len(rare_nets)))
        for pid in range(64):
            for j in range(len(master_list[pid])):
                coverage_info[cntr] = master_list[pid][j]
                cntr+=1
             
        global_stop_time = time.time()
        print("Global Runtime: ", global_stop_time - global_start_time, " seconds")
        
        
        if technique == 'TGRL':
            with open("../TGRL_testPatterns/"+v_file+"_testing_pats_coverage_info.pickle",'wb') as f:
                pickle.dump(coverage_info,f)
        elif technique == 'TARMAC':
            with open("../TARMAC_test_patterns/"+v_file+"_testing_pats_coverage_info.pickle",'wb') as f:
                pickle.dump(coverage_info,f)
        elif technique == 'MERO':
            with open("../MERO_patterns_for_journal/"+v_file+"/"+v_file+"_testing_pats_coverage_info.pickle",'wb') as f:
                pickle.dump(coverage_info,f)
        elif technique == 'GA_SAT':
            with open("../GA_SAT_patterns_for_journal/"+v_file+"_testing_pats_coverage_info.pickle",'wb') as f:
                pickle.dump(coverage_info,f)
        elif technique == 'random_LT':
            with open("../random_LT/"+v_file+"_testing_pats_coverage_info.pickle",'wb') as f:
                pickle.dump(coverage_info,f)
        elif technique == 'TMAX':
            with open("../TetraMAX_patterns/"+v_file+"_testing_pats_coverage_info.pickle",'wb') as f:
                pickle.dump(coverage_info,f)
#        elif technique in ['MERS','MERSh','MERSs']:
#            with open("../final_test_patterns/MERS/"+v_file+"_"+technique+"_testing_pats_coverage_info.pickle",'wb') as f:
#                pickle.dump(coverage_info,f)
        elif technique == 'DETERRENT':
            with open("../logs/"+v_file+"_testing_pats_coverage_info.pickle",'wb') as f:
                pickle.dump(coverage_info,f)
                
    
    
    #%%%  Evaluating random/RL Trojans
    
    if technique == 'TGRL':
        with open("../TGRL_testPatterns/"+v_file+"_testing_pats_coverage_info.pickle",'rb') as f:
            coverage_info = pickle.load(f)
    elif technique == 'TARMAC':
        with open("../TARMAC_test_patterns/"+v_file+"_testing_pats_coverage_info.pickle",'rb') as f:
            coverage_info = pickle.load(f)
    elif technique == 'MERO':
        with open("../MERO_patterns_for_journal/"+v_file+"/"+v_file+"_testing_pats_coverage_info.pickle",'rb') as f:
            coverage_info = pickle.load(f)
    elif technique == 'GA_SAT':
        with open("../GA_SAT_patterns_for_journal/"+v_file+"_testing_pats_coverage_info.pickle",'rb') as f:
            coverage_info = pickle.load(f)
    elif technique == 'random_LT':
        with open("../random_LT/"+v_file+"_testing_pats_coverage_info.pickle",'rb') as f:
            coverage_info = pickle.load(f)
    elif technique == 'TMAX':
        with open("../TetraMAX_patterns/"+v_file+"_testing_pats_coverage_info.pickle",'rb') as f:
            coverage_info = pickle.load(f)
#    elif technique in ['MERS','MERSh','MERSs']:
#        with open("../final_test_patterns/MERS/"+v_file+"_"+technique+"_testing_pats_coverage_info.pickle",'rb') as f:
#            coverage_info = pickle.load(f)
    elif technique == 'DETERRENT':
        with open("../logs/"+v_file+"_testing_pats_coverage_info.pickle",'rb') as f:
            coverage_info = pickle.load(f)
            
    
    log_name = ''
    print("Technique: " + technique)
    #num_pats_to_constrain = 500
    #coverage_info = coverage_info[:min(len(coverage_info),num_pats_to_constrain),:]
    print("Num_pats: " +str(len(coverage_info)))
    print("Benchmark: " + v_file)
    
    if Trojan_source == 'random':
        if not os.path.exists("../Trojan_inserted_netlists_width_"+str(t_wid)+"/"+v_file+"/random_Trojans_trigger_nets.pickle"):
            trigger_nets = []
            for n in range(100):
                if v_file == 'mips':
                    with open("../Trojan_inserted_netlists_width_"+str(t_wid)+"/"+v_file+"/T_"+str(n)+"/T_"+str(n)+".v",'r') as f:
                        file_contents = f.read()
                else:
                    with open("../Trojan_inserted_netlists_width_"+str(t_wid)+"/"+v_file+"/"+v_file+"_T_"+str(n)+".v",'r') as f:
                        file_contents = f.read()
                trig_nets = obtain_trigger_nets_from_v_file(file_contents,t_wid,n)
                trigger_nets.append(trig_nets)
            with open("../Trojan_inserted_netlists_width_"+str(t_wid)+"/"+v_file+"/random_Trojans_trigger_nets.pickle",'wb') as f:
                pickle.dump(trigger_nets,f)
        else:
            with open("../Trojan_inserted_netlists_width_"+str(t_wid)+"/"+v_file+"/random_Trojans_trigger_nets.pickle",'rb') as f:
                trigger_nets = pickle.load(f)
    else:
        print("ERROR! Please enter the correct Trojan source. Only random Trojans can be evaluated.")
    
    if len(trigger_nets)<100:
        print("Total number of Trojans: " + str(len(trigger_nets)))
        num_troj = len(trigger_nets)
    else:
        print("Total number of Trojans: 100")
        num_troj = 100
    trigger_activation_rate = 0
    for n in range(num_troj):
        idcs = [rare_nets.index(trigger_nets[n][i]) for i in range(len(trigger_nets[n]))]
        coverage_selected_nets = coverage_info[:,idcs]
        if np.any(np.all(coverage_selected_nets,axis=1)):
            print("For " + str(n)+ " trigger activated!")
            trigger_activation_rate+=1
    print("Trigger activation rate: " + str(int(trigger_activation_rate*100/num_troj)) + "%")
    print("Attack success rate: " + str(100- int(trigger_activation_rate*100/num_troj))+"%")