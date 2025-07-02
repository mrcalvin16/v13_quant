class EnsembleManager:
    def __init__(self, ml_model, rl_model, weight_ml=0.5, weight_rl=0.5):
        self.ml_model = ml_model
        self.rl_model = rl_model
        self.weight_ml = weight_ml
        self.weight_rl = weight_rl

    def predict(self, ml_input, rl_obs):
        ml_pred = self.ml_model.predict(ml_input)
        rl_pred = self.rl_model.predict(rl_obs)

        ml_scalar = float(ml_pred) if isinstance(ml_pred, (float, int)) else float(ml_pred[0])
        rl_scalar = float(rl_pred) if isinstance(rl_pred, (float, int)) else float(rl_pred)

        blended = self.weight_ml * ml_scalar + self.weight_rl * rl_scalar
        return blended
