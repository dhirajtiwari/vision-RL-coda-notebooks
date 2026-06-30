workspace "Enterprise Warranty Diagnostics" "C4 model — diagnostic-chatbot platform" {

    !identifiers hierarchical

    model {
        # People
        customer = person "Appliance Owner" "Uses web chat and submits warranty claims."
        agent = person "Contact Center Agent" "Reviews claims, approves/denies, handles escalations."
        sme = person "Knowledge Engineer" "Governs ontology, INDICATES weights, OEM blueprints."
        ops = person "Platform Ops" "Runs ETL, promotes graph batches, monitors lineage."

        # External software systems
        pimSystem = softwareSystem "PIM / PLM" "Product catalog, BOM, service manuals, OEM data." "External"
        crmSystem = softwareSystem "CRM" "Customers, registered assets, serial numbers, warranty status." "External"
        claimsSystem = softwareSystem "Claims System" "Closed claims, policies, precedents." "External"
        fsmSystem = softwareSystem "Field Service Management" "Work orders, field resolutions." "External"
        ccaas = softwareSystem "CCaaS / Case Management" "Production escalation target." "External"

        # Our software system
        diagnostics = softwareSystem "Enterprise Diagnostics Platform" "GraphRAG warranty diagnosis, dynamic troubleshooting trees, parts prediction, claim workflow, graph visualization." {
            tags "Internal"

            webApp = container "Streamlit Web Application" "Customer chat, claims UI, agent dashboard, KG explorer." "Python, Streamlit" "Web Browser" {
                tags "Container"
                chatTab = component "Chat Tab" "Invokes diagnosis pipeline." "Streamlit"
                claimsTab = component "Claims Tab" "Submit and approve/deny claims." "Streamlit"
                kgExplorer = component "KG Explorer" "Ontology, product, diagnosis subgraphs (PyVis)." "Streamlit"
                agentDash = component "Agent Dashboard" "Escalations and ETL lineage." "Streamlit"
            }

            api = container "Diagnostics REST API" "Enterprise diagnosis, claims, graph subgraph APIs." "Python, FastAPI" "REST" {
                tags "Container"
                diagnoseRoute = component "Diagnose Controller" "POST /diagnose" "FastAPI"
                claimsRoute = component "Claims Controller" "/claims/* endpoints" "FastAPI"
                graphRoute = component "Graph Controller" "GET /graph/* subgraph APIs" "FastAPI"
                healthRoute = component "Health & Lineage" "GET /health, /lineage/batches" "FastAPI"
            }

            agentRuntime = container "Diagnosis Agent Runtime" "LangGraph orchestration (in-process with API/UI)." "Python, LangGraph" {
                tags "Container"
                detectProduct = component "Detect Product" "tool_detect_product" "LangGraph node"
                runDiagnosis = component "Run Diagnosis" "tool_diagnose → GraphRAG" "LangGraph node"
                formatResponse = component "Format Response" "Formatted diagnosis text" "LangGraph node"
                handleEscalation = component "Handle Escalation" "save_escalation" "LangGraph node"
            }

            graphIntelligence = container "Graph Intelligence Library" "GraphRAG, trees, parts, visualization." "Python" {
                tags "Container"
                graphRag = component "GraphRAG" "graph_rag.py — symptom match, rank failure modes" ""
                diagEngine = component "Diagnostic Engine" "diagnostic_engine.py — NEXT_STEP trees" ""
                partsPredictor = component "Parts Predictor" "parts_predictor.py — multi-source ranking" ""
                graphViz = component "Graph Visualization" "graph_visualization.py — PyVis subgraphs" ""
            }

            integrations = container "Integration Services" "CRM, warranty, claims, case management." "Python" {
                tags "Container"
                crmEnrichment = component "CRM Enrichment" "crm_enrichment.py" ""
                warrantyElig = component "Warranty Eligibility" "warranty_eligibility.py" ""
                claimsWorkflow = component "Claims Workflow" "claims_workflow.py" ""
                caseMgmt = component "Case Management" "case_management.py" ""
            }

            etlBatch = container "ETL Batch Pipeline" "Extract, transform, load, smoke, promote." "Python CLI / CronJob" {
                tags "Container"
                orchestrator = component "Orchestrator" "orchestrator.py" ""
                knowledgeEtl = component "Knowledge ETL" "knowledge_etl.py" ""
                ontologyBuilder = component "Ontology Builder" "ontology_builder.py" ""
                pimSync = component "PIM Blueprint Sync" "pim_blueprint_sync.py" ""
                connectors = component "Enterprise Connectors" "pim, crm, claims, fsm connectors" ""
                smokeTest = component "Smoke Validation" "smoke_validation.py" ""
                promotion = component "Staging Promotion" "staging_promotion.py" ""
            }

            blueprintAuthoring = container "Blueprint Authoring" "OEM catalog builders (offline)." "Python" {
                tags "Container"
                oemCatalog = component "OEM Product Catalog" "oem_product_catalog.py — 10 OEM + 3 legacy" ""
                warrantyExt = component "Warranty Extensions" "warranty_catalog_extensions.py" ""
                synthGen = component "Synthetic Generator" "synthetic_data_generator.py" ""
                graphLoader = component "Graph Loader" "populate_graph.py" ""
            }

            mockEnterprise = container "Mock Enterprise API" "Simulated PIM/CRM/Claims/FSM for demo." "Python, FastAPI :8090" "REST" {
                tags "Container"
                mockPim = component "Mock PIM API" "GET /api/pim/products" ""
                mockCrm = component "Mock CRM API" "GET /api/crm/*" ""
                mockClaims = component "Mock Claims API" "GET /api/claims/closed" ""
                mockFsm = component "Mock FSM API" "GET /api/fsm/work-orders" ""
            }

            graphDb = container "Neo4j Graph Database" "Knowledge graph store." "Neo4j 5.x" "Database" {
                tags "Database"
            }

            fileStore = container "JSON File Store" "Fixtures, claims submissions, lineage, escalations." "Local filesystem / PVC" "File System" {
                tags "Database"
            }
        }

        # Relationships — people
        customer -> diagnostics.webApp "Uses" "HTTPS"
        agent -> diagnostics.webApp "Manages claims & escalations" "HTTPS"
        sme -> diagnostics.blueprintAuthoring "Authors OEM blueprints" ""
        ops -> diagnostics.etlBatch "Runs pipelines" "CLI/K8s CronJob"

        # External systems (production targets)
        diagnostics.etlBatch -> pimSystem "Extracts catalog" "HTTPS/JSON"
        diagnostics.etlBatch -> fsmSystem "Extracts resolutions" "HTTPS/JSON"
        diagnostics.etlBatch -> claimsSystem "Extracts closed claims" "HTTPS/JSON"
        diagnostics.integrations -> crmSystem "Runtime asset bind" "HTTPS/JSON"
        diagnostics.integrations -> claimsSystem "Warranty policies" "HTTPS/JSON"
        diagnostics.integrations -> ccaas "Escalation handoff" "HTTPS" {
            tags "Production"
        }

        # Internal container relationships
        diagnostics.webApp -> diagnostics.agentRuntime "Invokes" "Python"
        diagnostics.webApp -> diagnostics.integrations "Claims & CRM" "Python"
        diagnostics.webApp -> diagnostics.graphIntelligence "Graph viz" "Python"
        diagnostics.api -> diagnostics.agentRuntime "POST /diagnose" "Python"
        diagnostics.api -> diagnostics.integrations "Claims, CRM, warranty" "Python"
        diagnostics.api -> diagnostics.graphIntelligence "GET /graph/*" "Python"
        diagnostics.agentRuntime -> diagnostics.graphIntelligence "Diagnose" "Python"
        diagnostics.graphIntelligence -> diagnostics.graphDb "Reads" "Bolt/Cypher"
        diagnostics.integrations -> diagnostics.graphDb "Reads/MERGE" "Bolt/Cypher"
        diagnostics.integrations -> diagnostics.fileStore "Reads/writes JSON" "File I/O"
        diagnostics.agentRuntime -> diagnostics.fileStore "Escalations" "File I/O"
        diagnostics.etlBatch -> diagnostics.mockEnterprise "Demo fetch" "HTTP"
        diagnostics.etlBatch -> diagnostics.graphDb "MERGE load" "Bolt/Cypher"
        diagnostics.etlBatch -> diagnostics.fileStore "Fixtures & lineage" "File I/O"
        diagnostics.blueprintAuthoring -> diagnostics.fileStore "Writes pim_catalog.json" "File I/O"
        diagnostics.blueprintAuthoring -> diagnostics.graphDb "populate_graph" "Bolt/Cypher"
        diagnostics.etlBatch -> diagnostics.blueprintAuthoring "Uses OEM fixtures" ""
    }

    views {
        systemContext diagnostics "C4-L1-SystemContext" {
            include *
            autolayout lr
        }

        container diagnostics "C4-L2-Containers" {
            include *
            autolayout tb
        }

        component diagnostics.api "C4-L3-API-Components" {
            include element.parent==diagnostics.api
            include diagnostics.agentRuntime
            include diagnostics.graphIntelligence
            include diagnostics.integrations
            include diagnostics.graphDb
            autolayout lr
        }

        component diagnostics.webApp "C4-L3-WebApp-Components" {
            include element.parent==diagnostics.webApp
            include diagnostics.agentRuntime
            include diagnostics.integrations
            include diagnostics.graphIntelligence
            autolayout lr
        }

        component diagnostics.etlBatch "C4-L3-ETL-Components" {
            include element.parent==diagnostics.etlBatch
            include diagnostics.blueprintAuthoring
            include diagnostics.mockEnterprise
            include diagnostics.graphDb
            include diagnostics.fileStore
            autolayout tb
        }

        component diagnostics.graphIntelligence "C4-L3-GraphIntelligence-Components" {
            include element.parent==diagnostics.graphIntelligence
            include diagnostics.graphDb
            autolayout lr
        }

        component diagnostics "C4-L3-Platform-Components" {
            include *
            autolayout tb
        }

        deployment diagnostics "Production" "C4-Deployment-Kubernetes" {
            deploymentNode customerDevice "Customer Device" "Web Browser" {
                tags "Deployment"
            }
            deploymentNode k8s "Kubernetes Cluster" "Cloud" {
                deploymentNode staging "diagnostics-staging" "Namespace" {
                    containerInstance diagnostics.webApp
                    containerInstance diagnostics.api
                    containerInstance diagnostics.mockEnterprise
                    containerInstance diagnostics.graphDb
                }
                deploymentNode prod "diagnostics-prod" "Namespace" {
                    containerInstance diagnostics.webApp
                    containerInstance diagnostics.api
                    containerInstance diagnostics.graphDb
                }
            }
            customerDevice -> staging.diagnostics.webApp "HTTPS"
        }

        dynamic diagnostics "C4-Dynamic-Diagnosis" "Diagnosis request flow" {
            customer -> diagnostics.webApp "1. Enters symptom"
            diagnostics.webApp -> diagnostics.api "2. POST /diagnose (optional)"
            diagnostics.api -> diagnostics.integrations "3. CRM enrich + warranty gate"
            diagnostics.api -> diagnostics.agentRuntime "4. run_diagnosis()"
            diagnostics.agentRuntime -> diagnostics.graphIntelligence "5. GraphRAG + trees + parts"
            diagnostics.graphIntelligence -> diagnostics.graphDb "6. Cypher queries"
            diagnostics.agentRuntime -> diagnostics.webApp "7. DiagnosisResponse"
        }

        dynamic diagnostics "C4-Dynamic-Claim" "Claim submission flow" {
            agent -> diagnostics.webApp "1. Submit claim"
            diagnostics.webApp -> diagnostics.api "2. POST /claims/submit"
            diagnostics.api -> diagnostics.agentRuntime "3. run_diagnosis()"
            diagnostics.api -> diagnostics.integrations "4. submit_claim_from_diagnosis()"
            diagnostics.integrations -> diagnostics.fileStore "5. claims_submissions.json"
            diagnostics.integrations -> diagnostics.graphDb "6. MERGE Claim"
        }

        dynamic diagnostics "C4-Dynamic-ETL" "ETL batch flow" {
            ops -> diagnostics.blueprintAuthoring "1. Sync OEM blueprints"
            diagnostics.blueprintAuthoring -> diagnostics.fileStore "2. pim_catalog.json"
            ops -> diagnostics.etlBatch "3. Run orchestrator"
            diagnostics.etlBatch -> diagnostics.mockEnterprise "4. Connector fetch"
            diagnostics.etlBatch -> diagnostics.graphDb "5. populate_graph MERGE"
            diagnostics.etlBatch -> diagnostics.fileStore "6. lineage audit"
        }

        styles {
            element "Person" {
                shape Person
                background #08427B
                color #ffffff
            }
            element "Software System" {
                background #1168BD
                color #ffffff
            }
            element "Container" {
                background #438DD5
                color #ffffff
            }
            element "Component" {
                background #85BBF0
                color #000000
            }
            element "Database" {
                shape Cylinder
                background #438DD5
            }
            element "External" {
                background #999999
                color #ffffff
            }
        }
    }
}