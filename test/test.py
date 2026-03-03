# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


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
      0 -> a1
      1 -> a2
      2 -> b1
      3 -> b2
    """
    dut.ui_in.value = value
    dut.uio_in.value = sel & 0b11
    await RisingEdge(dut.clk)


async def pulse_start(dut):
    # uio_in[2] = start
    dut.ui_in.value = 0
    dut.uio_in.value = 0b00000100
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
    # low byte first: uio_in[3] = 0
    dut.uio_in.value = (out_sel & 0b11) << 4
    await Timer(1, unit="ns")
    low = int(dut.uo_out.value)

    # high byte: uio_in[3] = 1
    dut.uio_in.value = ((out_sel & 0b11) << 4) | 0b00001000
    await Timer(1, unit="ns")
    high = int(dut.uo_out.value)

    return (high << 8) | low


# -----------------------------
# Tests
# -----------------------------

@cocotb.test()
async def test_small_values(dut):
    dut._log.info("Starting top-level Tiny Tapeout test: small values")

    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    # Load example values
    # a1=1, a2=2, b1=3, b2=4
    await load_reg(dut, 0, 1)
    await load_reg(dut, 1, 2)
    await load_reg(dut, 2, 3)
    await load_reg(dut, 3, 4)

    await pulse_start(dut)

    c1 = await read_result_word(dut, 0)
    c2 = await read_result_word(dut, 1)
    c3 = await read_result_word(dut, 2)
    c4 = await read_result_word(dut, 3)

    dut._log.info(f"c1={c1} c2={c2} c3={c3} c4={c4}")

    # Expected values depend on your wrapper/core behavior.
    # If your core does simple product mapping:
    # c1 = a1*b1, c2 = a1*b2, c3 = a2*b1, c4 = a2*b2
    assert c1 == 3,  f"c1 mismatch: got {c1}, expected 3"
    assert c2 == 4,  f"c2 mismatch: got {c2}, expected 4"
    assert c3 == 6,  f"c3 mismatch: got {c3}, expected 6"
    assert c4 == 8,  f"c4 mismatch: got {c4}, expected 8"
