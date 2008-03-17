-- -----------------------------------------------------------------------------
-- Projet SyCOE
-- -----------------------------------------------------------------------------
-- Nom du fichier  : relais_mos.vhd
-- Description     : Module de commandes de sorties relais ou mos.
-- Date            : 03/05/2007
-- Auteur          : Gwenaël Jaouen
-- Version         : v0.01
-- -----------------------------------------------------------------------------

-- -----------------------------------------------------------------------------
-- Librarie
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- -----------------------------------------------------------------------------
-- Entité
-- -----------------------------------------------------------------------------

entity relais_mos is
  generic
  (
    nb_out : integer := 3;
    recovery_delay : integer := 3
  );

  port
  (
    -- Signaux globaux
    reset     : in  std_logic;
    clk       : in  std_logic;
  
    -- Signaux de contrôle
    data    : in std_logic_vector(nb_out - 1 downto 0);
    set     : in std_logic;
    busy    : out std_logic;
    error   : out std_logic;
    stop    : in std_logic;
    top1ms  : in std_logic;

    -- Signaux d'état réel des sorties
    status : out std_logic_vector(nb_out -1 downto 0);

    -- Signaux de commande des sorties
    command : out std_logic_vector(nb_out - 1 downto 0);
    watch   : in std_logic_vector(nb_out - 1 downto 0)
  );
end relais_mos ;

-- -----------------------------------------------------------------------------
-- Architecture
-- -----------------------------------------------------------------------------

architecture RTL of relais_mos is

  -- Machine d'état

  type State_t is (s_idle, s_wait_watch);
  signal state : State_t;

  -- Image des signaux en entrée

  signal watch_r       : std_logic_vector((nb_out - 1) downto 0);
  signal recovery_cpt  : integer range 0 to recovery_delay;
  
  signal busy_i : std_logic;

begin

  busy <= busy_i;

-- -----------------------------------------------------------------------------
-- Process de synchronisation des signaux en entrée
-- -----------------------------------------------------------------------------

SYNCHRO : process (clk, reset)
begin

  -- Signal reset actif : les signaux sont maintenus dans leur état par défaut
  -- ---------------------------------------------------------------------------

  if reset = '1' then
    watch_r  <= (others => '0');

  -- Front montant sur l'horloge globale : synchronisation des signaux d'entrée
  -- ---------------------------------------------------------------------------

  elsif rising_edge (clk) then
    watch_r  <= watch;
  end if;
end process SYNCHRO;

-- -----------------------------------------------------------------------------
-- Process machine d'état
-- -----------------------------------------------------------------------------

STATE_MACHINE : process (clk, reset)
begin

  -- Signal reset actif : on positionne tous les signaux avec leur valeur par
  -- défaut.
  -- ---------------------------------------------------------------------------

  if reset = '1' then
    state         <= s_idle;
    command       <= (others => '0');
    recovery_cpt  <= 0;
    busy_i        <= '0';
    error         <= '0';
    status        <= (others => '0');

  -- Front montant sur l'horloge 50 MHz : gestion de la machine d'état
  -- ---------------------------------------------------------------------------

  elsif rising_edge (clk) then

  -- Remise à zéro des signaux qui ont pu être activé lors du dernier passage
  -- dans la machine d'état. Cela permet de pouvoir générer sur ces signaux
  -- des impulsions d'une durée équivalente à une période de l'horloge
  -- globale.
  -- ---------------------------------------------------------------------------

--  error <= '0';

  -- Le signal busy est toujours actif, il n'est à 0 que lorsque la machine
  -- d'état est en idle
  -- ---------------------------------------------------------------------------
  
  busy_i <= '1';

  -- Gestion du signal stop demandant l'arret de la commande en cours.
  -- ---------------------------------------------------------------------------
  
  if stop = '1' then
    state <= s_idle;
  end if;
  
  -- Mise à jour du status avec l'état réel des sorties. Cette maj est réalisée
  -- uniquement lorsque le module n'est pas en train de commander les sorties
  -- c'est à dire lorsque la machine d'état est dans la phase idle.
  -- ---------------------------------------------------------------------------

  if state = s_idle then
    status <= watch_r;
  end if;

  -- Gestion de la machine d'état
  -- ---------------------------------------------------------------------------

    case state is
      
      -- s_idle : état à la sortie du reset et suite à une programmation des
      -- sortie. Dans cet état, il faut attendre l'activation du signal set 
      -- pour lancer une programmation des sorties. Une fois que les sorties 
      -- sont programméees, on passe à l'état s_wait_watch.
      -- -----------------------------------------------------------------------

      when s_idle =>
        if set = '1' then
          command       <= data;
          recovery_cpt  <= 0;
          state         <= s_wait_watch;
          error         <= '0';
        else
          busy_i <= '0';
        end if;
       
      -- s_wait_watch : qui permet d'attendre le temps "recovery_delay" avant 
      -- de vérifier que les sorties ont été correctement programmé. Le temps
      -- d'attente est décompté grâce au tops 1ms. Si à la fin de ce temps,
      -- les valeurs de retours sont différentes des valeurs programmées, on
      -- génére une erreur.
      -- -----------------------------------------------------------------------

      when s_wait_watch =>
        if top1ms = '1' then
          if (recovery_cpt = recovery_delay) then
            if data /= watch_r then
              error <= '1';
            end if;
            state <= s_idle;
          else
            recovery_cpt <= recovery_cpt + 1;
          end if;
        end if;
    end case;
  end if;
end process STATE_MACHINE;

end RTL;


