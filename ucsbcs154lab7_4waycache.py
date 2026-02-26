# ucsbcs154lab7_4waycache.py
# All Rights Reserved
# Copyright (c) 2022 Jonathan Balkind
# Distribution Prohibited

import pyrtl

pyrtl.core.set_debug_mode()

# Cache parameters:
# 32 bit addresses
# 4 ways
# 16 rows
# 16 bytes (4 words) per block

# Inputs
req_new = pyrtl.Input(bitwidth=1, name='req_new')       # High on cycles when a request is occurring
req_addr = pyrtl.Input(bitwidth=32, name='req_addr')    # Requested address
req_type = pyrtl.Input(bitwidth=1, name='req_type')     # 0 read, 1 write
req_data = pyrtl.Input(bitwidth=32, name='req_data')    # Only for writes

# Outputs
resp_hit = pyrtl.Output(bitwidth=1, name='resp_hit')    # Indicates whether there was a cache hit
resp_data = pyrtl.Output(bitwidth=32, name='resp_data') # If read request, return data at req_addr
# Memories
### Memories of cache? use address indiceses to index into here and check valid and tag. 
### 01234 for ways. addr width of all is 4 bits, so its 2^4 = 16 for the 16 rows. i guess valid0123 = just value at these index?
valid_0 = pyrtl.MemBlock(bitwidth=1, addrwidth=4, max_read_ports=2, max_write_ports=1, asynchronous=True, name='valid_0')
valid_1 = pyrtl.MemBlock(bitwidth=1, addrwidth=4, max_read_ports=2, max_write_ports=1, asynchronous=True, name='valid_1')
valid_2 = pyrtl.MemBlock(bitwidth=1, addrwidth=4, max_read_ports=2, max_write_ports=1, asynchronous=True, name='valid_2')
valid_3 = pyrtl.MemBlock(bitwidth=1, addrwidth=4, max_read_ports=2, max_write_ports=1, asynchronous=True, name='valid_3')

tag_0 = pyrtl.MemBlock(bitwidth=24, addrwidth=4, max_read_ports=2, max_write_ports=1, asynchronous=True, name='tag_0')
tag_1 = pyrtl.MemBlock(bitwidth=24, addrwidth=4, max_read_ports=2, max_write_ports=1, asynchronous=True, name='tag_1')
tag_2 = pyrtl.MemBlock(bitwidth=24, addrwidth=4, max_read_ports=2, max_write_ports=1, asynchronous=True, name='tag_2')
tag_3 = pyrtl.MemBlock(bitwidth=24, addrwidth=4, max_read_ports=2, max_write_ports=1, asynchronous=True, name='tag_3')

data_0 = pyrtl.MemBlock(bitwidth=128, addrwidth=4, max_read_ports=2, max_write_ports=1, asynchronous=True, name='data_0')
data_1 = pyrtl.MemBlock(bitwidth=128, addrwidth=4, max_read_ports=2, max_write_ports=1, asynchronous=True, name='data_1')
data_2 = pyrtl.MemBlock(bitwidth=128, addrwidth=4, max_read_ports=2, max_write_ports=1, asynchronous=True, name='data_2')
data_3 = pyrtl.MemBlock(bitwidth=128, addrwidth=4, max_read_ports=2, max_write_ports=1, asynchronous=True, name='data_3')

# To track which Way entry to replace next.
repl_way = pyrtl.MemBlock(bitwidth=2, addrwidth=4, max_read_ports=2, max_write_ports=1, asynchronous=True, name='repl_way')

# TODO: Declare your own WireVector, MemBlocks, etc.
addr_tag = pyrtl.WireVector(bitwidth=24, name = "addr_tag")
addr_index = pyrtl.WireVector(bitwidth = 4, name = "addr_index")
addr_offset = pyrtl.WireVector(bitwidth = 4, name = "addr_offset")
word_offset = pyrtl.WireVector(bitwidth = 2, name = "word_offset")
addr_tag <<= req_addr[8:32]
addr_index <<= req_addr[4:8]
addr_offset <<= req_addr[0:4]
word_offset <<= pyrtl.shift_right_logical(addr_offset,2)

repl_way_temp = pyrtl.WireVector(bitwidth = 2, name = "repl_way_temp")
resp_hit_temp = pyrtl.WireVector(bitwidth = 1, name = "resp_hit_temp")
resp_data_temp = pyrtl.WireVector(bitwidth = 32, name = "resp_data_temp")
write_mask = pyrtl.WireVector(bitwidth = 128, name = "write_mask")
write_data = pyrtl.WireVector(bitwidth = 128, name = "write_data")

####################################################################################
####################################################################################
####################################################################################

# TODO: Check four entries in a row in parallel.
# TODO: Determine if hit or miss.

# 1 if hit, 0 if not hit
hit_0 = (tag_0[addr_index] == addr_tag) & (valid_0[addr_index])
hit_1 = (tag_1[addr_index] == addr_tag) & (valid_1[addr_index])
hit_2 = (tag_2[addr_index] == addr_tag) & (valid_2[addr_index])
hit_3 = (tag_3[addr_index] == addr_tag) & (valid_3[addr_index])

resp_hit_temp <<= hit_0 | hit_1 | hit_2 | hit_3 # if all miss, then its a miss

resp_hit <<= resp_hit_temp
####################################################################################

## Round robin init 
repl_way_temp <<= repl_way[addr_index]
repl_way_at_index = pyrtl.WireVector(bitwidth = 2, name = "repl_way_at_index")
# update round robin
with pyrtl.conditional_assignment:
    with (req_new & ~resp_hit_temp):
        with repl_way_temp == 3:
            repl_way_at_index |= 0
        with pyrtl.otherwise:
            repl_way_at_index |= repl_way_temp + 1

repl_way[addr_index] <<= repl_way_at_index
# TODO: Handle replacement. Be careful handling replacement when you
# also have to do a write
####################################################################################


# payload = block data
data_0_payload = data_0[addr_index]
data_1_payload = data_1[addr_index]
data_2_payload = data_2[addr_index]
data_3_payload = data_3[addr_index]

data_0_temp = pyrtl.WireVector(bitwidth = 128, name = "data_0_temp")
data_1_temp = pyrtl.WireVector(bitwidth = 128, name = "data_1_temp")
data_2_temp = pyrtl.WireVector(bitwidth = 128, name = "data_2_temp")
data_3_temp = pyrtl.WireVector(bitwidth = 128, name = "data_3_temp")


# TODO: If request type is read, return read data at appropriate block address
# if read hit, return read_word
read_word_0 = pyrtl.shift_right_logical(data_0_payload, word_offset * 32) & pyrtl.Const(0x0FFFFFFFF, bitwidth = 32)
read_word_1 = pyrtl.shift_right_logical(data_1_payload, word_offset * 32) & pyrtl.Const(0x0FFFFFFFF, bitwidth = 32)
read_word_2 = pyrtl.shift_right_logical(data_2_payload, word_offset * 32) & pyrtl.Const(0x0FFFFFFFF, bitwidth = 32)
read_word_3 = pyrtl.shift_right_logical(data_3_payload, word_offset * 32) & pyrtl.Const(0x0FFFFFFFF, bitwidth = 32)

with pyrtl.conditional_assignment:
    with req_new & ~req_type & resp_hit_temp:
        resp_data_temp |= pyrtl.select(hit_0, read_word_0, pyrtl.select(hit_1, read_word_1, pyrtl.select(hit_2, read_word_2, pyrtl.select(hit_3,read_word_3, pyrtl.Const(0, bitwidth = 32)))))
    with pyrtl.otherwise:
        resp_data_temp |= pyrtl.Const(0, bitwidth = 32)

# READ HIT DONE. 
# Do read miss
""" 
tag_0[addr_index] <<= pyrtl.MemBlock.EnabledWrite(addr_tag, req_new & ~resp_hit_temp & (repl_way_temp == 0))
tag_1[addr_index] <<= pyrtl.MemBlock.EnabledWrite(addr_tag, req_new & ~resp_hit_temp & (repl_way_temp == 1))
tag_2[addr_index] <<= pyrtl.MemBlock.EnabledWrite(addr_tag, req_new & ~resp_hit_temp & (repl_way_temp == 2))
tag_3[addr_index] <<= pyrtl.MemBlock.EnabledWrite(addr_tag, req_new & ~resp_hit_temp & (repl_way_temp == 3))
 """
any_miss = req_new & ~req_type & ~resp_hit_temp
# if miss, set whole block to 0, valid to 1, tag = addr tag. 
valid_0[addr_index] <<= pyrtl.MemBlock.EnabledWrite(pyrtl.Const(1, bitwidth = 1), (any_miss & (repl_way_temp == 0)))
valid_1[addr_index] <<= pyrtl.MemBlock.EnabledWrite(pyrtl.Const(1, bitwidth = 1), (any_miss & (repl_way_temp == 1)))
valid_2[addr_index] <<= pyrtl.MemBlock.EnabledWrite(pyrtl.Const(1, bitwidth = 1), (any_miss & (repl_way_temp == 2)))
valid_3[addr_index] <<= pyrtl.MemBlock.EnabledWrite(pyrtl.Const(1, bitwidth = 1), (any_miss & (repl_way_temp == 3)))


tag_0[addr_index] <<= pyrtl.MemBlock.EnabledWrite(addr_tag, (any_miss & (repl_way_temp == 0)))
tag_1[addr_index] <<= pyrtl.MemBlock.EnabledWrite(addr_tag, (any_miss & (repl_way_temp == 1)))
tag_2[addr_index] <<= pyrtl.MemBlock.EnabledWrite(addr_tag, (any_miss & (repl_way_temp == 2)))
tag_3[addr_index] <<= pyrtl.MemBlock.EnabledWrite(addr_tag, (any_miss & (repl_way_temp == 3)))
# DONE READ MISS
# TODO: DO WRITE HIT
read_miss = req_new & ~req_type & ~resp_hit_temp
write_miss = req_new & req_type & ~resp_hit_temp
write_hit = req_new & req_type & resp_hit_temp


# if read miss, set block to 0. if write miss, set block except the new word to 0. if write HIT, then only change the filling. 
# if miss and repl way, set temp to be 0. else set temp to be new data
data_0_temp <<= pyrtl.select(read_miss & (repl_way_temp == 0), pyrtl.Const(0, bitwidth = 128), # if read miss, make all 0
                             pyrtl.select(write_miss & (repl_way_temp == 0),  write_data, # if write miss, make all 0 but write data
                                          pyrtl.select(write_hit & repl_way_temp == 0, (data_0_payload & write_mask) | write_data, pyrtl.Const(0)))) # if write hit, set cavity filling
data_1_temp <<= pyrtl.select(read_miss & (repl_way_temp == 1), pyrtl.Const(0, bitwidth = 128), # if read miss, make all 0
                             pyrtl.select(write_miss & (repl_way_temp == 1),  write_data, # if write miss, make all 0 but write data
                                          pyrtl.select(write_hit & repl_way_temp == 1, (data_1_payload & write_mask) | write_data, pyrtl.Const(0)))) # if write hit, set cavity filling
data_2_temp <<= pyrtl.select(read_miss & (repl_way_temp == 2), pyrtl.Const(0, bitwidth = 128), # if read miss, make all 0
                             pyrtl.select(write_miss & (repl_way_temp == 2),  write_data, # if write miss, make all 0 but write data
                                          pyrtl.select(write_hit & repl_way_temp == 2, (data_2_payload & write_mask) | write_data, pyrtl.Const(0)))) # if write hit, set cavity filling
data_3_temp <<= pyrtl.select(read_miss & (repl_way_temp == 3), pyrtl.Const(0, bitwidth = 128), # if read miss, make all 0
                             pyrtl.select(write_miss & (repl_way_temp == 3),  write_data, # if write miss, make all 0 but write data
                                          pyrtl.select(write_hit & repl_way_temp == 3, (data_3_payload & write_mask) | write_data, pyrtl.Const(0)))) # if write hit, set cavity filling
                                        

data_shift_amount = word_offset * 32
write_hit = req_new & req_type & resp_hit_temp
write_miss =  req_new & req_type & ~resp_hit_temp

# SELECT: WRITE HIT? MASK IS THING THE 11100001111 MASK : MASK IS ALL 0
# 
write_mask <<= pyrtl.select(write_hit, (~pyrtl.shift_left_logical(pyrtl.Const(0x0ffffffff, bitwidth=128), data_shift_amount)),0)
# TODO: LOOK OVER THIS AREA!!!
# SELECT: WRITE? WRITE DATA = 0: WRITE DATA = 
write_data <<= pyrtl.select((req_new & req_type), pyrtl.shift_left_logical(req_data.zero_extended(bitwidth=128), data_shift_amount), 0)

# enabled to write if hit write on correct way OR ANY miss but next in round robin. 
enable_0 = (req_new & req_type) & (hit_0 | (~resp_hit_temp & (repl_way_temp == 0)))
enable_1 = (req_new & req_type) & (hit_1 | (~resp_hit_temp & (repl_way_temp == 1)))
enable_2 = (req_new & req_type) & (hit_2 | (~resp_hit_temp & (repl_way_temp == 2)))
enable_3 = (req_new & req_type) & (hit_3 | (~resp_hit_temp & (repl_way_temp == 3)))

data_0[addr_index] <<= pyrtl.MemBlock.EnabledWrite(data_0_temp, enable_0)
data_1[addr_index] <<= pyrtl.MemBlock.EnabledWrite(data_1_temp, enable_1)
data_2[addr_index] <<= pyrtl.MemBlock.EnabledWrite(data_2_temp, enable_2)
data_3[addr_index] <<= pyrtl.MemBlock.EnabledWrite(data_3_temp, enable_3)

# TODO: If request type is write, write req_data to appropriate block address

""" zv0 = pyrtl.WireVector(bitwidth = 128, name = "zv0")
zv1 = pyrtl.WireVector(bitwidth = 128, name = "zv1")
zv2 = pyrtl.WireVector(bitwidth = 128, name = "zv2")
zv3 = pyrtl.WireVector(bitwidth = 128, name = "zv3") """
# miss and request, set valid to 1

""" 
valid_0[addr_index] <<= pyrtl.MemBlock.EnabledWrite(1, req_new & ~resp_hit_temp & (repl_way_temp == 0))
valid_1[addr_index] <<= pyrtl.MemBlock.EnabledWrite(1, req_new & ~resp_hit_temp & (repl_way_temp == 1))
valid_2[addr_index] <<= pyrtl.MemBlock.EnabledWrite(1, req_new & ~resp_hit_temp & (repl_way_temp == 2))
valid_3[addr_index] <<= pyrtl.MemBlock.EnabledWrite(1, req_new & ~resp_hit_temp & (repl_way_temp == 3))
 """

resp_data <<= resp_data_temp


# TODO: Determine output

############################## SIMULATION ######################################

def TestNoRequest(simulation, trace, addr=1024):
    simulation.step({
        'req_new':0,
        'req_addr':addr,
        'req_type':0,
        'req_data':0,
    })

    assert(trace.trace["resp_hit"][-1] == 0)
    assert(trace.trace["resp_data"][-1] == 0)
    print("Passed No Request Case!")

# Precondition: addr is not already in the cache.
# Postcondition: There is a cache miss. 
def TestMiss(simulation, trace, addr = 0):
    simulation.step({
        'req_new':1,
        'req_addr':addr,
        'req_type':0,
        'req_data':0,
    })

    assert(trace.trace["resp_hit"][-1] == 0)
    assert(trace.trace["resp_data"][-1] == 0)

    print("Passed Miss Case!")

# Precondition: addr is already in the cache.
# Postcondition: There is a cache hit and the cache returns
# the expected word. 
def TestHit(simulation, trace, addr = 0, expected_data = 0):
    simulation.step({
        'req_new':1,
        'req_addr':addr,
        'req_type':0,
        'req_data':0,
    })

    assert(trace.trace["resp_hit"][-1] == 1)
    assert(trace.trace["resp_data"][-1] == expected_data) 

    print("Passed Hit Case!")

# Precondition: addr is already in the cache.
# Postcondition: The word located at memory address 'addr'
# has been replaced with 'new_data'.
def TestWrite(simulation, trace, addr=0, new_data=156):
    simulation.step({
        'req_new': 1,
        'req_addr': addr,
        'req_type': 1,
        'req_data': new_data,
    })

    assert(trace.trace["resp_hit"][-1] == 1)
    assert(trace.trace["resp_data"][-1] == 0) 

    # Read back the correct value
    simulation.step({
        'req_new': 1,
        'req_addr': addr,
        'req_type': 0,
        'req_data': 0,
    })

    assert(trace.trace["resp_hit"][-1] == 1)
    assert(trace.trace["resp_data"][-1] == new_data) 
    print("Passed Write Test!")

# Precondition: addr does not already hit in the cache.
# Postcondition: addr exists in the cache at the correct
# cache index
def TestCorrectIndex(simulation, trace, addr = 32):
    simulation.step({
        'req_new': 1,
        'req_addr': addr,
        'req_type': 0,
        'req_data': 0,
    })
    # read miss 
    assert(trace.trace["resp_hit"][-1] == 0)
    assert(trace.trace["resp_data"][-1] == 0) 
    
    bin_addr = bin(addr)[2:]
    missing_bits = 32 - len(bin_addr)
    if missing_bits > 0:
        bin_addr = ("0" * missing_bits) + bin_addr

    cache_index = int("0b" + bin_addr[-8:-4], 2)
    addr_tag = int("0b" + bin_addr[:24], 2)

    tag_0_val = simulation.inspect_mem(tag_0).get(cache_index)
    tag_1_val = simulation.inspect_mem(tag_1).get(cache_index)
    tag_2_val = simulation.inspect_mem(tag_2).get(cache_index)
    tag_3_val = simulation.inspect_mem(tag_3).get(cache_index)

    assert((tag_0_val == addr_tag) or (tag_1_val == addr_tag) or (tag_2_val == addr_tag) or (tag_3_val == addr_tag))

    # Ensure that we hit in the next cycle.
    simulation.step({
        'req_new': 1,
        'req_addr': addr,
        'req_type': 0,
        'req_data': 0,
    })

    assert(trace.trace["resp_hit"][-1] == 1)
    assert(trace.trace["resp_data"][-1] == 0) 

    print("Passed Correct Index Test!")

sim_trace = pyrtl.SimulationTrace()
sim = pyrtl.Simulation(tracer=sim_trace)


TestNoRequest(sim, sim_trace)
TestMiss(sim, sim_trace)
TestHit(sim, sim_trace)

TestWrite(sim, sim_trace)
TestCorrectIndex(sim, sim_trace)

# Print trace
# sim_trace.render_trace(symbol_len=8)
