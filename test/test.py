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


async def load_reg(dut, reg_image, sel, value):
    """
    sel:
      0 -> a1
      1 -> a2
      2 -> b1
      3 -> b2
    """
    reg_image[sel] = value
    dut.ui_in.value = value
    dut.uio_in.value = sel & 0b11
    await RisingEdge(dut.clk)


async def pulse_start_preserve_reg(dut, reg_image, preserve_sel=0):
    """
    Your current wrapper uses uio_in[1:0] for register select and uio_in[2] for start.
    That means asserting start still selects one register.

    To avoid accidentally overwriting a stored value during the start pulse,
    keep ui_in equal to the currently stored value of the selected register.
    By default, preserve a1 (sel=0).
    """
    preserved_value = reg_image[preserve_sel]

    # start = 1, but keep selected register unchanged
    dut.ui_in.value = preserved_value
    dut.uio_in.value = (preserve_sel & 0b11) | 0b00000100
    await RisingEdge(dut.clk)

    # start = 0, still preserve the same register for one more cycle
    dut.ui_in.value = preserved_value
    dut.uio_in.value = (preserve_sel & 0b11)
    await RisingEdge(dut.clk)


async def read_result_word(dut, out_sel):
    """
    out_sel:
      0 -> c1
      1 -> c2
      2 -> c3
      3 -> c4
    """

    # low byte first
    dut.uio_in.value = (out_sel & 0b11) << 4
    await Timer(1, unit="ns")
    low = int(dut.uo_out.value)

    # then high byte
    dut.uio_in.value = ((out_sel & 0b11) << 4) | 0b00001000
    await Timer(1, unit="ns")
    high = int(dut.uo_out.value)

    return (high << 8) | low


@cocotb.test()
async def test_wrapper_smoke(dut):
    dut._log.info("Starting top-level Tiny Tapeout wrapper smoke test")

    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    await reset_dut(dut)

    # Mirror of what we believe is stored in the wrapper registers:
    # [a1, a2, b1, b2]
    reg_image = [0, 0, 0, 0]

    # Load wrapper registers
    await load_reg(dut, reg_image, 0, 1)  # a1 = 1
    await load_reg(dut, reg_image, 1, 2)  # a2 = 2
    await load_reg(dut, reg_image, 2, 3)  # b1 = 3
    await load_reg(dut, reg_image, 3, 4)  # b2 = 4

    # Pulse start without clobbering a1
    await pulse_start_preserve_reg(dut, reg_image, preserve_sel=0)

    # Read outputs
    c1 = await read_result_word(dut, 0)
    c2 = await read_result_word(dut, 1)
    c3 = await read_result_word(dut, 2)
    c4 = await read_result_word(dut, 3)

    dut._log.info(f"c1={c1} c2={c2} c3={c3} c4={c4}")

    # With the current wrapper + streaming core arrangement,
    # one post-start compute cycle should produce only the first partial result.
    assert c1 == 3, f"c1 mismatch: got {c1}, expected 3"
    assert c2 == 0, f"c2 mismatch: got {c2}, expected 0"
    assert c3 == 0, f"c3 mismatch: got {c3}, expected 0"
    assert c4 == 0, f"c4 mismatch: got {c4}, expected 0"
