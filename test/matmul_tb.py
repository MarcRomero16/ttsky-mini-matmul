import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ClockCycles, ReadOnly

N = 2
CLOCK_NS = 10
FLUSH_CYCLES = 2
RANDOM_CASES = 20
RANDOM_SEED = 42


def matmul_expected(A, B):
    C = [[0 for _ in range(N)] for _ in range(N)]
    for i in range(N):
        for j in range(N):
            total = 0
            for k in range(N):
                total += A[i][k] * B[k][j]
            C[i][j] = total & 0xFFFF  # 16-bit truncation
    return C


def print_matrix(mat, label=None):
    if label is not None:
        print(label)
    for row in mat:
        print(" ".join(f"{val:6}" for val in row))


def get_a_ports(dut):
    return [dut.A_cell_1, dut.A_cell_2]


def get_b_ports(dut):
    return [dut.B_cell_1, dut.B_cell_2]


def get_out_ports(dut):
    return [dut.out1, dut.out2, dut.out3, dut.out4]


def read_output_matrix(dut):
    vals = [int(port.value) for port in get_out_ports(dut)]
    return [vals[r * N:(r + 1) * N] for r in range(N)]


def check_matrix(expected, actual, msg_prefix=""):
    for i in range(N):
        for j in range(N):
            assert expected[i][j] == actual[i][j], (
                f"{msg_prefix}Mismatch at ({i}, {j}): "
                f"expected {expected[i][j]}, got {actual[i][j]}"
            )


def check_all_zero(actual, msg_prefix=""):
    for i in range(N):
        for j in range(N):
            assert actual[i][j] == 0, (
                f"{msg_prefix}Expected zero at ({i}, {j}), got {actual[i][j]}"
            )


async def clear_inputs(dut):
    for p in get_a_ports(dut):
        p.value = 0
    for p in get_b_ports(dut):
        p.value = 0


async def pulse_start(dut):
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0


async def setup_dut(dut):
    # Reinitialize clock each test
    dut.clk.value = 0
    cocotb.start_soon(Clock(dut.clk, CLOCK_NS, unit="ns").start())

    await clear_inputs(dut)
    dut.start.value = 0
    dut.reset.value = 1

    await ClockCycles(dut.clk, 3)
    dut.reset.value = 0
    await RisingEdge(dut.clk)

def build_diagonal_inputs(A, B, t):
    """
    At cycle t, each input lane gets one value from the active diagonal.
    A lane r gets A[r][t-r] if valid.
    B lane c gets B[t-c][c] if valid.
    Otherwise input is 0.
    """
    a_vals = [0] * N
    b_vals = [0] * N

    for r in range(N):
        k = t - r
        if 0 <= k < N:
            a_vals[r] = A[r][k]

    for c in range(N):
        k = t - c
        if 0 <= k < N:
            b_vals[c] = B[k][c]

    return a_vals, b_vals


async def drive_diagonal_wave(dut, A, B, verbose=False):
    a_ports = get_a_ports(dut)
    b_ports = get_b_ports(dut)

    for t in range(2 * N - 1):
        a_vals, b_vals = build_diagonal_inputs(A, B, t)

        await FallingEdge(dut.clk)
        for i in range(N):
            a_ports[i].value = a_vals[i]
            b_ports[i].value = b_vals[i]

        await RisingEdge(dut.clk)
        await ReadOnly()

        if verbose:
            print(f"\nCycle t={t}")
            print(f"A inputs: {a_vals}")
            print(f"B inputs: {b_vals}")
            print_matrix(read_output_matrix(dut), label="Partial outputs:")

    # Clear inputs after final active wave
    await FallingEdge(dut.clk)
    await clear_inputs(dut)


async def run_case(dut, A, B, *, verbose=False, flush_cycles=FLUSH_CYCLES):
    expected = matmul_expected(A, B)

    await clear_inputs(dut)
    await pulse_start(dut)
    await drive_diagonal_wave(dut, A, B, verbose=verbose)

    await ClockCycles(dut.clk, flush_cycles)
    await RisingEdge(dut.clk)
    await ReadOnly()

    actual = read_output_matrix(dut)

    # IMPORTANT: leave ReadOnly before returning, so the caller can drive signals
    await FallingEdge(dut.clk)

    return expected, actual


@cocotb.test()
async def simple_matrix_test(dut):
    await setup_dut(dut)

    A = [
        [1, 2],
        [3, 4]
    ]
    B = [
        [5, 6],
        [7, 8]
    ]

    expected, actual = await run_case(dut, A, B, verbose=True)

    print_matrix(expected, "\nExpected:")
    print_matrix(actual, "\nActual:")

    check_matrix(expected, actual, msg_prefix="[simple] ")
    print("\nSimple matrix test passed.")


@cocotb.test()
async def zero_matrix_test(dut):
    await setup_dut(dut)

    A = [
        [0, 0],
        [0, 0]
    ]
    B = [
        [0, 0],
        [0, 0]
    ]

    expected, actual = await run_case(dut, A, B)
    check_matrix(expected, actual, msg_prefix="[zero] ")
    check_all_zero(actual, msg_prefix="[zero] ")

    print("\nZero matrix test passed.")


@cocotb.test()
async def identity_matrix_test(dut):
    await setup_dut(dut)

    A = [
        [1, 0],
        [0, 1]
    ]
    B = [
        [9, 10],
        [11, 12]
    ]

    expected, actual = await run_case(dut, A, B)

    direct_expected = [
        [9, 10],
        [11, 12]
    ]

    check_matrix(expected, actual, msg_prefix="[identity] ")
    check_matrix(direct_expected, actual, msg_prefix="[identity-direct] ")

    print("\nIdentity matrix test passed.")


@cocotb.test()
async def maxed_matrix_test(dut):
    await setup_dut(dut)

    A = [
        [255, 255],
        [255, 255]
    ]
    B = [
        [255, 255],
        [255, 255]
    ]

    expected, actual = await run_case(dut, A, B)

    trunc_expected = [
        [0xFC02, 0xFC02],
        [0xFC02, 0xFC02]
    ]

    check_matrix(expected, actual, msg_prefix="[max] ")
    check_matrix(trunc_expected, actual, msg_prefix="[max-trunc] ")

    print("\nMaxed matrix test passed.")


@cocotb.test()
async def back_to_back_start_clears_state_test(dut):
    await setup_dut(dut)

    A1 = [
        [1, 2],
        [3, 4]
    ]
    B1 = [
        [5, 6],
        [7, 8]
    ]

    exp1, act1 = await run_case(dut, A1, B1)
    check_matrix(exp1, act1, msg_prefix="[back-to-back first] ")

    A2 = [
        [2, 0],
        [1, 3]
    ]
    B2 = [
        [4, 1],
        [2, 5]
    ]

    exp2, act2 = await run_case(dut, A2, B2)
    check_matrix(exp2, act2, msg_prefix="[back-to-back second] ")

    assert act2 != act1, (
        "[back-to-back] Second result matched first result; "
        "possible stale-state / start-clear bug."
    )

    print("\nBack-to-back start-clears-state test passed.")


@cocotb.test()
async def reset_clears_outputs_test(dut):
    await setup_dut(dut)

    A = [
        [3, 1],
        [2, 4]
    ]
    B = [
        [6, 5],
        [7, 8]
    ]

    expected, actual = await run_case(dut, A, B)
    check_matrix(expected, actual, msg_prefix="[reset precheck] ")

    dut.reset.value = 1
    await clear_inputs(dut)
    await RisingEdge(dut.clk)
    await ReadOnly()

    cleared = read_output_matrix(dut)
    check_all_zero(cleared, msg_prefix="[reset] ")

    # IMPORTANT: leave ReadOnly before changing reset again
    await FallingEdge(dut.clk)
    dut.reset.value = 0
    await RisingEdge(dut.clk)

    print("\nReset clears outputs test passed.")


@cocotb.test()
async def randomized_matrix_test(dut):
    await setup_dut(dut)

    rng = random.Random(RANDOM_SEED)

    for case_idx in range(RANDOM_CASES):
        A = [[rng.randrange(256) for _ in range(N)] for _ in range(N)]
        B = [[rng.randrange(256) for _ in range(N)] for _ in range(N)]

        expected, actual = await run_case(dut, A, B)

        try:
            check_matrix(expected, actual, msg_prefix=f"[random case {case_idx}] ")
        except AssertionError:
            print_matrix(A, f"\n[random case {case_idx}] A:")
            print_matrix(B, f"[random case {case_idx}] B:")
            print_matrix(expected, f"[random case {case_idx}] Expected:")
            print_matrix(actual, f"[random case {case_idx}] Actual:")
            raise

    print(f"\nRandomized matrix test passed ({RANDOM_CASES} cases).")