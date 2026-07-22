from Source.Core.Knowledge.project_graph import ProjectGraph

g = ProjectGraph()

print("=" * 60)

print(g.inherits("BallChainManager"))

print("=" * 60)

print(g.uses("BallChainManager"))

print("=" * 60)

print(g.namespaces("BallChainManager"))

print("=" * 60)

print(g.find_component("AudioSource"))

print("=" * 60)

print(g.find_base("MonoBehaviour"))
