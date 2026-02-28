`timescale 1ns/1ps

`define START_TESTBENCH    error_o = 0; pass_o = 0; #10;
`define FINISH_WITH_FAIL   error_o = 1; pass_o = 0; #10; $finish();
`define FINISH_WITH_PASS   pass_o = 1; error_o = 0; #10; $finish();

module testbench
  (output logic error_o = 1'bx
  ,output logic pass_o  = 1'bx);

  logic [10:0] error;

  logic        clk_i;
  logic        reset_i;

  logic  [7:0] io_A_1, io_A_2;
  logic  [7:0] io_B_1, io_B_2;
  logic        io_start;

  wire [15:0]  io_C_1,  io_C_2,  io_C_3,  io_C_4;

  // 100MHz clock -> period 10ns (toggle every 5ns)
  initial clk_i = 1'b0;
  always #5 clk_i = ~clk_i;

  matmul 
   #()
  matmul_inst (
    .clk      (clk_i),
    .reset    (reset_i),
    .start    (io_start),

    .A_cell_1 (io_A_1),
    .A_cell_2 (io_A_2),

    .B_cell_1 (io_B_1),
    .B_cell_2 (io_B_2),

    .out1     (io_C_1),
    .out2     (io_C_2),
    .out3     (io_C_3),
    .out4     (io_C_4)
  );

  // Stimulus Check
  logic [7:0] A [0:1][0:1]; 
  logic [7:0] B [0:1][0:1]; 
  logic [15:0] Cexp [0:1][0:1];
  
  // Using always_comb to calculate expected outputs
//   always_comb begin
//   for (int i = 0; i < 2; i++) begin
//     for (int j = 0; j < 2; j++) begin
//       int unsigned sum;
//       sum = 0;
//       for (int k = 0; k < 2; k++) begin
//         sum += A[i][k] * B[k][j];
//       end
//       Cexp[i][j] = sum[15:0];
//     end
//   end
//   end

  // t = 3n - 3
  initial begin
    `START_TESTBENCH
    error = 0;
    io_A_1 = 0; io_A_2 = 0;
    io_B_1 = 0; io_B_2 = 0;

    reset_i = 1'b1;                 // assert reset
    repeat (3) @(posedge clk_i);
    reset_i = 1'b0;                 // deassert reset
    @(posedge clk_i);

    // --------------------------------
    // Test: Simple 2x2 Matrix Multiplication
    // --------------------------------

    // A
    A[0][0]=1; A[0][1]=2;
    A[1][0]=3; A[1][1]=4;  
    // B
    B[0][0]= 5; B[0][1]= 6;
    B[1][0]= 7; B[1][1]=8;
    
    // Expected C = A*B
    Cexp[0][0]= 19; Cexp[0][1]= 22;
    Cexp[1][0]= 43; Cexp[1][1]= 50;

    io_start = 1'b1;
    @(posedge clk_i);
    io_start = 1'b0;

    // t=0
    @(negedge clk_i);
    io_A_1 = 1; io_A_2 = 0;
    io_B_1 = 5; io_B_2 = 0; 
    @(posedge clk_i);
    #1;
    $display("t0 C00=%0d C01=%0d C10=%0d C11=%0d", io_C_1, io_C_2, io_C_3, io_C_4);

    // t=1
    @(negedge clk_i);
    io_A_1 = 2; io_A_2 = 3;
    io_B_1 = 7; io_B_2 = 6;
    @(posedge clk_i);
    #1;
    $display("t1 C00=%0d C01=%0d C10=%0d C11=%0d", io_C_1, io_C_2, io_C_3, io_C_4);

    // t=2
    @(negedge clk_i);
    io_A_1 = 0; io_A_2 = 4;
    io_B_1 = 0; io_B_2 = 8;
    @(posedge clk_i);
    #1;
    $display("t2 C00=%0d C01=%0d C10=%0d C11=%0d", io_C_1, io_C_2, io_C_3, io_C_4);

    // t=3 flush
    @(negedge clk_i);
    io_A_1 = 0; io_A_2 = 0;
    io_B_1 = 0; io_B_2 = 0;
    @(posedge clk_i);
    #1;
    $display("t3 C00=%0d C01=%0d C10=%0d C11=%0d", io_C_1, io_C_2, io_C_3, io_C_4);

    // checks (flattened: row*4 + col)
    if (io_C_1 !== Cexp[0][0]) begin $display("C00 mismatch got=%0d exp=%0d", io_C_1, Cexp[0][0]); error++; end
    if (io_C_2 !== Cexp[0][1]) begin $display("C01 mismatch got=%0d exp=%0d", io_C_2, Cexp[0][1]); error++; end
    if (io_C_3 !== Cexp[1][0]) begin $display("C10 mismatch got=%0d exp=%0d", io_C_3, Cexp[1][0]); error++; end
    if (io_C_4 !== Cexp[1][1]) begin $display("C11 mismatch got=%0d exp=%0d", io_C_4, Cexp[1][1]); error++; end

    // --------------------------------
    // Test: 2x2 Matrix Multiplication (8'b11111111 inputs) Truncated output
    // --------------------------------

    // A
    A[0][0]=8'b11111111; A[0][1]=8'b11111111;
    A[1][0]=8'b11111111; A[1][1]=8'b11111111;  
    // B
    B[0][0]= 8'b11111111; B[0][1]= 8'b11111111;
    B[1][0]= 8'b11111111; B[1][1]=8'b11111111;
    
    // Expected C = A*B 1111110000000010
    Cexp[0][0]= 16'hFC02; Cexp[0][1]= 16'hFC02;
    Cexp[1][0]= 16'hFC02; Cexp[1][1]= 16'hFC02;

    io_start = 1'b1;
    repeat (3) @(posedge clk_i);
    io_start = 1'b0;
    @(posedge clk_i)

    // t=0
    @(negedge clk_i);
    io_A_1 = 8'hFF; io_A_2 = 0;
    io_B_1 = 8'hFF; io_B_2 = 0; 
    @(posedge clk_i);
    #1;
    $display("t0 C00=%0d C01=%0d C10=%0d C11=%0d", io_C_1, io_C_2, io_C_3, io_C_4);

    // t=1
    @(negedge clk_i);
    io_A_1 = 8'hFF; io_A_2 = 8'hFF;
    io_B_1 = 8'hFF; io_B_2 = 8'hFF;
    @(posedge clk_i);
    #1;
    $display("t1 C00=%0d C01=%0d C10=%0d C11=%0d", io_C_1, io_C_2, io_C_3, io_C_4);

    // t=2
    @(negedge clk_i);
    io_A_1 = 0; io_A_2 = 8'hFF;
    io_B_1 = 0; io_B_2 = 8'hFF;
    @(posedge clk_i);
    #1;
    $display("t2 C00=%0d C01=%0d C10=%0d C11=%0d", io_C_1, io_C_2, io_C_3, io_C_4);

    // t=3 flush
    @(negedge clk_i);
    io_A_1 = 0; io_A_2 = 0;
    io_B_1 = 0; io_B_2 = 0;
    @(posedge clk_i);
    #1;
    $display("t3 C00=%0d C01=%0d C10=%0d C11=%0d", io_C_1, io_C_2, io_C_3, io_C_4);

    // checks (flattened: row*4 + col)
    if (io_C_1 !== Cexp[0][0]) begin $display("C00 mismatch got=%0d exp=%0d", io_C_1, Cexp[0][0]); error++; end
    if (io_C_2 !== Cexp[0][1]) begin $display("C01 mismatch got=%0d exp=%0d", io_C_2, Cexp[0][1]); error++; end
    if (io_C_3 !== Cexp[1][0]) begin $display("C10 mismatch got=%0d exp=%0d", io_C_3, Cexp[1][0]); error++; end
    if (io_C_4 !== Cexp[1][1]) begin $display("C11 mismatch got=%0d exp=%0d", io_C_4, Cexp[1][1]); error++; end

    if (error > 0) begin
      `FINISH_WITH_FAIL
    end else begin
      `FINISH_WITH_PASS
    end
  end

  final begin
    $display("Simulation time is %t", $time);
    if(error_o === 1) begin
      $display("\033[0;31m    ______                    \033[0m");
      $display("\033[0;31m   / ____/_____________  _____\033[0m");
      $display("\033[0;31m  / __/ / ___/ ___/ __ \\/ ___/\033[0m");
      $display("\033[0;31m / /___/ /  / /  / /_/ / /    \033[0m");
      $display("\033[0;31m/_____/_/  /_/   \\____/_/     \033[0m");
      $display("Simulation Failed");
    end else if (pass_o === 1) begin
      $display("\033[0;32m    ____  ___   __________\033[0m");
      $display("\033[0;32m   / __ \\/   | / ___/ ___/\033[0m");
      $display("\033[0;32m  / /_/ / /| | \\__ \\\\__ \\ \033[0m");
      $display("\033[0;32m / ____/ ___ |___/ /__/ / \033[0m");
      $display("\033[0;32m/_/   /_/  |_/____/____/  \033[0m");
      $display();
      $display("Simulation Succeeded!");
    end else begin
      $display("   __  ___   ____ __ _   ______ _       ___   __");
      $display("  / / / / | / / //_// | / / __ \\ |     / / | / /");
      $display(" / / / /  |/ / ,<  /  |/ / / / / | /| / /  |/ / ");
      $display("/ /_/ / /|  / /| |/ /|  / /_/ /| |/ |/ / /|  /  ");
      $display("\\____/_/ |_/_/ |_/_/ |_/\\____/ |__/|__/_/ |_/   ");
      $display("Please set error_o or pass_o!");
    end
  end

endmodule