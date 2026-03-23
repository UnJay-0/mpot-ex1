import argparse
import os
import sys
from pathlib import Path

import gurobipy as gp
import networkx as nx
import tsplib95

from mpot_ex1.model import create_model


def read_instance(instance_path: str | os.PathLike) -> nx.DiGraph:
    problem = tsplib95.load(instance_path)
    graph = problem.get_graph()
    graph.remove_edges_from(nx.selfloop_edges(graph))
    return graph.to_directed()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ILP-based TSP solver")
    parser.add_argument(
        "--instance", type=str, required=True, help="path to instance file"
    )
    parser.add_argument("--formulation", required=True, choices=["seq", "scf", "mcf"])

    args = parser.parse_args()

    inst = Path(args.instance).stem
    model_name = f"{inst}_{args.formulation}"

    graph = read_instance(args.instance)

    # context handlers take care of disposing resources correctly
    with gp.Model(model_name) as model:
        model._graph = graph
        model._formulation = args.formulation

        create_model(model)
        model.update()

        # sanity check to ensure that the model is an ILP
        if not model.IsMIP:
            sys.exit(
                f"Error: Your formulation for '{args.formulation}' is not a (mixed) integer linear program."
            )
        if model.IsQP or model.IsQCP:
            sys.exit(f"Error: Your formulation for '{args.formulation}' is non-linear.")

        # write model to file in readable format (useful for debugging)
        # model.write(f"{model_name}.lp")

        # by default, Gurobi considers the incumbent solution to be optimal if the gap is <= 0.0001
        # this setting ensures that Gurobi doesn't stop prematurely in these cases
        model.Params.MIPGap = 0

        model.optimize()

        # TODO read solution values / attributes from `model`
        # – the number of variables (total, continuous, integer, binary),
        print(f"\nTotal number of variables: {model.NumVars}")
        print(f"Number of continous variables: {model.NumVars - model.NumIntVars}")
        print(f"Number of int variables: {model.NumIntVars - model.NumBinVars}")
        print(f"Number of binary variables: {model.NumBinVars}")
        # – the number of constraints,
        print(f"\nTotal number of constraints: {model.NumConstrs}")
        # – the required runtime and maximum memory consumption,
        print(f"Runtime: {model.Runtime}")
        print(f"Memory consumption: {model.MemUsed}")
        # – the number of branch-and-bound nodes explored,
        print(f"Number of branch-and-bound nodes explored: {model.NodeCount}")
        # – the optimal objective value, and
        print(f"Total costs: {model.ObjVal}")
        # – an optimal tour (i.e., the sequence in which the cities are visited).

        for v in model.getVars():
            if v.X:
                print('%s %g' % (v.VarName, v.X))
