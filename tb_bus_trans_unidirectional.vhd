library ieee;
use ieee.std_logic_1164.all;

entity tb_bus_trans_unidirectional is end;

architecture simulation of tb_bus_trans_unidirectional is
    signal a, b, c : std_logic_vector(7 downto 0);
    signal s : std_logic_vector(1 downto 0);
begin
    dut : entity work.bus_trans_unidirectional port map (A => a, B => b, C => c, S => s);
    s <= "00", "01" after 20 ns, "10" after 40 ns, "11" after 60 ns;
    a <= x"3C", x"A5" after 20 ns;
    b <= x"C3", x"3C" after 20 ns, x"5A" after 40 ns, x"F0" after 60 ns;

    process
        procedure check(name : string; ok : boolean) is
        begin
            assert ok report "FAIL|" & name severity failure;
            report "PASS|" & name;
        end;
    begin
        wait for 5 ns;
        check("route_00", s = "00" and c = x"3C");
        wait for 20 ns;
        check("route_01", s = "01" and c = x"A5");
        wait for 20 ns;
        check("route_10", s = "10" and c = x"5A");
        wait for 20 ns;
        check("route_11", s = "11" and c = x"F0");
        wait for 15 ns;
        report "SUMMARY|4 routing checks passed; completed at 80 ns";
        wait;
    end process;
end;
