import gurobipy as gp
import networkx as nx
from gurobipy import GRB, Model


def create_model(model: Model):
    graph: nx.DiGraph = model._graph
    formulation: str = model._formulation

    # see, e.g., https://docs.gurobi.com/projects/optimizer/en/current/reference/python.html

    print(f"{graph.number_of_nodes()=}, {graph.number_of_edges()=}")
    N = graph.number_of_nodes() # Number of cities


    # create common variables
    # see, e.g., https://docs.gurobi.com/projects/optimizer/en/current/reference/python/model.html#Model.addVars

    # common variables here
    x = model.addVars(
        [(i, j)
            for i in range(1, N)
            for j in range(1, N) if i != j],
        vtype=GRB.BINARY,
        name="x"
    )

    # reference to relevant variables for later use outside this function (e.g., reading solutions)
    # common variables
    model._x = x

    # create common constraints
    # see, e.g., https://docs.gurobi.com/projects/optimizer/en/current/reference/python/model.html#Model.addConstr

    # common constraints here
    model.addConstrs((sum(x[i, j] for j in range(1, N) if i != j) == 1
        for i in range(1, N)), name="leaving")

    model.addConstrs((sum(x[j, i] for j in range(1, N) if i != j) == 1
        for i in range(1, N)), name="entering")

    # Objective
    model.setObjective(
        sum(graph[i][j]["weight"] * x[i, j]
        for i in range(1, N)
        for j in range(1, N)
        if i != j), GRB.MINIMIZE)

    # create model-specific variables and constraints

    # SEQ
    if formulation == "seq":
        u = model.addVars(
            [i for i in range (2, N)],
            lb=1,
            ub=N-1,
            vtype=GRB.CONTINUOUS,
            name="order"
        )
        # TODO add your SEQ constraints here
        model.addConstrs(((u[i] + x[i, j]) <= (u[j] + (N-2) * (1-x[i, j]))
            for i in range(2, N)
            for j in range(2, N) if i != j),
            name="ordering")

    # SCF
    elif formulation == "scf":
        # TODO add your SCF constraints here
        pass

    # MCF
    elif formulation == "mcf":
        # TODO add your MCF constraints here
        pass
