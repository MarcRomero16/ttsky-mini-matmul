<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

This project is a small **2×2 streaming matrix multiplier** written in Verilog. The main idea is that the design stores two 2×2 input matrices first, and then a small controller feeds those values into the systolic array over multiple clock cycles. Because of that, the matrix multiplication is not done all at once in one cycle. Instead, the values move through the array over time until the full 2×2 result is built.

The design is split into three parts:

- **`matmul.v`**: the systolic matrix multiplication core  
- **`controller.v`**: the controller that feeds the correct input wave each cycle  
- **`tt_um_marcromero16_matmul.v`**: the Tiny Tapeout top-level wrapper (module name `tt_um_marcromero16_matmul`)  

The **`matmul.v`** module is the actual datapath. It takes streamed input values and performs the multiply-and-accumulate operations that build the four output values of the 2×2 result matrix.

The **`controller.v`** module handles the cycle-by-cycle sequencing. After a start pulse, it sends the stored matrix entries into the systolic array in the correct diagonal pattern. For a 2×2 case, it feeds:

- first diagonal
- middle diagonal
- last diagonal
- one final flush cycle

This makes the systolic array receive the values in the order it needs.

The **`tt_um_marcromero16_matmul.v`** wrapper connects everything to the Tiny Tapeout pins. It stores all 8 matrix entries first:

- **A00, A01, A10, A11**
- **B00, B01, B10, B11**

Then the controller uses those stored values to drive the systolic array.

For the wrapper, I use:

- **`ui_in[7:0]`** as the 8-bit data input
- **`uio_in[7:0]`** as control inputs
- **`uo_out[7:0]`** as the output readback path

The control bits are used like this:

- **`uio_in[2:0]`**: chooses which matrix register to load  
- **`uio_in[3]`**: load enable  
- **`uio_in[4]`**: start  
- **`uio_in[6:5]`**: chooses which output to read (`c1`, `c2`, `c3`, or `c4`)  
- **`uio_in[7]`**: chooses low byte or high byte of the selected output  

Since Tiny Tapeout has limited I/O, the outputs are read back one byte at a time. Each result (`c1`, `c2`, `c3`, `c4`) is 16 bits, so the wrapper includes a simple readback mux that lets me select which output word and which byte to send to `uo_out`.

At a high level, the circuit computes:

- **C = A × B**

where:

- **A** is a 2×2 input matrix
- **B** is a 2×2 input matrix
- **C** is the 2×2 output matrix

The outputs are:

- **`c1 = C00`**
- **`c2 = C01`**
- **`c3 = C10`**
- **`c4 = C11`**

Each output entry is the sum of two products, and the final values are stored as 16-bit results.

---

## How to test

I used a **cocotb testbench written in Python** to test this project. My testing is split into two levels: testing the internal matrix multiplier core by itself, and testing the full Tiny Tapeout top-level wrapper.

### 1. Core module testing

The file **`matmul_tb.py`** directly tests the internal `matmul` module. This lets me verify that the systolic matrix multiplication logic works correctly before worrying about the Tiny Tapeout wrapper.

The core testbench includes:

- a simple directed test with known values
- a zero-matrix test
- an identity-matrix test
- a max-value test to check 16-bit truncation
- back-to-back operation tests to make sure a new start clears previous state
- reset tests
- randomized test cases compared against a software-computed expected result

I think this is enough to test the core because it checks both normal behavior and edge cases. It does not just test one example. It also checks reset behavior, repeated operations, truncation behavior, and many random input combinations.

### 2. Top-level wrapper testing

I also test the Tiny Tapeout top module through the standard `tb.v` wrapper and `test.py` cocotb flow. This checks that the wrapper correctly:

- loads all 8 matrix values
- starts the controller
- waits for the controller to finish feeding the systolic array
- reads back the four output words correctly through the output mux

My `test.py` includes multiple directed tests similar to the core testbench. These include:

- a simple directed matrix multiply test
- a zero-matrix test
- an identity-matrix test
- a max-value test
- back-to-back operation tests
- reset behavior tests

I did **not** include the randomized test in `test.py`, since the top-level wrapper test is mainly there to verify the Tiny Tapeout interface and integration. I kept the randomized testing in `matmul_tb.py`, where it makes more sense to stress-test the internal matrix multiplier directly.

This matters because even if the internal multiplier works, the full project could still fail if:

- matrix values are loaded into the wrong registers
- control bits are mapped incorrectly
- the controller timing is wrong
- output selection is wrong
- reset does not behave correctly at the top level

## Use of GenAI tools
I used GenAI tools as a support tool while working on this project. I mainly used them to help me:

- develop and improve my testbenches
- debug simulation issues
- improve and organize my documentation

I still reviewed and edited everything myself, and I used simulation results to verify that the final design behaved the way I expected. The GenAI tools helped speed up debugging and test development, but I still checked the design manually before using the final version.
