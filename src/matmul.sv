module matmul (
    input clk,
    input reset,
    input start,
    input [7:0] A_cell_1, //row1 pipe
    input [7:0] A_cell_2, //row2 pipe
    input [7:0] B_cell_1, //col1 pipe
    input [7:0] B_cell_2, //col2 pipe
    output [15:0] out1,
    output [15:0] out2,
    output [15:0] out3,
    output [15:0] out4
);

// Accumulators values
logic [15:0] acc1, acc2, acc3, acc4;

// Registers to hold previous inputs
logic [7:0] a_reg_top, a_reg_bot;
logic [7:0] b_reg_left, b_reg_right;

always_ff @(posedge clk) begin : DFF
    if (reset | start) begin // If restart or start, clear matmul
        acc1 <= 16'd0;
        acc2 <= 16'd0;
        acc3 <= 16'd0;
        acc4 <= 16'd0;
        a_reg_top <= 8'd0;
        a_reg_bot <= 8'd0;
        b_reg_left <= 8'd0;
        b_reg_right <= 8'd0;
    end else begin
        // Multilply, then add to the accumulated value
        acc1 <= acc1 + {8'd0, A_cell_1} * {8'd0, B_cell_1};
        acc2 <= acc2 + {8'd0, a_reg_top} * {8'd0, B_cell_2};
        acc3 <= acc3 + {8'd0, A_cell_2} * {8'd0, b_reg_left};
        acc4 <= acc4 + {8'd0, a_reg_bot} * {8'd0, b_reg_right};

        // Store current inputs so it can be used next cycle in parallel
        a_reg_top <= A_cell_1;
        a_reg_bot <= A_cell_2;
        b_reg_left <= B_cell_1;
        b_reg_right <= B_cell_2;
    end
end

// Push out the outputs each cycle
assign out1 = acc1;
assign out2 = acc2;
assign out3 = acc3;
assign out4 = acc4;

endmodule