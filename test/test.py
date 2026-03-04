# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles
from cocotb.triggers import RisingEdge, FallingEdge, ClockCycles, ReadOnly, Timer

async def reset_dut(dut):
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0

    for _ in range(5):
        await RisingEdge(dut.clk)

    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

async def load_reg(dut, sel, value):
    """
    sel:
      0 -> A00
      1 -> A01
      2 -> A10
      3 -> A11
      4 -> B00
      5 -> B01
      6 -> B10
      7 -> B11
    """

    dut.ui_in.value = value

    # uio_in[2:0] = select
    # uio_in[3] = load
    dut.uio_in.value = (sel & 0b111) | 0b00001000
    await RisingEdge(dut.clk)

    # turn load back off
    dut.uio_in.value = 0
    await RisingEdge(dut.clk)

async def pulse_start(dut):
    # uio_in[4] = start
    dut.ui_in.value = 0
    dut.uio_in.value = 0b00010000
    await RisingEdge(dut.clk)

    dut.uio_in.value = 0
    await RisingEdge(dut.clk)

async def read_result_word(dut, out_sel):
    """
    out_sel:
      0 -> c1
      1 -> c2
      2 -> c3
      3 -> c4
    """

    # uio_in[6:5] = output select
    # uio_in[7] = byte select
    # low byte
    dut.uio_in.value = (out_sel & 0b11) << 5
    await Timer(1, unit="ns")
    low = int(dut.uo_out.value)

    # high byte
    dut.uio_in.value = ((out_sel & 0b11) << 5) | 0b10000000
    await Timer(1, unit="ns")
    high = int(dut.uo_out.value)

    return (high << 8) | low

@cocotb.test()
async def test_wrapper_smoke(dut):
    dut._log.info("Starting top-level Tiny Tapeout wrapper test")

    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    await reset_dut(dut)

    # Load matrix A
    # [ [1, 2],
    #   [3, 4] ]
    await load_reg(dut, 0, 1)  # A00
    await load_reg(dut, 1, 2)  # A01
    await load_reg(dut, 2, 3)  # A10
    await load_reg(dut, 3, 4)  # A11

    # Load matrix B
    # [ [5, 6],
    #   [7, 8] ]
    await load_reg(dut, 4, 5)  # B00
    await load_reg(dut, 5, 6)  # B01
    await load_reg(dut, 6, 7)  # B10
    await load_reg(dut, 7, 8)  # B11

    # Start the controller
    await pulse_start(dut)

    # Wait for the controller to finish feeding the systolic array
    await ClockCycles(dut.clk, 4)

    # Read outputs
    c1 = await read_result_word(dut, 0)
    c2 = await read_result_word(dut, 1)
    c3 = await read_result_word(dut, 2)
    c4 = await read_result_word(dut, 3)

    dut._log.info(f"c1={c1} c2={c2} c3={c3} c4={c4}")

    # Expected result:
    # [ [19, 22],
    #   [43, 50] ]
    assert c1 == 19, f"c1 mismatch: got {c1}, expected 19"
    assert c2 == 22, f"c2 mismatch: got {c2}, expected 22"
    assert c3 == 43, f"c3 mismatch: got {c3}, expected 43"
    assert c4 == 50, f"c4 mismatch: got {c4}, expected 50"

@cocotb.test()
async def max_test(dut):
    dut._log.info("Starting top-level Tiny Tapeout max test")

    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    await reset_dut(dut)

    # Load matrix A
    # [ [255, 255],
    #   [255, 255] ]
    await load_reg(dut, 0, 255)  # A00
    await load_reg(dut, 1, 255)  # A01
    await load_reg(dut, 2, 255)  # A10
    await load_reg(dut, 3, 255)  # A11

    # Load matrix B
    # [ [255, 255],
    #   [255, 255] ]
    await load_reg(dut, 4, 255)  # B00
    await load_reg(dut, 5, 255)  # B01
    await load_reg(dut, 6, 255)  # B10
    await load_reg(dut, 7, 255)  # B11

    # Start the controller
    await pulse_start(dut)

    # Wait for the controller to finish feeding the systolic array
    await ClockCycles(dut.clk, 4)

    # Read outputs
    c1 = await read_result_word(dut, 0)
    c2 = await read_result_word(dut, 1)
    c3 = await read_result_word(dut, 2)
    c4 = await read_result_word(dut, 3)

    dut._log.info(f"c1={c1} c2={c2} c3={c3} c4={c4}")

    # Expected result truncated to 16 bits, so we get:
    # [ [64514, 64514],
    #   [64514, 64514] ]
    assert c1 == 64514, f"c1 mismatch: got {c1}, expected 64514"
    assert c2 == 64514, f"c2 mismatch: got {c2}, expected 64514"
    assert c3 == 64514, f"c3 mismatch: got {c3}, expected 64514"
    assert c4 == 64514, f"c4 mismatch: got {c4}, expected 64514"

@cocotb.test()
async def zeroes_test(dut):
    dut._log.info("Starting top-level Tiny Tapeout zeroes test")

    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    await reset_dut(dut)

    # Load matrix A
    # [ [0, 0],
    #   [0, 0] ]
    await load_reg(dut, 0, 0)  # A00
    await load_reg(dut, 1, 0)  # A01
    await load_reg(dut, 2, 0)  # A10
    await load_reg(dut, 3, 0)  # A11

    # Load matrix B
    # [ [0, 0],
    #   [0, 0] ]
    await load_reg(dut, 4, 0)  # B00
    await load_reg(dut, 5, 0)  # B01
    await load_reg(dut, 6, 0)  # B10
    await load_reg(dut, 7, 0)  # B11

    # Start the controller
    await pulse_start(dut)

    # Wait for the controller to finish feeding the systolic array
    await ClockCycles(dut.clk, 4)

    # Read outputs
    c1 = await read_result_word(dut, 0)
    c2 = await read_result_word(dut, 1)
    c3 = await read_result_word(dut, 2)
    c4 = await read_result_word(dut, 3)

    dut._log.info(f"c1={c1} c2={c2} c3={c3} c4={c4}")

    # Expected result truncated to 16 bits, so we get:
    # [ [0, 0],
    #   [0, 0] ]
    assert c1 == 0, f"c1 mismatch: got {c1}, expected 0"
    assert c2 == 0, f"c2 mismatch: got {c2}, expected 0"
    assert c3 == 0, f"c3 mismatch: got {c3}, expected 0"
    assert c4 == 0, f"c4 mismatch: got {c4}, expected 0"

@cocotb.test()
async def Identity_matrix_test(dut):
    dut._log.info("Starting top-level Tiny Tapeout Identity matrix test")

    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    await reset_dut(dut)

    # Load matrix A
    # [ [1, 0],
    #   [0, 1] ]
    await load_reg(dut, 0, 1)  # A00
    await load_reg(dut, 1, 0)  # A01
    await load_reg(dut, 2, 0)  # A10
    await load_reg(dut, 3, 1)  # A11

    # Load matrix B
    # [ [9, 10],
    #   [11, 12] ]
    await load_reg(dut, 4, 9)  # B00
    await load_reg(dut, 5, 10)  # B01
    await load_reg(dut, 6, 11)  # B10
    await load_reg(dut, 7, 12)  # B11

    # Start the controller
    await pulse_start(dut)

    # Wait for the controller to finish feeding the systolic array
    await ClockCycles(dut.clk, 4)

    # Read outputs
    c1 = await read_result_word(dut, 0)
    c2 = await read_result_word(dut, 1)
    c3 = await read_result_word(dut, 2)
    c4 = await read_result_word(dut, 3)

    dut._log.info(f"c1={c1} c2={c2} c3={c3} c4={c4}")

    # Expected result truncated to 16 bits, so we get:
    # [ [9, 10],
    #   [11, 12] ]
    assert c1 == 9, f"c1 mismatch: got {c1}, expected 9"
    assert c2 == 10, f"c2 mismatch: got {c2}, expected 10"
    assert c3 == 11, f"c3 mismatch: got {c3}, expected 11"
    assert c4 == 12, f"c4 mismatch: got {c4}, expected 12"

@cocotb.test()
async def Back_to_back_start_test(dut):
    dut._log.info("Starting top-level Tiny Tapeout Back to back start test")

    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    await reset_dut(dut)

    # Load matrix A
    # [ [1, 2],
    #   [3, 4] ]
    await load_reg(dut, 0, 1)  # A00
    await load_reg(dut, 1, 2)  # A01
    await load_reg(dut, 2, 3)  # A10
    await load_reg(dut, 3, 4)  # A11

    # Load matrix B
    # [ [5, 6],
    #   [7, 8] ]
    await load_reg(dut, 4, 5)  # B00
    await load_reg(dut, 5, 6)  # B01
    await load_reg(dut, 6, 7)  # B10
    await load_reg(dut, 7, 8)  # B11

    # Start the controller
    await pulse_start(dut)

    # Wait for the controller to finish feeding the systolic array
    await ClockCycles(dut.clk, 4)

    # Read outputs
    c1 = await read_result_word(dut, 0)
    c2 = await read_result_word(dut, 1)
    c3 = await read_result_word(dut, 2)
    c4 = await read_result_word(dut, 3)

    dut._log.info(f"c1={c1} c2={c2} c3={c3} c4={c4}")

    # Expected result:
    # [ [19, 22],
    #   [43, 50] ]
    assert c1 == 19, f"c1 mismatch: got {c1}, expected 19"
    assert c2 == 22, f"c2 mismatch: got {c2}, expected 22"
    assert c3 == 43, f"c3 mismatch: got {c3}, expected 43"
    assert c4 == 50, f"c4 mismatch: got {c4}, expected 50"

    # Load matrix A again
    # [ [2, 0],
    #   [1, 3] ]
    await load_reg(dut, 0, 2)  # A00
    await load_reg(dut, 1, 0)  # A01
    await load_reg(dut, 2, 1)  # A10
    await load_reg(dut, 3, 3)  # A11

    # Load matrix B again
    # [ [4, 1],
    #   [2, 5] ]
    await load_reg(dut, 4, 4)  # B00
    await load_reg(dut, 5, 1)  # B01
    await load_reg(dut, 6, 2)  # B10
    await load_reg(dut, 7, 5)  # B11

    # Start the controller again without resetting
    await pulse_start(dut)

    # Wait for the controller to finish feeding the systolic array
    await ClockCycles(dut.clk, 4)

    # Read outputs
    c1 = await read_result_word(dut, 0)
    c2 = await read_result_word(dut, 1)
    c3 = await read_result_word(dut, 2)
    c4 = await read_result_word(dut, 3)

    dut._log.info(f"c1={c1} c2={c2} c3={c3} c4={c4}")

    # Expected result:
    # [ [8, 2],
    #   [10, 16] ]
    assert c1 == 8, f"c1 mismatch: got {c1}, expected 8"
    assert c2 == 2, f"c2 mismatch: got {c2}, expected 2"
    assert c3 == 10, f"c3 mismatch: got {c3}, expected 10"
    assert c4 == 16, f"c4 mismatch: got {c4}, expected 16"

@cocotb.test()
async def reset_test(dut):
    dut._log.info("Starting top-level Tiny Tapeout reset test")

    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    await reset_dut(dut)

    # Load matrix A
    # [ [1, 2],
    #   [3, 4] ]
    await load_reg(dut, 0, 1)  # A00
    await load_reg(dut, 1, 2)  # A01
    await load_reg(dut, 2, 3)  # A10
    await load_reg(dut, 3, 4)  # A11

    # Load matrix B
    # [ [1, 2],
    #   [3, 4] ]
    await load_reg(dut, 4, 1)  # B00
    await load_reg(dut, 5, 2)  # B01
    await load_reg(dut, 6, 3)  # B10
    await load_reg(dut, 7, 4)  # B11

    # Start the controller
    await pulse_start(dut)

    # Reset during computation
    await reset_dut(dut)

    # Read outputs
    c1 = await read_result_word(dut, 0)
    c2 = await read_result_word(dut, 1)
    c3 = await read_result_word(dut, 2)
    c4 = await read_result_word(dut, 3)

    dut._log.info(f"c1={c1} c2={c2} c3={c3} c4={c4}")

    # Expected result truncated to 16 bits, so we get:
    # [ [0, 0],
    #   [0, 0] ]
    assert c1 == 0, f"c1 mismatch: got {c1}, expected 0"
    assert c2 == 0, f"c2 mismatch: got {c2}, expected 0"
    assert c3 == 0, f"c3 mismatch: got {c3}, expected 0"
    assert c4 == 0, f"c4 mismatch: got {c4}, expected 0"

