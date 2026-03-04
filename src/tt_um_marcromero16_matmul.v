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

  wire reset;
  wire load;
  wire start;

  assign reset = ~rst_n;
  assign load  = uio_in[3];
  assign start = uio_in[4];

  // Stored matrix A values
  reg [7:0] A00;
  reg [7:0] A01;
  reg [7:0] A10;
  reg [7:0] A11;

  // Stored matrix B values
  reg [7:0] B00;
  reg [7:0] B01;
  reg [7:0] B10;
  reg [7:0] B11;

  // Controller outputs that feed the systolic array
  wire [7:0] feed_a1;
  wire [7:0] feed_a2;
  wire [7:0] feed_b1;
  wire [7:0] feed_b2;

  wire running;
  wire done;

  // Matmul outputs
  wire [15:0] c1;
  wire [15:0] c2;
  wire [15:0] c3;
  wire [15:0] c4;

  // Selected output for readback
  wire [15:0] selected_c;

  // Load matrix registers from ui_in
  // uio_in[2:0] picks which one to load
  always @(posedge clk) begin
    if (reset) begin
      A00 <= 8'd0;
      A01 <= 8'd0;
      A10 <= 8'd0;
      A11 <= 8'd0;
      B00 <= 8'd0;
      B01 <= 8'd0;
      B10 <= 8'd0;
      B11 <= 8'd0;
    end else if (load) begin
      case (uio_in[2:0])
        3'b000: A00 <= ui_in;
        3'b001: A01 <= ui_in;
        3'b010: A10 <= ui_in;
        3'b011: A11 <= ui_in;
        3'b100: B00 <= ui_in;
        3'b101: B01 <= ui_in;
        3'b110: B10 <= ui_in;
        3'b111: B11 <= ui_in;
      endcase
    end
  end

  // Controller sends the correct inputs each cycle
  controller controller_inst (
    .clk(clk),
    .reset(reset),
    .start(start),

    .A00(A00),
    .A01(A01),
    .A10(A10),
    .A11(A11),

    .B00(B00),
    .B01(B01),
    .B10(B10),
    .B11(B11),

    .a1(feed_a1),
    .a2(feed_a2),
    .b1(feed_b1),
    .b2(feed_b2),

    .running(running),
    .done(done)
  );

  // Systolic matrix multiplier core
  matmul matmul_inst (
    .clk(clk),
    .reset(reset),
    .start(start),

    .A_cell_1(feed_a1),
    .A_cell_2(feed_a2),
    .B_cell_1(feed_b1),
    .B_cell_2(feed_b2),

    .out1(c1),
    .out2(c2),
    .out3(c3),
    .out4(c4)
  );

  // Pick which output word to read
  assign selected_c =
      (uio_in[6:5] == 2'b00) ? c1 :
      (uio_in[6:5] == 2'b01) ? c2 :
      (uio_in[6:5] == 2'b10) ? c3 :
                               c4;

  // uio_in[7] picks low byte or high byte
  assign uo_out = (uio_in[7]) ? selected_c[15:8] : selected_c[7:0];

  // Not using bidirectional pins as outputs
  assign uio_out = 8'h00;
  assign uio_oe  = 8'h00;

  // Prevent unused warnings
  wire _unused = &{ena, running, done, 1'b0};

endmodule
