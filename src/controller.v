module controller (
    input  wire       clk,
    input  wire       reset,
    input  wire       start,

    // Stored matrix values
    input  wire [7:0] A00,
    input  wire [7:0] A01,
    input  wire [7:0] A10,
    input  wire [7:0] A11,
    input  wire [7:0] B00,
    input  wire [7:0] B01,
    input  wire [7:0] B10,
    input  wire [7:0] B11,

    // Outputs to the systolic array input lanes
    output reg  [7:0] a1,
    output reg  [7:0] a2,
    output reg  [7:0] b1,
    output reg  [7:0] b2,

    output reg        running,
    output reg        done
);

reg [1:0] t;

always @(posedge clk) begin
    if (reset) begin
        a1      <= 8'd0;
        a2      <= 8'd0;
        b1      <= 8'd0;
        b2      <= 8'd0;
        t       <= 2'd0;
        running <= 1'b0;
        done    <= 1'b0;
    end else begin
        done <= 1'b0;

        // Start a new operation
        if (start && !running) begin
            running <= 1'b1;
            t       <= 2'd0;
        end

        if (running) begin
            case (t)
                2'd0: begin
                    // First diagonal
                    a1 <= A00;
                    a2 <= 8'd0;
                    b1 <= B00;
                    b2 <= 8'd0;
                    t  <= 2'd1;
                end

                2'd1: begin
                    // Middle diagonal
                    a1 <= A01;
                    a2 <= A10;
                    b1 <= B10;
                    b2 <= B01;
                    t  <= 2'd2;
                end

                2'd2: begin
                    // Last diagonal
                    a1 <= 8'd0;
                    a2 <= A11;
                    b1 <= 8'd0;
                    b2 <= B11;
                    t  <= 2'd3;
                end

                2'd3: begin
                    // Flush cycle
                    a1      <= 8'd0;
                    a2      <= 8'd0;
                    b1      <= 8'd0;
                    b2      <= 8'd0;
                    running <= 1'b0;
                    done    <= 1'b1;
                    t       <= 2'd0;
                end
            endcase
        end
    end
end

endmodule
