// ==============================================================================
// Polyglot Pharma Supply Chain - Neo4j Graph Sanity Checks & Verification Suite
// ==============================================================================

// ------------------------------------------------------------------------------
// Check 1: Zero Orphan Nodes Verification
// Expectation: orphan_count == 0 (Every node participates in the supply network)
// ------------------------------------------------------------------------------
MATCH (n)
WHERE NOT (n)--()
RETURN count(n) AS orphan_count, collect(head(labels(n)))[0..5] AS sample_orphan_labels;


// ------------------------------------------------------------------------------
// Check 2: Scale-Free Degree Distribution of Top Manufacturer Hubs
// Expectation: Power-law hub structure where top manufacturers have high out-degree
// ------------------------------------------------------------------------------
MATCH (m:Manufacturer)
OPTIONAL MATCH (m)-[:SUPPLIES]->(dist:Distributor)
OPTIONAL MATCH (m)-[:PRODUCES]->(dr:Drug)
WITH m.name AS manufacturer, 
     count(DISTINCT dist) AS supplied_distributors,
     count(DISTINCT dr) AS produced_drugs,
     (count(DISTINCT dist) + count(DISTINCT dr)) AS total_degree
RETURN manufacturer, supplied_distributors, produced_drugs, total_degree
ORDER BY total_degree DESC
LIMIT 10;


// ------------------------------------------------------------------------------
// Check 3: Multi-Hop Supply Lineage Path Verification (Manufacturer -> Distributor -> Pharmacy)
// Expectation: At least one 3-hop end-to-end path exists linking manufacturer to dispensing pharmacy
// ------------------------------------------------------------------------------
MATCH path = (m:Manufacturer)-[:SUPPLIES]->(d:Distributor)-[:DISTRIBUTES_TO]->(p:Pharmacy)
RETURN m.name AS manufacturer,
       d.name AS regional_hub,
       p.name AS dispensing_pharmacy,
       p.city AS pharmacy_city,
       p.state AS pharmacy_state
LIMIT 5;


// ------------------------------------------------------------------------------
// Check 4: Therapeutic Drug Substitution Network Traversal
// Expectation: Identify interchangeable drugs sharing generic active ingredients
// ------------------------------------------------------------------------------
MATCH (d1:Drug)-[r:SUBSTITUTABLE_WITH]->(d2:Drug)
MATCH (m1:Manufacturer)-[:PRODUCES]->(d1)
MATCH (m2:Manufacturer)-[:PRODUCES]->(d2)
RETURN d1.brand_name AS primary_drug,
       m1.name AS primary_producer,
       r.generic_compound AS active_compound,
       d2.brand_name AS substitute_drug,
       m2.name AS substitute_producer
LIMIT 5;


// ------------------------------------------------------------------------------
// Check 5: End-to-End Cold-Chain Sensitive Supply Path Trace
// Expectation: Verify temperature-controlled transit routes from biological manufacturer to pharmacy
// ------------------------------------------------------------------------------
MATCH (m:Manufacturer)-[:PRODUCES]->(dr:Drug {requires_cold_chain: true})
MATCH (m)-[:SUPPLIES]->(d:Distributor {has_cold_chain_storage: true})
MATCH (d)-[distRel:DISTRIBUTES_TO]->(p:Pharmacy {has_cold_storage: true})
RETURN dr.brand_name AS cold_chain_drug,
       dr.temperature_category AS temp_spec,
       m.name AS manufacturer,
       d.name AS cold_distributor,
       p.name AS certified_pharmacy,
       distRel.delivery_frequency AS delivery_schedule
LIMIT 5;

