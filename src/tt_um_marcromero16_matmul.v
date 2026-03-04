/*
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_marcromero16_matmul (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  // Internal storage for one wave of streamed inputs
  reg [7:0] a1, a2, b1, b2;

  wire [15:0] c1, c2, c3, c4;
  wire reset = ~rst_n;
  wire start = uio_in[2];

  // Load selected input register from ui_in
  // uio_in[1:0]:
  // 00 -> a1
  // 01 -> a2
  // 10 -> b1
  // 11 -> b2
  always @(posedge clk) begin
    if (reset) begin
      a1 <= 8'd0;
      a2 <= 8'd0;
      b1 <= 8'd0;
      b2 <= 8'd0;
    end else begin
      case (uio_in[1:0])
        2'b00: a1 <= ui_in;
        2'b01: a2 <= ui_in;
        2'b10: b1 <= ui_in;
        2'b11: b2 <= ui_in;
      endcase
    end
  end

  matmul matmul_inst (
    .clk      (clk),
    .reset    (reset),
    .start    (start),
    .A_cell_1 (a1),
    .A_cell_2 (a2),
    .B_cell_1 (b1),
    .B_cell_2 (b2),
    .out1     (c1),
    .out2     (c2),
    .out3     (c3),
    .out4     (c4)
  );

  // Readback mux:
  // uio_in[5:4] chooses c1/c2/c3/c4
  // uio_in[3]   chooses low byte (0) or high byte (1)

  wire [15:0] selected_c;

  assign selected_c =
      (uio_in[5:4] == 2'b00) ? c1 :
      (uio_in[5:4] == 2'b01) ? c2 :
      (uio_in[5:4] == 2'b10) ? c3 :
                              c4;

  assign uo_out = uio_in[3] ? selected_c[15:8] : selected_c[7:0];

  // We are not driving bidirectional pins in this version
  assign uio_out = 8'h00;
  assign uio_oe  = 8'h00;

  // Mark unused signal(s)
  wire _unused = &{ena, uio_in[7:6], 1'b0};

endmodule
