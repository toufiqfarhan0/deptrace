"""
Canonical HydraDB ontology and query definitions for Track 1 (EnterpriseRAG-Bench).

HydraDB uses OpenCypher. Rather than a DDL schema, we establish the ontology
by defining canonical vertex labels, relationship types, verified write patterns,
and benchmark query traversals.

HydraDB Query Engine Compatibility Rules:
1. Supported Write Pattern: Standalone single-hop relationship MERGE:
      MERGE (a:LabelA {id: INTEGER, ...})-[:REL_TYPE {id: INTEGER}]->(b:LabelB {id: INTEGER, ...})
2. Integer IDs: All vertex and edge IDs must be non-negative integers.
3. Standalone Node CREATE: Not executable in current query engine.
4. MATCH + CREATE: Not supported.
5. MERGE + SET: Not executable in current query engine.
6. Storage Backend: Local development requires CLOUD_PROVIDER=memory.
"""

from __future__ import annotations

# -------------------------------------------------------------------
# Canonical Node Labels
# -------------------------------------------------------------------

PERSON = "Person"
TEAM = "Team"
CHANNEL = "Channel"
CUSTOMER = "Customer"
PROJECT = "Project"
INCIDENT = "Incident"
MESSAGE = "Message"
DOCUMENT = "Document"
DECISION = "Decision"
CONFIGURATION_CHANGE = "ConfigurationChange"
ENTITY = "Entity"
STATEMENT = "Statement"


# -------------------------------------------------------------------
# Canonical Relationship Types
# -------------------------------------------------------------------

MEMBER_OF = "MEMBER_OF"
AUTHORED = "AUTHORED"
IN_CHANNEL = "IN_CHANNEL"
PART_OF = "PART_OF"
MENTIONS = "MENTIONS"

INVOLVED_IN = "INVOLVED_IN"
HAS_INCIDENT = "HAS_INCIDENT"

MADE = "MADE"
AFFECTS = "AFFECTS"

SUPPORTED_BY = "SUPPORTED_BY"
ABOUT = "ABOUT"
CONTRADICTS = "CONTRADICTS"

RESOLVED_BY = "RESOLVED_BY"
INVOLVES = "INVOLVES"


# -------------------------------------------------------------------
# Verified Standalone MERGE Write Patterns
# -------------------------------------------------------------------

MERGE_PERSON_INVOLVED_IN_INCIDENT = """
MERGE (p:Person {id: $person_id, name: $person_name})
-[:INVOLVED_IN {id: $rel_id}]->
(i:Incident {id: $incident_id, name: $incident_name, status: $status})
"""

MERGE_CUSTOMER_HAS_INCIDENT = """
MERGE (c:Customer {id: $customer_id, name: $customer_name})
-[:HAS_INCIDENT {id: $rel_id}]->
(i:Incident {id: $incident_id})
"""

MERGE_INCIDENT_RESOLVED_BY_CHANGE = """
MERGE (i:Incident {id: $incident_id})
-[:RESOLVED_BY {id: $rel_id}]->
(c:ConfigurationChange {id: $change_id, change_id: $change_key, description: $description})
"""


# -------------------------------------------------------------------
# Verified Graph Traversals
# -------------------------------------------------------------------

FIND_INCIDENT_PEOPLE_QUERY = """
MATCH (p:Person)-[:INVOLVED_IN]->(i:Incident)
WHERE i.id = 40001
RETURN p.name AS person
"""

FIND_CUSTOMER_INCIDENT_QUERY = """
MATCH (c:Customer)-[:HAS_INCIDENT]->(i:Incident)
WHERE c.id = 30001
RETURN
    c.name AS customer,
    i.name AS incident,
    i.status AS status
"""

FIND_INCIDENT_RESOLUTION_QUERY = """
MATCH (i:Incident)-[:RESOLVED_BY]->(c:ConfigurationChange)
WHERE i.id = 40001
RETURN
    i.name AS incident,
    c.change_id AS change_id,
    c.description AS description
"""