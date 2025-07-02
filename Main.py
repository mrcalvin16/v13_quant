from utils.logger import get_logger
from utils.config_loader import load_config
from prediction.ml_ensemble import MLEnsemble
from prediction.rl_agent import RLAgent
from prediction.ensemble_manager import EnsembleManager
from execution.equities import EquityExecutor
from execution.crypto import CryptoExecutor
from execution.options import OptionsExecutor
from execution.unified import UnifiedExecutor
from explainability.shap_explainer import SHAPExplainer

logger = get_logger("V13Main")

def main():
    config = load_config()
    logger.info("V13 Quant Engine Starting...")

    # Prediction engines
    ml = MLEnsemble()
    rl = RLAgent()
    ensemble = EnsembleManager(ml, rl, weight_ml=0.6, weight_rl=0.4)

    # Execution engines
    equity_exec = EquityExecutor(config["alpaca"])
    crypto_exec = CryptoExecutor(config["binance"])
    options_exec = OptionsExecutor(config["tradier"])
    unified_exec = UnifiedExecutor(equity_exec, crypto_exec, options_exec)

    # Load a sample input (replace with real features)
    ml_input = [0.3, 0.2, 0.1]
    rl_obs = [0.05, 0.02]

    # Predict blended signal
    prediction = ensemble.predict(ml_input, rl_obs)
    logger.info(f"Blended prediction: {prediction:.4f}")

    # Simple threshold logic
    if prediction > 0.7:
        logger.info("Submitting sample equity buy order...")
        unified_exec.submit_order("equity", "AAPL", 1, "buy")

if __name__ == "__main__":
    main()
