"""Only the router transition-cost anchor uses a current-pixel wheel proxy."""
from retry.wheel304_base import Agent as FrozenAgent
from retry.hud248_features import decode
from retry import connected_agent as router
class Agent(FrozenAgent):
 def act(self,observation):
  router.RANKING_WHEEL_PROXY=-float(decode(observation[-1])[4])
  return super().act(observation)
