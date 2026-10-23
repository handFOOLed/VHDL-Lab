library ieee;
use ieee.std_logic_1164.all;
use std.env.all;

entity tb_bus_trans is
end entity;

architecture simulation of tb_bus_trans is
    signal a, b, c : std_logic_vector(7 downto 0) := (others => 'Z');
    signal s : std_logic_vector(1 downto 0) := "00";
    signal a_drive, c_drive : std_logic_vector(7 downto 0) := (others => 'Z');
    constant released : std_logic_vector(7 downto 0) := (others => 'Z');
    constant conflict : std_logic_vector(7 downto 0) := (others => 'X');
begin
    a <= a_drive;
    c <= c_drive;
    dut : entity work.bus_trans
        port map (A => a, B => b, C => c, S => s);

    stimulus : process
        procedure check(constant name : string; constant ok : boolean) is
        begin
            assert ok report "FAIL|" & name severity failure;
            report "PASS|" & name severity note;
        end procedure;
    begin
        -- Each normal direction change releases external drivers before S changes.
        wait for 1 ns;
        c_drive <= x"3C";
        wait for 4 ns;
        check("route_00", s = "00" and a = x"3C" and c = x"3C" and a_drive = released);
        wait for 15 ns; -- 20 ns
        c_drive <= released;
        a_drive <= released;
        wait for 1 ns;
        s <= "01";
        wait for 1 ns;
        a_drive <= x"A5";
        wait for 3 ns;
        check("route_01", s = "01" and a = x"A5" and c = x"A5" and c_drive = released);
        wait for 15 ns; -- 40 ns
        a_drive <= released;
        c_drive <= released;
        wait for 1 ns;
        s <= "10";
        wait for 1 ns;
        b <= x"5A";
        wait for 3 ns;
        check("route_10", s = "10" and c = x"5A" and a = released and c_drive = released);
        wait for 15 ns; -- 60 ns
        a_drive <= released;
        c_drive <= released;
        wait for 1 ns;
        s <= "11";
        wait for 1 ns;
        b <= x"F0";
        wait for 3 ns;
        check("route_11", s = "11" and c = x"F0" and a = released and c_drive = released);
        wait for 15 ns; -- 80 ns: end of required routing intervals

        -- Release both buses in both bidirectional modes.
        a_drive <= released;
        c_drive <= released;
        wait for 1 ns;
        s <= "00";
        wait for 2 ns;
        check("release_00", a = released and c = released);
        wait for 1 ns;
        s <= "01";
        wait for 1 ns;
        check("release_01", a = released and c = released);

        -- Deliberate negative tests: X is the expected resolved bus value.
        wait for 0.5 ns;
        s <= "00";
        wait for 0.5 ns; -- 86 ns
        c_drive <= x"FF";
        a_drive <= x"00";
        wait for 1 ns;
        check("conflict_00", a = conflict and c = x"FF");
        wait for 1 ns;
        a_drive <= released;
        wait for 1 ns;
        check("recovery_00", a = x"FF" and c = x"FF");
        wait for 1 ns; -- 90 ns
        a_drive <= released;
        c_drive <= released;
        wait for 1 ns;
        s <= "01";
        wait for 1 ns;
        a_drive <= x"A5";
        c_drive <= x"5A";
        wait for 1 ns;
        check("conflict_01", c = conflict and a = x"A5");
        wait for 1 ns;
        c_drive <= released;
        wait for 1 ns;
        check("recovery_01", c = x"A5" and a = x"A5");
        wait for 1 ns;
        a_drive <= released;
        wait for 1 ns;
        check("release_final", a = released and c = released);
        wait for 3 ns;
        report "SUMMARY|11 checks passed; 4 routing, 3 release, 2 expected conflicts, 2 recoveries" severity note;
        finish;
    end process;
end architecture;
