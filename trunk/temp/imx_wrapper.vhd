-------------------------------------------------------------------------------
--
--  Design        : i.MX signal to Wishbone bus wrapper
--
--  File          : imx_wrapper.vhd
--
--  Related files : (none)
--
--  Author(s)     : Fabrice Mousset (fabrice.mousset@laposte.net)
--
--  Creation Date : 2007/01/05
--
--  Abstract      : The i.MX wrapper convert i.MX signal to Wishbone master interface.
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
    Entity imx_wrapper is
-- ----------------------------------------------------------------------------
    port
    (
      -- i.MX Signals
      imx_cs_n    : in    std_logic;
      imx_oe_n    : in    std_logic;
      imx_eb3_n   : in    std_logic;
      imx_address : in    std_logic_vector(12 downto 1);
      imx_data    : inout std_logic_vector(15 downto 0);

      -- Global Signals
      gls_clk   : in std_logic;
      gls_reset : in std_logic;

      -- Wishbone interface signals
      wbm_m1_ADDR_O : out std_logic_vector(12 downto 0);  -- Address bus
      wbm_m1_DATA_I : in  std_logic_vector(15 downto 0);  -- Data bus for read access
      wbm_m1_DATA_O : out std_logic_vector(15 downto 0);  -- Data bus for write access
      wbm_m1_WE_O   : out std_logic;                      -- Write access
      wbm_m1_SEL_O  : out std_logic_vector(1 downto 0);   -- Select output array
      wbm_m1_STB_O  : out std_logic;                      -- Data Strobe
      wbm_m1_ACK_I  : out std_logic;                      -- Acknowledge
      wbm_m1_CYC_O  : out std_logic                       -- Cycle
    );
    end entity;

-- ----------------------------------------------------------------------------
    Architecture RTL of imx_wrapper is
-- ----------------------------------------------------------------------------

  signal write      : std_logic;
  signal read       : std_logic;
  signal sel        : std_logic_vector(1 downto 0);
  signal strobe     : std_logic;
  signal writedata  : std_logic_vector(15 downto 0);
  signal address    : std_logic_vector(12 downto 0);

begin

  -- --------------------------------------------------------------------------
  --  External signals synchronization process
  -- --------------------------------------------------------------------------
  process(gls_clk, gls_reset)
  begin
    if(gls_reset = '1') then
      write     <= '0';
      read      <= '0';
      sel       <= "00";
      strobe    <= '0';
      writedata <= (others => '0');
      address   <= (others => '0');
    elsif(rising_edge(gls_clk)) then
      strobe    <= not (imx_cs_n) and not(imx_oe_n and imx_eb3_n);
      write     <= not (imx_cs_n or imx_eb3_n);
      read      <= not (imx_cs_n or imx_oe_n);
      address   <= imx_address & '0';
      writedata <= imx_data;
    end if;
  end process;
  
  -- Wishbone signals generation
  wbm_m1_ADDR_O <= address    when (strobe = '1') else (others => '0');
  wbm_m1_DATA_O <= writedata  when (write = '1')  else (others => '0');
  wbm_m1_STB_O  <= strobe;
  wbm_m1_WE_O   <= write;
  wbm_m1_SEL_O  <= strobe & strobe;
  wbm_m1_CYC_O  <= strobe;
  
  -- iMX data bus generation
  imx_data <= wbm_m1_readdata when(read = '1') else (others => 'Z');

end architecture RTL;
