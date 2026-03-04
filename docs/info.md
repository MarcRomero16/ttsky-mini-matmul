<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

This project is a small **2×2 streaming matrix multiplier** written in Verilog. The main idea is that instead of loading in two full matrices at once, the values are fed into the design over multiple clock cycles. Inside the circuit, the values move through registers and are multiplied and accumulated over time until the full 2×2 result matrix is produced.

The design is split into two parts:

- **`matmul.v`**: the actual matrix multiplication core  
- **`project.v`**: the Tiny Tapeout top-level wrapper  

The `matmul.v` module handles the multiply-and-accumulate logic for the matrix multiplication itself. The `project.v` module is the required Tiny Tapeout wrapper that connects my design to the standard Tiny Tapeout input and output pins.

For the wrapper, I use:

- **`ui_in[7:0]`** as the main 8-bit data input
- **`uio_in`** as control inputs
- **`uo_out[7:0]`** as the output readback path

The control pins are used to:

- choose which internal register to load
- send a **start** pulse
- choose which output result to read
- choose whether to read the low byte or high byte of that result

Since Tiny Tapeout has limited I/O, this lets me still access all four 16-bit outputs by reading them out one byte at a time.

At a high level, the circuit computes:

- **C = A × B**

where:

- **A** is a 2×2 input matrix
- **B** is a 2×2 input matrix
- **C** is the 2×2 output matrix

Each output entry is made by summing two products, and the final values are truncated to 16 bits.

---

## How to test

I used a **cocotb testbench written in Python** to test this project. My testing is split into two levels: testing the internal multiplier itself, and testing the full Tiny Tapeout top-level wrapper.

### 1. Core module testing

The file **`matmul_tb.py`** directly tests the internal `matmul` module. This lets me verify that the matrix multiplication logic works correctly before worrying about the Tiny Tapeout wrapper.

The testbench includes:

- a simple directed test with known values
- a zero-matrix test
- an identity-matrix test
- a max-value test to check 16-bit truncation
- back-to-back operation tests to make sure `start` clears previous state
- reset tests
- randomized test cases compared against a software-computed expected result

I believe this is enough to test the core because it checks both normal behavior and edge cases. It does not just test one example — it also checks reset behavior, repeated operations, overflow/truncation, and many random input combinations.

### 2. Top-level wrapper testing

I also test the Tiny Tapeout top module through the standard `tb.v` wrapper and cocotb flow. This checks that the wrapper logic correctly connects the Tiny Tapeout pins to the internal matrix multiplier.

This matters because even if the internal multiplier works, the full project could still fail if:

- inputs are loaded incorrectly
- control signals are mapped wrong
- output readback is wrong
- reset does not behave correctly at the top level

## Use of GenAI tools
I used GenAI tools as a support tool while working on this project. I mainly used them to help me:

develop and improve my testbenches

debug simulation issues

improve and organize my documentation

I still reviewed and edited everything myself, and I used simulation results to verify that the final design behaved the way I expected. The GenAI tools helped speed up debugging and test development, but I still checked the design manually before using the final version.
