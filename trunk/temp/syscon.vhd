-------------------------------------------------------------------------------
--
--  Design        : Whisbone Clock and Synchrone RESET generator.
--
--  File          : syscon.vhd
--
--  Related files : (none)
--
--  Author(s)     : Fabrice Mousset (fabrice.mousset@laposte.net)
--
--  Creation Date : 2007/01/05
--
--  Abstract      : This is the top file of the IP
--
--  Parameters    : (none)
--
-------------------------------------------------------------------------------
--
-- Released under both BSD license (see bsd.txt) and LGPL license (see lgpl.txt).
-- Whenever there is any discrepancy between the two licenses, the BSD license
-- will take precedence.
--
-------------------------------------------------------------------------------
-- Revision list :
--
-- Date       By        Changes
--
-------------------------------------------------------------------------------

library IEEE;
  use IEEE.std_logic_1164.all;
  use IEEE.numeric_std.all;

-- ----------------------------------------------------------------------------
--  Entity declaration
-- ----------------------------------------------------------------------------
Entity syscon is
  port
  (
    -- WISHBONE Interface
    clk_i : in  std_logic;
    rst_o : out std_logic;
  
    -- NON-WISHBONE Signals
    ext_rst: in  std_logic
  );
End Entity;

-- ----------------------------------------------------------------------------
--  Architecture declaration
-- ----------------------------------------------------------------------------
Architecture RTL of syscon is

  signal dly: std_logic;
  signal rst: std_logic;

begin

  rst_o <= rst;

  -- ---------------------------------------------------------------------------
  --  RESET signal generator process.
  -- ---------------------------------------------------------------------------
  process(clk_i)
  begin
    if(rising_edge(clk_i)) then
      dly <= ( not(ext_rst) and     dly  and not(rst) )
          or ( not(ext_rst) and not(dly) and     rst  );
  
      rst <= ( not(ext_rst) and not(dly) and not(rst) );
    end if;
  end process;

end architecture;
