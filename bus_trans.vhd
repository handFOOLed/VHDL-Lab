
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity bus_trans is
    port (
        A : inout std_logic_vector(7 downto 0);
        B : in    std_logic_vector(7 downto 0);
        C : inout std_logic_vector(7 downto 0);
        S : in    std_logic_vector(1 downto 0)
    );
end bus_trans;

architecture dataflow of bus_trans is
begin

    -- S=00: C -> A
    -- 其他情况: A释放总线
    A <= C when S = "00"
         else (others => 'Z');

    -- S=00: C释放总线
    -- S=01: A -> C
    -- S=10/11: B -> C
    C <= (others => 'Z') when S = "00"
         else A when S = "01"
         else B;

end dataflow;
