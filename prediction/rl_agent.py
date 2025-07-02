from stable_baselines3 import PPO
import gym

class RLAgent:
    def __init__(self, env_name="CartPole-v1"):
        self.env = gym.make(env_name)
        self.model = PPO("MlpPolicy", self.env, verbose=0)

    def train(self, timesteps=10000):
        self.model.learn(total_timesteps=timesteps)

    def predict(self, obs):
        action, _ = self.model.predict(obs)
        return action

    def save(self, path):
        self.model.save(path)

    def load(self, path):
        self.model = PPO.load(path)
