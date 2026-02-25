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

addr_tag <<= req_addr[8:32]
addr_index <<= req_addr[4:8]
addr_offset <<= req_addr[0:4]

hit_way = pyrtl.WireVector(bitwidth = 4, name = "hit_way")
repl_way_temp = pyrtl.WireVector(bitwidth = 2, name = "repl_way_temp")
resp_hit_temp = pyrtl.WireVector(bitwidth = 1, name = "resp_hit_temp")
resp_data_temp = pyrtl.WireVector(bitwidth = 128, name = "resp_data_temp")
write_mask = pyrtl.WireVector(bitwidth = 128, name = "write_mask")
write_data = pyrtl.WireVector(bitwidth = 128, name = "write_data")

####################################################################################

# TODO: Check four entries in a row in parallel.
# TODO: Determine if hit or miss.

# hit_way = which way was hit (0 to 4)
# hit_result_temp = 0 if hit, 1 if not hit 

with pyrtl.conditional_assignment:
    with req_new: # if this is a read/write request
        with (tag_0[addr_index] == addr_tag) & (valid_0[addr_index]):
            resp_hit_temp |= pyrtl.Const(1)
            hit_way |= pyrtl.Const(0)
        with (tag_1[addr_index] == addr_tag) & (valid_1[addr_index]):
            resp_hit_temp |= pyrtl.Const(1)
            hit_way |= pyrtl.Const(1)
        with (tag_2[addr_index] == addr_tag) & (valid_2[addr_index]):
            resp_hit_temp |= pyrtl.Const(1)
            hit_way |= pyrtl.Const(2)
        with (tag_3[addr_index] == addr_tag) & (valid_3[addr_index]):
            resp_hit_temp |= pyrtl.Const(1)
            hit_way |= pyrtl.Const(3)
        with pyrtl.otherwise:
            resp_hit_temp |= pyrtl.Const(0)
            hit_way |= pyrtl.Const(0)

resp_hit <<= resp_hit_temp

## Round robin init 
repl_way_temp <<= repl_way[addr_index]

# TODO: If request type is write, write req_data to appropriate block address
enable_0 = pyrtl.WireVector(bitwidth = 1, name = "enable_0")
enable_1 = pyrtl.WireVector(bitwidth = 1, name = "enable_1")
enable_2 = pyrtl.WireVector(bitwidth = 1, name = "enable_2")
enable_3 = pyrtl.WireVector(bitwidth = 1, name = "enable_3")



# TODO: If request type is read, return read data at appropriate block address
# bitshift the thing all the way left, then and with 0000001111. 
with pyrtl.conditional_assignment:
    with (req_new & ~req_type): # if this was a read request
        with resp_hit_temp: # if it was a hit
            # index into the class, read the appropriate thing.
            with hit_way == 0:
                resp_data_temp |= pyrtl.shift_left_logical(data_0[addr_index], 32 * addr_offset) & 0b1111
            with hit_way == 1:
                resp_data_temp |= pyrtl.shift_left_logical(data_1[addr_index], 32 * addr_offset) & 0b1111
            with hit_way == 2:
                resp_data_temp |= pyrtl.shift_left_logical(data_2[addr_index], 32 * addr_offset) & 0b1111
            with hit_way == 3:
                resp_data_temp |= pyrtl.shift_left_logical(data_3[addr_index], 32 * addr_offset) & 0b1111
        with pyrtl.otherwise: # if it was a miss and READ. DOES THIS WORK OR DO SIMILR TO WRITE MISS
            with repl_way_temp == 0:
                valid_0[addr_index] |= pyrtl.Const(1)
            with repl_way_temp == 1:
                valid_1[addr_index] |= pyrtl.Const(1)
            with repl_way_temp == 2:
                valid_2[addr_index] |= pyrtl.Const(1)
            with repl_way_temp == 3:
                valid_3[addr_index] |= pyrtl.Const(1)
    with (req_new & req_type): # if this was a write request       
        with resp_hit_temp: # if this was WRITE HIT     
            with hit_way == 0:
                enable_0 |= pyrtl.Const(1)
                enable_1 |= pyrtl.Const(0)
                enable_2 |= pyrtl.Const(0)
                enable_3 |= pyrtl.Const(0)
            with hit_way == 1:
                enable_0 |= pyrtl.Const(0)
                enable_1 |= pyrtl.Const(1)
                enable_2 |= pyrtl.Const(0)
                enable_3 |= pyrtl.Const(0)
            with hit_way == 2:
                enable_0 |= pyrtl.Const(0)
                enable_1 |= pyrtl.Const(0)
                enable_2 |= pyrtl.Const(1)
                enable_3 |= pyrtl.Const(0)
            with hit_way == 3:
                enable_0 |= pyrtl.Const(0)
                enable_1 |= pyrtl.Const(0)
                enable_2 |= pyrtl.Const(0)
                enable_3 |= pyrtl.Const(1)
        with pyrtl.otherwise: # if this was a WRITE MISS
            with repl_way_temp == 0:
                valid_0[addr_index] |= pyrtl.Const(1)
            with repl_way_temp == 1:
                valid_1[addr_index] |= pyrtl.Const(1)
            with repl_way_temp == 2:
                valid_2[addr_index] |= pyrtl.Const(1)
            with repl_way_temp == 3:
                valid_3[addr_index] |= pyrtl.Const(1)

resp_data <<= resp_data_temp

        # need to replace by round robin!
        
            #On a cache miss, our cache will not access a larger memory as would occur in a regular
            # memory hierarchy. You may instead assume the new block's contents are "0". If you miss on
            # req_addr, you should return “0” as your resp_data and output “0” as your resp_hit. The
            # replaced data block should be set to “0” and valid for future accesses.
       
data_shift_amount = addr_offset * 32

# if resp_hit_temp = 1 : WE HIT then write mask is 0000 1111 1111 0000 0000 (if offset was)
write_mask <<= pyrtl.select(resp_hit_temp, ~pyrtl.shift_left_logical(pyrtl.Const(0x0ffffffff, bitwidth=128), data_shift_amount), 0)

# TODO: This line is incomplete you will need to change it appropriately. 
# IF MISSED AND REQ_TYPE is READ (0) and IS NEW REQUEST
write_data <<= pyrtl.select(~resp_hit_temp & ~req_type & req_new, 0, pyrtl.shift_left_logical(req_data.zero_extended(bitwidth=128), data_shift_amount))
data_0_payload = data_0[addr_index]
data_1_payload = data_1[addr_index]
data_2_payload = data_2[addr_index]
data_3_payload = data_3[addr_index]

data_0[addr_index] <<= pyrtl.MemBlock.EnabledWrite((data_0_payload & write_mask) | write_data, enable_0) 
data_1[addr_index] <<= pyrtl.MemBlock.EnabledWrite((data_1_payload & write_mask) | write_data, enable_1)
data_2[addr_index] <<= pyrtl.MemBlock.EnabledWrite((data_2_payload & write_mask) | write_data, enable_2)
data_3[addr_index] <<= pyrtl.MemBlock.EnabledWrite((data_3_payload & write_mask) | write_data, enable_3)

repl_way_at_index = pyrtl.WireVector(bitwidth = 2, name = "repl_way_at_index")
with pyrtl.conditional_assignment:
    with (req_new & ~resp_hit_temp): # if mem request and was a MISS
        with repl_way_temp == 3:
            repl_way_at_index |= 0
        with pyrtl.otherwise:
            repl_way_at_index |= repl_way_temp + 1

repl_way[addr_index] <<= repl_way_at_index
# TODO: Handle replacement. Be careful handling replacement when you
# also have to do a write

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