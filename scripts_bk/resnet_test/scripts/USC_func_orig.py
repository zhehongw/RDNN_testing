import os
from numpy import arange
import bisect
from decimal import *
import numpy
import math
from scipy import stats as scistats
import csv
from scipy.ndimage.filters import correlate as convolveim
import copy

import architecture as arch

def bindigits(n, bits):
    s = bin(int(n) & int("1"*bits, 2))[2:]
    return ("{0:0>%s}" % (bits)).format(s)

#constants
def USB_init_constant():
    arch.USB_inst_file.write('11' + '000010' + '010000' + '011111' + '111000' + '010000' + '\n') #RRAM_SD
    arch.USB_inst_file.write('11' + '000011' + '00000000' + '00001000' + '01000100' + '\n') #PRS0, PRL0
    arch.USB_inst_file.write('11' + '000100' + '00001111' + '01000100' + '00001111' + '\n') #PRS1, PSL1, PSS1
    arch.USB_inst_file.write('11' + '000101' + '00000000' + '00000000' + '00000000' + '\n') #PRS2, PSL2, PSS2
    arch.USB_inst_file.write('11' + '000110' + '00000000' + '00000000' + '00000000' + '\n') #PRS3, PSL3, PSS3
    arch.USB_inst_file.write('11' + '000111' + '00000000' + '00000000' + '00000000' + '\n') #PRS4, PSL4, PSS4
    arch.USB_inst_file.write('11' + '001000' + '00000000' + '00000000' + '00000000' + '\n') #PRS5, PSL5, PSS5
    arch.USB_inst_file.write('11' + '001001' + '00000000' + '00000000' + '00000000' + '\n') #PRS6, PSL6, PSS6
    arch.USB_inst_file.write('11' + '001010' + '00000000' + '00000000' + '00000000' + '\n') #PRS7, PSL7, PSS7
    arch.USB_inst_file.write('11' + '001100' + '0000000000000000' + '0010' + '0001' + '\n') #p_div, core_div
    arch.USB_inst_file.write('11' + '001011' + '000000000000000010010000' + '\n') #core RO
    arch.USB_inst_file.write('11' + '001101' + '000000000000000000000001' + '\n') #internal clock sel
    arch.USB_inst_file.write('11' + '001110' + '000000000000000000000' + '1' + bindigits(arch.rram_mode,2) + '\n') #RRAM MODE, form, mode

    arch.USB_inst_file.write('11' + '010111' + '000' + '0000000000000000' + bindigits(3,5) + '\n') #VREF_TUNE
    arch.USB_inst_file.write('11' + '010111' + '001' + '0000000000000000' + bindigits(9,5) + '\n') #VREF_TUNE
    arch.USB_inst_file.write('11' + '010111' + '010' + '0000000000000000' + bindigits(13,5) + '\n') #VREF_TUNE
    arch.USB_inst_file.write('11' + '010111' + '011' + '0000000000000000' + bindigits(17,5) + '\n') #VREF_TUNE
    arch.USB_inst_file.write('11' + '010111' + '100' + '0000000000000000' + bindigits(21,5) + '\n') #VREF_TUNE
    arch.USB_inst_file.write('11' + '010111' + '101' + '0000000000000000' + bindigits(25,5) + '\n') #VREF_TUNE
    arch.USB_inst_file.write('11' + '010111' + '110' + '0000000000000000' + bindigits(29,5) + '\n') #VREF_TUNE
    arch.USB_inst_file.write('11' + '011000' + '000000000000000000000000' + '\n') #ref sel
    arch.USB_inst_file.write('11' + '011001' + '000000000000000000000011' + '\n') #ref I out sel

def USB_dummy_long():
    for i in range(0, 100000000):
        arch.USB_inst_file.write('11' + '000011' + '00000000' + '00000001' + '00000010' + '\n') #PRL0, PRS0

def USB_dummy_short():
    for i in range(0, 1024):
        arch.USB_inst_file.write('11' + '000011' + '00000000' + '00000001' + '00000010' + '\n') #PRL0, PRS0

def USB_init_pe_idx_pe(pe_idx):
    arch.USB_inst_file.write('11' + '010000' + '0000000000000' + '1' + bindigits(pe_idx, 5) + bindigits(pe_idx, 5) + '\n') #pe idx

def USB_init_pe_idx_all():
    for pe_idx in range(0, arch.num_pe):
        USB_init_pe_idx_pe(pe_idx)

def USB_init_pe_inst_all(inst_begin_list, inst_end_list):
    for pe_idx in range(0, arch.num_pe):
        arch.USB_inst_file.write('11' + '010100' + '0000000' + '1' + bindigits(inst_begin_list[pe_idx], 10) + '0' + bindigits(pe_idx, 5) + '\n') #pe idx
        arch.USB_inst_file.write('11' + '010100' + '0000000' + '1' + bindigits(inst_end_list[pe_idx], 10) + '1' + bindigits(pe_idx, 5) + '\n') #pe idx

def USB_init_w_huffman_table_pe(pe_idx):
    w_huff_cnt = 0 
    w_table_file = open('../pe_' + str(pe_idx) + '_weight_table.txt', 'r')
    for line in w_table_file:
        line = line[:-1]
        #line_reverse = line[::-1]
        arch.USB_inst_file.write('11' + '010001' + '1' + '00000000' + line + '\n') #data
        arch.USB_inst_file.write('11' + '010001' + '0' + '00000000' + bindigits(pe_idx, 5) + '1' + bindigits(w_huff_cnt, 9) + '\n') #addr
        w_huff_cnt = w_huff_cnt + 1

def USB_init_w_huffman_all():
    for pe_idx in range(0, arch.num_pe):
        USB_init_w_huffman_table_pe(pe_idx)

def USB_init_w_huffman_shared():
    w_huff_cnt = 0 
    w_table_file = open('../pe_' + str(0) + '_weight_table.txt', 'r')
    for line in w_table_file:
        line = line[:-1]
        #line_reverse = line[::-1]
        arch.USB_inst_file.write('11' + '010001' + '1' + '00000000' + line + '\n') #data
        arch.USB_inst_file.write('11' + '010001' + '0' + '00000000' + bindigits(20, 5) + '1' + bindigits(w_huff_cnt, 9) + '\n') #addr
        w_huff_cnt = w_huff_cnt + 1

def USB_init_loc_huffman_table_pe(pe_idx):
    loc_huff_cnt = 0 
    runlength_table_file = open('../pe_' + str(pe_idx) + '_runlength_table.txt', 'r')
    for line in runlength_table_file:
        line = line[:-1]
        #line_reverse = line[::-1]
        arch.USB_inst_file.write('11' + '010010' + '1' + '00000000' + line + '\n') #data
        arch.USB_inst_file.write('11' + '010010' + '0' + '00000000' + bindigits(pe_idx, 5) + '1' + bindigits(loc_huff_cnt, 9) + '\n') #addr
        loc_huff_cnt = loc_huff_cnt + 1

def USB_init_loc_huffman_all():
    for pe_idx in range(0, arch.num_pe):
        USB_init_loc_huffman_table_pe(pe_idx)

def USB_init_loc_huffman_shared():
    loc_huff_cnt = 0 
    runlength_table_file = open('../pe_' + str(0) + '_runlength_table.txt', 'r')
    for line in runlength_table_file:
        line = line[:-1]
        #line_reverse = line[::-1]
        arch.USB_inst_file.write('11' + '010010' + '1' + '00000000' + line + '\n') #data
        arch.USB_inst_file.write('11' + '010010' + '0' + '00000000' + bindigits(20, 5) + '1' + bindigits(loc_huff_cnt, 9) + '\n') #addr
        loc_huff_cnt = loc_huff_cnt + 1

def USB_init_icache_pe(pe_idx):
    CNN_icache_cnt = 0
    for line in arch.inst_list[pe_idx]:
        #line = line[:-1]
        #inst_word = '{message:>256{fill}}'.format(message=line, fill='').replace(' ', '0')
        #write control 0
        arch.USB_inst_file.write('11' + '000000' + '110' + '000' + '000' + bindigits(CNN_icache_cnt, 10) + bindigits(pe_idx, 5) + '\n') #KEYPOINT_THRESHOLD
        line_reverse = line[::-1]
        #print line_reverse
        for i in range(0, 9):
            if(i < 8): 
                #print line_reverse[i*30:i*30+30][::-1]
                arch.USB_inst_file.write('10' + str(line_reverse[i*30:i*30+30][::-1]) + '\n') 
            else:
                #print line_reverse[i*30:i*30+16][::-1]
                arch.USB_inst_file.write('10' + '0'*14 + str(line_reverse[i*30:i*30+16][::-1]) + '\n') 
        CNN_icache_cnt = CNN_icache_cnt + 1

def USB_init_icache_all():
    for pe_idx in range(0, arch.num_pe):
        USB_init_icache_pe(pe_idx)

def USB_init_icache_pe_from_file(pe_idx):
    CNN_icache_cnt = 0
    with open(str('../inst_golden/pe_' + str(pe_idx) + '_inst.txt')) as inst_file:
        for line in inst_file:
            #print line
            line = line[:-1]
            #print line
            #inst_word = '{message:>256{fill}}'.format(message=line, fill='').replace(' ', '0')
            #write control 0
            arch.USB_inst_file.write('11' + '000000' + '110' + '000' + '000' + bindigits(CNN_icache_cnt, 10) + bindigits(pe_idx, 5) + '\n') #KEYPOINT_THRESHOLD
            line_reverse = line[::-1]
            #print line_reverse
            for i in range(0, 9):
                if(i < 8): 
                    #print line_reverse[i*30:i*30+30][::-1]
                    arch.USB_inst_file.write('10' + str(line_reverse[i*30:i*30+30][::-1]) + '\n') 
                else:
                    #print line_reverse[i*30:i*30+16][::-1]
                    arch.USB_inst_file.write('10' + '0'*14 + str(line_reverse[i*30:i*30+16][::-1]) + '\n') 
            CNN_icache_cnt = CNN_icache_cnt + 1

def USB_init_icache_from_file_all():
    for pe_idx in range(0, arch.num_pe):
        USB_init_icache_pe_from_file(pe_idx)

def USB_init_shared(ia_words):
    CNN_shared_cnt = 0
    for line in ia_words:
        if(line != 'x'*256):
            #line = line[:-1]
            #mem_word = '{message:>256{fill}}'.format(message=line, fill='').replace(' ', '0')
            #write control 0
            arch.USB_inst_file.write('11' + '000000' + '110' + '001' + '000' + bindigits(CNN_shared_cnt, 15) + '\n') #KEYPOINT_THRESHOLD
            line_reverse = line[::-1]
            #print line_reverse
            for i in range(0, 9):
                if(i < 8): 
                    #print line_reverse[i*30:i*30+30][::-1]
                    arch.USB_inst_file.write('10' + str(line_reverse[i*30:i*30+30][::-1]) + '\n') 
                else:
                    #print line_reverse[i*30:i*30+16][::-1]
                    arch.USB_inst_file.write('10' + '0'*14 + str(line_reverse[i*30:i*30+16][::-1]) + '\n') 
        CNN_shared_cnt = CNN_shared_cnt + 1

def USB_init_RRAM_pe(pe_idx):
    CNN_RRAM_cnt = 1536
    for line in arch.RRAM_words_full[pe_idx]:
        arch.USB_inst_file.write('11' + '010011' + '0000000000000000000' + bindigits(pe_idx, 5) + '\n') #pe index
        #line = line[:-1]
        #inst_word = '{message:>256{fill}}'.format(message=line, fill='').replace(' ', '0')
        #write control 0
        arch.USB_inst_file.write('11' + '000000' + '110' + '010' + bindigits(CNN_RRAM_cnt/arch.rram_banks, 15) + bindigits(CNN_RRAM_cnt%arch.rram_banks, 3) + '\n') 
        line_reverse = line[::-1]
        #print line_reverse
        for i in range(0, 4):
            if(i < 3): 
                #print line_reverse[i*30:i*30+30][::-1]
                arch.USB_inst_file.write('10' + str(line_reverse[i*30:i*30+30][::-1]) + '\n') 
            else:
                #print line_reverse[i*30:i*30+16][::-1]
                arch.USB_inst_file.write('10' + '0'*24 + str(line_reverse[i*30:i*30+16][::-1]) + '\n') 
        CNN_RRAM_cnt = CNN_RRAM_cnt + 1
    USB_dummy_short()

def USB_init_RRAM_single(pe_idx):
    CNN_RRAM_base = 3072 
    CNN_RRAM_cnt = 3072
    for line in arch.RRAM_words_full[pe_idx]:
        arch.USB_inst_file.write('11' + '010011' + '0000000000000000000' + bindigits(pe_idx, 5) + '\n') #pe index
        #line = line[:-1]
        #inst_word = '{message:>256{fill}}'.format(message=line, fill='').replace(' ', '0')
        #write control 0
        arch.USB_inst_file.write('11' + '000000' + '110' + '010' + bindigits(CNN_RRAM_cnt/arch.rram_banks, 15) + bindigits(CNN_RRAM_cnt%arch.rram_banks, 3) + '\n') 
        line_reverse = line[::-1]
        line_reverse = '1'*96
        #print line_reverse
        print line
        for i in range(0, 4):
            if(i < 3): 
                #print line_reverse[i*30:i*30+30][::-1]
                arch.USB_inst_file.write('10' + str(line_reverse[i*30:i*30+30][::-1]) + '\n') 
            else:
                #print line_reverse[i*30:i*30+16][::-1]
                arch.USB_inst_file.write('10' + '0'*24 + str(line_reverse[i*30:i*30+16][::-1]) + '\n') 
        CNN_RRAM_cnt = CNN_RRAM_cnt + 1
        if(CNN_RRAM_cnt - CNN_RRAM_base == 5):
            break

    USB_dummy_short()

def USB_init_RRAM_form(pe_idx):
    CNN_RRAM_base = 3072 
    CNN_RRAM_cnt = 3072
    for line in arch.RRAM_words_full[pe_idx]:
        line = '1'*96
        arch.USB_inst_file.write('11' + '010011' + '0000000000000000000' + bindigits(pe_idx, 5) + '\n') #pe index
        #line = line[:-1]
        #inst_word = '{message:>256{fill}}'.format(message=line, fill='').replace(' ', '0')
        #write control 0
        arch.USB_inst_file.write('11' + '000000' + '110' + '010' + bindigits(CNN_RRAM_cnt/arch.rram_banks, 15) + bindigits(CNN_RRAM_cnt%arch.rram_banks, 3) + '\n') 
        line_reverse = line
        #print line_reverse
        for i in range(0, 4):
            if(i < 3): 
                #print line_reverse[i*30:i*30+30][::-1]
                arch.USB_inst_file.write('10' + str(line_reverse[i*30:i*30+30][::-1]) + '\n') 
            else:
                #print line_reverse[i*30:i*30+16][::-1]
                arch.USB_inst_file.write('10' + '0'*24 + str(line_reverse[i*30:i*30+16][::-1]) + '\n') 
        CNN_RRAM_cnt = CNN_RRAM_cnt + 1
        if(CNN_RRAM_cnt - CNN_RRAM_base == 6):
            break

    USB_dummy_short()

def USB_init_RRAM_all():
    for pe_idx in range(0, arch.num_pe):
        USB_init_RRAM_pe(pe_idx)

def USB_init_RRAM_pe_from_file(pe_idx):
    CNN_RRAM_cnt = 0
    arch.USB_inst_file.write('11' + '010011' + '0000000000000000000' + bindigits(pe_idx, 5) + '\n') #pe index
    with open(str('../data_golden/pe_' + str(pe_idx) + '_RRAM_full.mem')) as rram_file:
        for line in rram_file:
            line = line[:-1]
            #inst_word = '{message:>256{fill}}'.format(message=line, fill='').replace(' ', '0')
            #write control 0
            arch.USB_inst_file.write('11' + '000000' + '110' + '010' + bindigits(CNN_RRAM_cnt/arch.rram_banks, 15) + bindigits(CNN_RRAM_cnt%arch.rram_banks, 3) + '\n') #KEYPOINT_THRESHOLD
            line_reverse = line[::-1]
            #print line_reverse
            for i in range(0, 4):
                if(i < 3): 
                    #print line_reverse[i*30:i*30+30][::-1]
                    arch.USB_inst_file.write('10' + str(line_reverse[i*30:i*30+30][::-1]) + '\n') 
                else:
                    #print line_reverse[i*30:i*30+16][::-1]
                    arch.USB_inst_file.write('10' + '0'*24 + str(line_reverse[i*30:i*30+16][::-1]) + '\n') 
            CNN_RRAM_cnt = CNN_RRAM_cnt + 1

def USB_init_RRAM_from_file_all():
    for pe_idx in range(0, arch.num_pe):
        USB_init_RRAM_pe_from_file(pe_idx)

def USB_start_CNN_stop_USB():
    arch.USB_inst_file.write('11' + '001111' + '00000000000000000000000' + '1' + '\n') #START CNN
    arch.USB_inst_file.write('11' + '011111' + '00000000000000000000000' + '1' + '\n') #STOP USB
    #dummy
    arch.USB_inst_file.write('11' + '000010' + '000001' + '000010' + '000011' + '000100' + '\n') #RRAM_SD
    arch.USB_inst_file.write('11' + '000010' + '000001' + '000010' + '000011' + '000100' + '\n') #RRAM_SD
    arch.USB_inst_file.write('11' + '000010' + '000001' + '000010' + '000011' + '000100' + '\n') #RRAM_SD
    arch.USB_inst_file.write('11' + '000010' + '000001' + '000010' + '000011' + '000100' + '\n') #RRAM_SD
    arch.USB_inst_file.write('11' + '000010' + '000001' + '000010' + '000011' + '000100' + '\n') #RRAM_SD
    arch.USB_inst_file.write('11' + '000010' + '000001' + '000010' + '000011' + '000100' + '\n') #RRAM_SD
    arch.USB_inst_file.write('11' + '000010' + '000001' + '000010' + '000011' + '000100' + '\n') #RRAM_SD
    arch.USB_inst_file.write('11' + '000010' + '000001' + '000010' + '000011' + '000100' + '\n') #RRAM_SD

def USB_read_constant():
    arch.USB_inst_file.write('11' + '000001' + '10' + '0000000000000000' + '000010' + '\n') #RRAM_SD
    USB_dummy_short()
    arch.USB_inst_file.write('11' + '000001' + '10' + '0000000000000000' + '000011' + '\n') #PRL0, PRS0
    USB_dummy_short()
    arch.USB_inst_file.write('11' + '000001' + '10' + '0000000000000000' + '000100' + '\n') #PSS1, PRS1, PRL1
    USB_dummy_short()
    arch.USB_inst_file.write('11' + '000001' + '10' + '0000000000000000' + '000101' + '\n') #PSS2, PRS2, PRL2
    USB_dummy_short()
    arch.USB_inst_file.write('11' + '000001' + '10' + '0000000000000000' + '000110' + '\n') #PSS3, PRS3, PRL3
    USB_dummy_short()
    arch.USB_inst_file.write('11' + '000001' + '10' + '0000000000000000' + '000111' + '\n') #PSS4, PRS4, PRL4
    USB_dummy_short()
    arch.USB_inst_file.write('11' + '000001' + '10' + '0000000000000000' + '001000' + '\n') #PSS5, PRS5, PRL5
    USB_dummy_short()
    arch.USB_inst_file.write('11' + '000001' + '10' + '0000000000000000' + '001001' + '\n') #PSS6, PRS6, PRL6
    USB_dummy_short()
    arch.USB_inst_file.write('11' + '000001' + '10' + '0000000000000000' + '001010' + '\n') #PSS7, PRS7, PRL7
    USB_dummy_short()
    arch.USB_inst_file.write('11' + '000001' + '10' + '0000000000000000' + '001011' + '\n') #core_div, p_div
    USB_dummy_short()
    arch.USB_inst_file.write('11' + '000001' + '10' + '0000000000000000' + '001100' + '\n') #core RO
    USB_dummy_short()
    arch.USB_inst_file.write('11' + '000001' + '10' + '0000000000000000' + '001110' + '\n') #RRAM MODE
    USB_dummy_short()

def USB_read_shared(addr_start, addr_end, cont):
    arch.USB_inst_file.write('11' + '010101' + '000000000' + bindigits(addr_end, 15) + '\n') #addr_start 
    arch.USB_inst_file.write('11' + '000001' + '1110' + str(cont) + '0000' + bindigits(addr_start, 15) + '\n') #shared mem 
    for i in range(0, 100):
        arch.USB_inst_file.write('11' + '000010' + '000001' + '000010' + '000011' + '000100' + '\n') #RRAM_SD

def USB_read_RRAM(pe_idx, idx, addr_start, addr_end, cont):
    arch.USB_inst_file.write('11' + '010011' + '0000000000000000000' + bindigits(pe_idx, 5) + '\n') #pe index
    arch.USB_inst_file.write('11' + '010110' + '000000000' + bindigits(addr_end, 15) + '\n') #addr_end
    arch.USB_inst_file.write('11' + '000001' + '1111' + str(cont) + '0' + bindigits(idx, 3) + bindigits(addr_start, 15) + '\n') #RRAM mem 

#def USB_init_RRAM_pe():
#    CNN_shared_cnt = 0
#    for line in ia_words:
#        #line = line[:-1]
#        #mem_word = '{message:>256{fill}}'.format(message=line, fill='').replace(' ', '0')
#        #write control 0
#        arch.USB_inst_file.write('11' + '000000' + '110' + '000' + '000' + bindigits(CNN_shared_cnt, 10) + bindigits(pe_idx, 5) + '\n') #KEYPOINT_THRESHOLD
#        line_reverse = line[::-1]
#        #print line_reverse
#        for i in range(0, 9):
#            if(i < 8): 
#                #print line_reverse[i*30:i*30+30][::-1]
#                arch.USB_inst_file.write('10' + str(line_reverse[i*30:i*30+30][::-1]) + '\n') 
#            else:
#                #print line_reverse[i*30:i*30+16][::-1]
#                arch.USB_inst_file.write('10' + '0'*14 + str(line_reverse[i*30:i*30+16][::-1]) + '\n') 
#        CNN_shared_cnt = CNN_shared_cnt + 1


#with open("Ext_inst.txt") as Ext_icache_file:
#    for line in Ext_icache_file:
#        line = line[:-1]
#        inst_word = '{message:>384{fill}}'.format(message=line, fill='').replace(' ', '0')
#        CNN_icache_mem[2].write("%s\n" % inst_word[0:128])
#        CNN_icache_mem[1].write("%s\n" % inst_word[128:256])
#        CNN_icache_mem[0].write("%s\n" % inst_word[256:384])
#        #write control 0
#        USB_inst_file.write('11' + '000000' + '110' + '000' + bindigits(12, 4) + bindigits(CNN_icache_cnt, 14) + '\n') #KEYPOINT_THRESHOLD
#        line_reverse = line[::-1]
#        #print line_reverse
#        for i in range(0, 12):
#            if(i < 11): 
#                USB_inst_file.write('10' + str(line_reverse[i*30:i*30+30][::-1]) + '\n') 
#            else:
#                USB_inst_file.write('10' + '0'*18 + str(line_reverse[i*30:i*30+12][::-1]) + '\n') 
#        CNN_icache_cnt = CNN_icache_cnt + 1
#
#Ext_icache_file.close()
#
##fill icache 
#for i in range(0,icache_banks):
#    for rest_addr in range(0, 1024-CNN_icache_cnt):
#        CNN_icache_mem[i].write('x' * 128 + '\n')
#    CNN_icache_mem[i].close()
# 
#
#CNN_wram_file = open('CNN_wram' + '.txt','w+')
#CNN_wram_mem = []
#CNN_wram_cnt = 0 
#for i in range(0, wram_banks):
#    CNN_wram_mem.append(open('CNN_wram_' + str(i) + '.mem','w+'))
#
#with open("DoG_WRAM_full.mem") as DoG_wram_file:
#    for line in DoG_wram_file:
#        line = line[:-1]
#        inst_word = '{message:>512{fill}}'.format(message=line, fill='').replace(' ', '0')
#        CNN_wram_mem[3].write("%s\n" % inst_word[0:128])
#        CNN_wram_mem[2].write("%s\n" % inst_word[128:256])
#        CNN_wram_mem[1].write("%s\n" % inst_word[256:384])
#        CNN_wram_mem[0].write("%s\n" % inst_word[384:512])
#        #write control 0
#        USB_inst_file.write('11' + '000000' + '110' + '001' + bindigits(18, 5) + bindigits(CNN_wram_cnt, 13) + '\n') 
#        line_reverse = line[::-1]
#        #print line_reverse
#        for i in range(0, 18):
#            if(i < 17): 
#                USB_inst_file.write('10' + str(line_reverse[i*30:i*30+30][::-1]) + '\n') 
#            else:
#                USB_inst_file.write('10' + '0'*28 + str(line_reverse[i*30:i*30+2][::-1]) + '\n') 
#        CNN_wram_cnt = CNN_wram_cnt + 1
#
#DoG_wram_file.close()
#
#with open("Ext_WRAM_full.mem") as Ext_wram_file:
#    for line in Ext_wram_file:
#        line = line[:-1]
#        inst_word = '{message:>512{fill}}'.format(message=line, fill='').replace(' ', '0')
#        CNN_wram_mem[3].write("%s\n" % inst_word[0:128])
#        CNN_wram_mem[2].write("%s\n" % inst_word[128:256])
#        CNN_wram_mem[1].write("%s\n" % inst_word[256:384])
#        CNN_wram_mem[0].write("%s\n" % inst_word[384:512])
#        #write control 0
#        USB_inst_file.write('11' + '000000' + '110' + '001' + bindigits(18, 5) + bindigits(CNN_wram_cnt, 13) + '\n') 
#        line_reverse = line[::-1]
#        #print line_reverse
#        for i in range(0, 18):
#            if(i < 17): 
#                USB_inst_file.write('10' + str(line_reverse[i*30:i*30+30][::-1]) + '\n') 
#            else:
#                USB_inst_file.write('10' + '0'*28 + str(line_reverse[i*30:i*30+2][::-1]) + '\n') 
#        CNN_wram_cnt = CNN_wram_cnt + 1
#
#Ext_wram_file.close()
#
##fill wram
#for i in range(0, wram_banks):
#    for rest_addr in range(0, 4096-CNN_wram_cnt):
#        CNN_wram_mem[i].write('x' * 128 + '\n')
#    CNN_wram_mem[i].close()
# 
#
#CNN_bram_file = open('CNN_bram' + '.txt','w+')
#CNN_bram_mem = []
#CNN_bram_cnt = 0 
#for i in range(0, bram_banks):
#    CNN_bram_mem.append(open('CNN_bram_' + str(i) + '.mem','w+'))
#
#with open("DoG_BRAM_full.mem") as DoG_bram_file:
#    for line in DoG_bram_file:
#        line = line[:-1]
#        inst_word = '{message:>64{fill}}'.format(message=line, fill='').replace(' ', '0')
#        CNN_bram_mem[0].write("%s\n" % inst_word[0:64])
#        #write control 0
#        USB_inst_file.write('11' + '000000' + '110' + '100' + bindigits(3, 2) + bindigits(CNN_bram_cnt, 16) + '\n') 
#        line_reverse = line[::-1]
#        #print line_reverse
#        for i in range(0, 18):
#            if(i < 17): 
#                USB_inst_file.write('10' + str(line_reverse[i*30:i*30+30][::-1]) + '\n') 
#            else:
#                USB_inst_file.write('10' + '0'*28 + str(line_reverse[i*30:i*30+2][::-1]) + '\n') 
#        CNN_bram_cnt = CNN_bram_cnt + 1
#
#DoG_bram_file.close()
#
#with open("Ext_BRAM_full.mem") as Ext_bram_file:
#    for line in Ext_bram_file:
#        line = line[:-1]
#        inst_word = '{message:>64{fill}}'.format(message=line, fill='').replace(' ', '0')
#        CNN_bram_mem[0].write("%s\n" % inst_word[0:64])
#        #write control 0
#        USB_inst_file.write('11' + '000000' + '110' + '100' + bindigits(3, 2) + bindigits(CNN_bram_cnt, 16) + '\n') 
#        line_reverse = line[::-1]
#        #print line_reverse
#        for i in range(0, 18):
#            if(i < 17): 
#                USB_inst_file.write('10' + str(line_reverse[i*30:i*30+30][::-1]) + '\n') 
#            else:
#                USB_inst_file.write('10' + '0'*28 + str(line_reverse[i*30:i*30+2][::-1]) + '\n') 
#        CNN_bram_cnt = CNN_bram_cnt + 1
#
#Ext_bram_file.close()
#
##fill bram
#for i in range(0, bram_banks):
#    for rest_addr in range(0, 64-CNN_bram_cnt):
#        CNN_bram_mem[i].write('x' * 64 + '\n')
#    CNN_bram_mem[i].close()
# 
