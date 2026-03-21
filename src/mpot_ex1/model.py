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
            for i in range1(1, N)
            for j in range1(1, N) if i != j],
        vtype=GRB.BINARY,
        name="x"
    )

    # reference to relevant variables for later use outside this function (e.g., reading solutions)
    # common variables
    model._x = x

    # create common constraints
    # see, e.g., https://docs.gurobi.com/projects/optimizer/en/current/reference/python/model.html#Model.addConstr

    # common constraints here
    model.addConstrs((sum(x[i, j] for j in range1(1, N) if i != j) == 1
        for i in range1(1, N)), name="leaving")

    model.addConstrs((sum(x[j, i] for j in range1(1, N) if i != j) == 1
        for i in range1(1, N)), name="entering")

    # Objective
    model.setObjective(
        sum(graph[i][j]["weight"] * x[i, j]
        for i in range1(1, N)
        for j in range1(1, N)
        if i != j), GRB.MINIMIZE)

    # create model-specific variables and constraints

    # SEQ
    if formulation == "seq":
        u = model.addVars(
            [i for i in range1 (2, N)],
            lb=1,
            ub=N-1,
            vtype=GRB.CONTINUOUS,
            name="order"
        )
        # TODO add your SEQ constraints here
        model.addConstrs(((u[i] + x[i, j]) <= (u[j] + (N-2) * (1-x[i, j]))
            for i in range1(2, N)
            for j in range1(2, N) if i != j),
            name="ordering")

    # SCF
    elif formulation == "scf":
        # TODO add your SCF constraints here
        f = model.addVars(
            [(i, j)
                for i in range1(1, N)
                for j in range1(1, N)
                if i != j],
            lb=0,
            ub=N-1,
            vtype=GRB.CONTINUOUS,
            name="flow"
        )
        model.addConstr(sum(f[1, j] for j in range1(2, N)) == N-1,
            name="first_city_flow"
        )
        model.addConstrs(
            ((sum(f[j, i] for j in range1(1, N) if j != i) - sum(f[i, j] for j in range1(1, N) if j!=i)) == 1
            for i in range1(2, N)),
            name="one_unit_per_flow"
        )
        model.addConstrs(
            (f[i, j] <= (N-1) * x[i, j]
                for i in range1(1, N)
                for j in range(1, N)
                if i != j),
            name="flow_if_travel"
        )

    # MCF
    elif formulation == "mcf":
        # TODO add your MCF constraints here
        f = model.addVars(
            [(i, j, k)
                for i in range1(1, N)
                for j in range1(1, N)
                for k in range1(2, N)
                if i != j],
            lb=0,
            ub=1,
            vtype=GRB.CONTINUOUS,
            name="flow"
        )

        model.addConstrs(
            ((sum(f[1, j, k] for j in range1(2, N)) - sum(f[j, 1, k] for j in range1(2, N))) == 1
                for k in range(2, N)),
            name="first_city_flow")

        model.addConstrs(
            ((sum(f[k, j, k] for j in range1(1, N) if j!=k) - sum(f[j, k, k] for j in range1(1, N) if j!=k)) == -1
                for k in range(2, N)),
            name="city_k_flow"
        )

        model.addConstrs(
            ((sum(f[i, j, k] for j in range1(1, N) if j!=i) - sum(f[j, i, k] for j in range1(1, N) if j!=i)) == 0
                for i in range(2, N)
                for k in range(2, N)
                if i != k),
            name="onward_flow"
        )

        model.addConstrs(
            (f[i, j, k] <= x[i, j]
            for i in range(1, N)
            for j in range(1, N)
            for k in range(2, N)
            if i != j),
            name="flow_if_travel"
        )

def range1(start, end):
    return range(start, end+1)
