import ast
import math
import random
from dataclasses import dataclass
from typing import Any, Callable, Dict

from flask import Flask, jsonify, render_template, request


@dataclass
class BlackScholesInput:
    spot: float
    strike: float
    rate: float
    volatility: float
    maturity: float
    simulations: int
    payoff_expression: str


class SafeExpressionEvaluator:
    """Safely evaluate limited Python expressions for custom payoffs."""

    allowed_nodes = {
        "Expression",
        "BinOp",
        "UnaryOp",
        "Add",
        "Sub",
        "Mult",
        "Div",
        "Pow",
        "Mod",
        "FloorDiv",
        "USub",
        "UAdd",
        "Constant",
        "Name",
        "Call",
        "Load",
        "Compare",
        "Gt",
        "GtE",
        "Lt",
        "LtE",
        "Eq",
        "NotEq",
        "BoolOp",
        "And",
        "Or",
        "IfExp",
    }

    allowed_names: Dict[str, Any] = {
        "abs": abs,
        "max": max,
        "min": min,
        "exp": math.exp,
        "log": math.log,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "pi": math.pi,
        "e": math.e,
    }

    def __init__(self, additional_names: Dict[str, Any] | None = None) -> None:
        self.names = dict(self.allowed_names)
        if additional_names:
            self.names.update(additional_names)

    def _validate_ast(self, node: ast.AST) -> None:
        node_name = type(node).__name__
        if node_name not in self.allowed_nodes:
            raise ValueError(f"Unsupported expression element: {node_name}")
        for child in ast.iter_child_nodes(node):
            self._validate_ast(child)

    def build(self, expression: str) -> Callable[[Dict[str, float]], float]:
        parsed = ast.parse(expression, mode="eval")
        self._validate_ast(parsed)

        def evaluator(variables: Dict[str, float]) -> float:
            local_names = dict(self.names)
            local_names.update(variables)
            return eval(compile(parsed, "<payoff>", "eval"), {"__builtins__": {}}, local_names)

        return evaluator


def simulate_price(params: BlackScholesInput) -> float:
    payoff_fn = SafeExpressionEvaluator(
        {"K": params.strike, "r": params.rate, "sigma": params.volatility, "T": params.maturity}
    ).build(params.payoff_expression)

    drift = (params.rate - 0.5 * params.volatility**2) * params.maturity
    diffusion_scale = params.volatility * math.sqrt(params.maturity)

    total = 0.0
    for _ in range(params.simulations):
        z = random.gauss(0, 1)
        st = params.spot * math.exp(drift + diffusion_scale * z)
        total += payoff_fn({"ST": st})

    discounted_average = math.exp(-params.rate * params.maturity) * total / params.simulations
    return discounted_average


def parse_request(req: Dict[str, str]) -> BlackScholesInput:
    return BlackScholesInput(
        spot=float(req.get("spot", 0)),
        strike=float(req.get("strike", 0)),
        rate=float(req.get("rate", 0)),
        volatility=float(req.get("volatility", 0)),
        maturity=float(req.get("maturity", 0)),
        simulations=int(req.get("simulations", 10000)),
        payoff_expression=req.get("payoff_expression", "max(ST - K, 0)"),
    )


app = Flask(__name__)


@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.route("/price", methods=["POST"])
def price() -> Any:
    try:
        params = parse_request(request.form)
        price_value = simulate_price(params)
        return jsonify({"price": price_value})
    except Exception as exc:  # pragma: no cover - simple error passthrough
        return jsonify({"error": str(exc)}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
