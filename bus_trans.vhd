library ieee;
use ieee.std_logic_1164.all;

entity bus_trans is
    port (
        A : inout std_logic_vector(7 downto 0);
        B : in std_logic_vector(7 downto 0);
        C : inout std_logic_vector(7 downto 0);
        S : in std_logic_vector(1 downto 0)
    );
end;

architecture dataflow of bus_trans is
begin
    A <= C when S = "00" else (others => 'Z');
    C <= (others => 'Z') when S = "00" else A when S = "01" else B;
end;
