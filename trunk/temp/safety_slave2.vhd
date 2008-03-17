-- Projet SyCOE - Gestion de la boucle de s�curit� 
-- -----------------------------------------------------------------------------
-- Nom du fichier  : safety_slave.vhd
-- Description     : Composant esclave de la boucle de s�curit� interne implant�
--                  sur les cartes iDecision d'un rack
-- Date            : 11/12/2007
-- Auteur          : Fabrice Mousset
-- Version         : v1.00
-- -----------------------------------------------------------------------------

-- -----------------------------------------------------------------------------
--  Chargement des libraries
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.std_logic_unsigned.all;

-- -----------------------------------------------------------------------------
--  D�claration de l'entit�
-- -----------------------------------------------------------------------------

entity safety_slave is
  generic
  (
    t_alarm   : integer := 56   -- 750ns @ 75 MHz
  );
  port
  (
    reset       : in  std_logic;
    clk         : in  std_logic;
    
    safety_in   : in  std_logic;
    safety_out  : out std_logic;
    protect     : in  std_logic;
    ack         : in  std_logic;
    alarm       : out std_logic
  );
end entity; 

-- -----------------------------------------------------------------------------
--  D�claration de l'architecture
-- -----------------------------------------------------------------------------

architecture RTL of safety_slave is

  -- Machine d'�tats
  type safetyFSM_t is (sNormal, sProtect, sAlarm);
  signal safetyFSM : safetyFSM_t;

  -- Signaux pour la gestion de l'entr�e SafetyLoop interne
  signal safety_in_i  : std_logic;
  signal sl_alarm_cnt : integer range 0 to t_alarm - 1;
  signal sl_alarm     : std_logic;
  signal sl_ok        : std_logic;

  signal safety_in_r  : std_logic_vector(1 downto 0);
  signal safety_in_ir : std_logic;
  
  signal protect_r    : std_logic;
begin

  -- ---------------------------------------------------------------------------
  --  SAFETY : Process de gestion de l'�tat de boucle de s�curit�
  -- ---------------------------------------------------------------------------
  SAFETY : process(clk, reset)
  begin
    if(reset = '1') then
      safety_in_r   <= "00";
      safety_in_i   <= '0';
      safety_in_ir  <= '0';
      sl_alarm_cnt  <= 0;
      sl_alarm      <= '0';
      sl_ok         <= '0';
      protect_r     <= '0';

    elsif(rising_edge(clk)) then
    
      protect_r <= protect;

      -- Double synchronisation sur le signal safety_in
      safety_in_r(0)  <= safety_in;
      safety_in_r(1)  <= safety_in_r(0);
      if(safety_in_r(0) = safety_in_r(1)) then
        safety_in_i <= safety_in_r(1);
      end if;
      
      -- D�tection des changements de phase sur l'entr�e SafetyLoop
      safety_in_ir <= safety_in_i;
      if(safety_in_ir /= safety_in_i) then
        sl_ok         <= '1';
        sl_alarm      <= not sl_ok;
        sl_alarm_cnt  <= t_alarm - 1;
        if(sl_alarm_cnt = 0) then
          sl_ok     <= '0';
          sl_alarm  <= '1';
        end if;
        -- MAJ de la mesure de la p�riode du signal de la SafetyLoop
      elsif(sl_alarm_cnt /= 0) then
        sl_alarm_cnt <= sl_alarm_cnt - 1;
      else
        sl_alarm <= '1';
      end if;
    end if;
  end process;

  -- ---------------------------------------------------------------------------
  --  FSM : Process de gestion de la machine d'�tat de la boucle de s�curit�
  -- ---------------------------------------------------------------------------
  FSM : process(clk, reset)
  begin
    if(reset = '1') then
      safetyFSM   <= sNormal;
      safety_out  <= '0';
      alarm       <= '0';
    elsif(rising_edge(clk)) then
    
      -- Gestion de la machine d'�tat
      case safetyFSM is
        -- sNormal : Etat normal, aucun syst�me en alarme
        --  * MAJ du signal de sortie SafetyLoop avec l'�tat de l'entr�e
        --  * RAZ du signal d'alarme
        --  * Attente d'une protection ou d'une alarme
        when sNormal =>
          safety_out  <= safety_in_i;
          alarm       <= '0';
          
          -- La mise en protection est prioritaire par rapport � l'alarme
          if(protect = '1') then
            safetyFSM <= sProtect;
          elsif(sl_alarm = '1') then
            safetyFSM <= sAlarm;            
          end if;
        
        -- sAlarm : Au moins une carte iDecision du rack en protection
        --  * MAJ du signal de sortie SafetyLoop avec l'�tat de l'entr�e
        --  * Signal d'alarme forc� � '1' (�tat actif)
        --  * D�tection de la fin de l'alarme et passage en mode normal
        when sAlarm =>
          safety_out  <= safety_in_i;
          alarm       <= '1';
          
          -- D�tection de la fin d'une alarme
          if(protect_r = '1') then
            safetyFSM <= sProtect;
          elsif(sl_alarm = '0') then
            safetyFSM <= sNormal;
          end if;

        -- sProtect : Mise en protection du syst�me
        --  * RAZ de la sortie Alarme
        --  * Attente de l'acquittement de l'alarme
        when sProtect =>
          alarm <= '0';
          
          -- Quand la mise en protection par SafetyLoop externe est acquitt�e on
          -- passe en phase de recouvrement de la boucle de s�curit� interne.
          if(ack = '1') then
            safetyFSM <= sNormal;
          end if;
        
      end case;
    end if;
  end process;
end architecture;
