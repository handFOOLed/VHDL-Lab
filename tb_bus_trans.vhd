library ieee;
use ieee.std_logic_1164.all;

entity tb_bus_trans is end;

architecture simulation of tb_bus_trans is
    signal a, b, c : std_logic_vector(7 downto 0);
    signal s : std_logic_vector(1 downto 0);
    signal a_drive, c_drive : std_logic_vector(7 downto 0);
begin
    dut : entity work.bus_trans port map (A => a, B => b, C => c, S => s);
    a <= a_drive;
    c <= c_drive;
    s <= "00", "01" after 21 ns, "10" after 41 ns, "11" after 60 ns;
    b <= x"C3", x"3C" after 21 ns, x"5A" after 42 ns, x"F0" after 60 ns;
    a_drive <= x"ZZ", x"A5" after 22 ns, x"ZZ" after 40 ns;
    c_drive <= x"3C", x"ZZ" after 20 ns;

    process
        procedure check(name : string; ok : boolean) is
        begin
            assert ok report "FAIL|" & name severity failure;
            report "PASS|" & name;
        end;
    begin
        wait for 5 ns;
        check("route_00", s = "00" and a = x"3C");
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
