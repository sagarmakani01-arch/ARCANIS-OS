from .database import Database


class KnowledgeEngine:
    def __init__(self):
        self.db = Database()

    def learn(self, concept, description="", category="general"):
        cid = self.db.add_concept(concept, description, category)
        self.db.add_memory(f"Learned concept: {concept}", "knowledge", category)
        return cid

    def relate(self, source, target, rel_type="related", weight=1.0):
        rc = self.db.add_relation(source, target, rel_type, weight)
        if rc:
            self.db.add_memory(f"Related '{source}' → '{target}' ({rel_type})", "knowledge")
        return rc

    def search(self, query, limit=20):
        return self.db.get_concepts(query, limit)

    def get_all_concepts(self):
        return self.db.get_concepts()

    def get_all_relations(self):
        return self.db.get_relations()

    def get_graph_data(self):
        concepts = self.get_all_concepts()
        relations = self.get_all_relations()
        nodes = [{"id": c["id"], "name": c["name"], "category": c["category"]} for c in concepts]
        edges = [{"source": r["source_name"], "target": r["target_name"], "type": r["relation_type"]} for r in relations]
        return nodes, edges

    def add_memory(self, content, source="system", context="", level="info"):
        return self.db.add_memory(content, source, context, level)

    def get_memories(self, limit=50):
        return self.db.get_memories(limit)

    def get_stats(self):
        return self.db.get_stats()
