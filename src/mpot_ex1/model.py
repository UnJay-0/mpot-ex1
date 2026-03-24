import networkx as nx
from gurobipy import GRB, Model, quicksum


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
            for i in range(1, N+1)
            for j in range(1, N+1) if i != j],
        vtype=GRB.BINARY,
        name="x"
    )

    # reference to relevant variables for later use outside this function (e.g., reading solutions)
    # common variables
    model._x = x

    # create common constraints
    # see, e.g., https://docs.gurobi.com/projects/optimizer/en/current/reference/python/model.html#Model.addConstr

    # common constraints here
    model.addConstrs((quicksum(x[i, j] for j in range(1, N+1) if i != j) == 1
        for i in range(1, N+1)), name="leaving")

    model.addConstrs((quicksum(x[j, i] for j in range(1, N+1) if i != j) == 1
        for i in range(1, N+1)), name="entering")

    # Objective
    model.setObjective(
        sum(graph[i][j]["weight"] * x[i, j]
        for i in range(1, N+1)
        for j in range(1, N+1)
        if i != j), GRB.MINIMIZE)

    # create model-specific variables and constraints

    # SEQ
    if formulation == "seq":
        u = model.addVars(
            list(range(2, N+1)),
            lb=1,
            ub=N-1,
            vtype=GRB.CONTINUOUS,
            name="order"
        )
        model.addConstrs(((u[i] + x[i, j]) <= (u[j] + (N-2) * (1-x[i, j]))
            for i in range(2, N+1)
            for j in range(2, N+1) if i != j),
            name="ordering")

    # SCF
    elif formulation == "scf":
        f = model.addVars(
            [(i, j)
                for i in range(1, N+1)
                for j in range(1, N+1)
                if i != j],
            lb=0,
            ub=N-1,
            vtype=GRB.CONTINUOUS,
            name="flow"
        )
        model.addConstr(quicksum(f[1, j] for j in range(2, N+1)) == N-1,
            name="first_city_flow"
        )
        model.addConstrs(
            ((quicksum(f[j, i] for j in range(1, N+1) if j != i) - quicksum(f[i, j] for j in range(1, N+1) if j!=i)) == 1
            for i in range(2, N+1)),
            name="one_unit_per_flow"
        )
        model.addConstrs(
            (f[i, j] <= (N-1) * x[i, j]
                for i in range(1, N+1)
                for j in range(1, N+1)
                if i != j),
            name="flow_if_travel"
        )

    # MCF
    elif formulation == "mcf":
        f = model.addVars(
            [(i, j, k)
                for i in range(1, N+1)
                for j in range(1, N+1)
                for k in range(2, N+1)
                if i != j],
            lb=0,
            ub=1,
            vtype=GRB.CONTINUOUS,
            name="flow"
        )

        model.addConstrs(
            ((quicksum(f[1, j, k] for j in range(2, N+1)) - quicksum(f[j, 1, k] for j in range(2, N+1))) == 1
                for k in range(2, N+1)),
            name="first_city_flow")

        model.addConstrs(
            ((quicksum(f[k, j, k] for j in range(1, N+1) if j!=k) - quicksum(f[j, k, k] for j in range(1, N+1) if j!=k)) == -1
                for k in range(2, N+1)),
            name="city_k_flow"
        )

        model.addConstrs(
            ((quicksum(f[i, j, k] for j in range(1, N+1) if j!=i) - quicksum(f[j, i, k] for j in range(1, N+1) if j!=i)) == 0
                for i in range(2, N+1)
                for k in range(2, N+1)
                if i != k),
            name="onward_flow"
        )

        model.addConstrs(
            (f[i, j, k] <= x[i, j]
                for i in range(1, N+1)
                for j in range(1, N+1)
                for k in range(2, N+1)
                if i != j),
            name="flow_if_travel"
        )
