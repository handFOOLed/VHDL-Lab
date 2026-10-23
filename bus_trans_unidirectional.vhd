library ieee;
use ieee.std_logic_1164.all;

entity bus_trans_unidirectional is
    port (
        A, B : in std_logic_vector(7 downto 0);
        C : out std_logic_vector(7 downto 0);
        S : in std_logic_vector(1 downto 0)
    );
end;

architecture dataflow of bus_trans_unidirectional is
begin
    C <= A when S = "00" or S = "01" else B;
end;
