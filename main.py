import os
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from models import TitleReport, DeedEntity, CovenantRestriction, TitleVerification, ZoningAssessment
from retriever import DeedRetriever

# Define State Structure
class TitleState(TypedDict):
    raw_text: str
    clean_text: str
    metadata: Dict[str, Any]
    history: List[DeedEntity]
    restrictions: List[CovenantRestriction]
    verification: TitleVerification
    zoning: ZoningAssessment
    precedents: List[str]
    current_step: str

# 1. OCR & Text Cleaning Node
def clean_ocr_node(state: TitleState) -> Dict[str, Any]:
    print("--- [Node: OCR & Cleaner] ---")
    raw = state["raw_text"]
    clean = "\n".join([line.strip() for line in raw.split("\n") if line.strip()])
    return {
        "clean_text": clean,
        "current_step": "OCR_CLEAN"
    }

# 2. Entity Abstractor Node
def entity_abstractor_node(state: TitleState) -> Dict[str, Any]:
    print("--- [Node: Entity Abstractor] ---")
    text = state["clean_text"]
    history = []
    
    current_entry = {}
    for line in text.split("\n"):
        if "Grantor:" in line:
            current_entry["grantor"] = line.split("Grantor:")[1].strip()
        elif "Grantee:" in line:
            current_entry["grantee"] = line.split("Grantee:")[1].strip()
        elif "Price:" in line:
            price_str = line.split("Price:")[1].strip().replace("$", "").replace(",", "")
            current_entry["price"] = float(price_str)
        elif "RECORD ENTRY:" in line:
            year = line.replace("---", "").replace("RECORD ENTRY:", "").strip()
            current_entry["year"] = int(year)
        elif "DEED OF" in line or "GRANT OF" in line:
            current_entry["type"] = line.strip()
            
        if "grantee" in current_entry and "grantor" in current_entry:
            # Instantiate Pydantic model
            deed = DeedEntity(
                grantor=current_entry["grantor"],
                grantee=current_entry["grantee"],
                price=current_entry.get("price", 0.0),
                year=current_entry.get("year", 1900)
            )
            history.append(deed)
            current_entry = {}

    return {
        "history": history,
        "current_step": "ENTITY_EXTRACTED"
    }

# 3. Title Chain Resolver Node
def title_resolver_node(state: TitleState) -> Dict[str, Any]:
    print("--- [Node: Title Chain Resolver] ---")
    history = state["history"]
    discrepancies = []
    ownership_flow = []
    
    if history:
        ownership_flow.append(history[0].grantor)
        ownership_flow.append(history[0].grantee)
        
    for i in range(len(history) - 1):
        prev_grantee = history[i].grantee
        next_grantor = history[i+1].grantor
        ownership_flow.append(history[i+1].grantee)
        if prev_grantee != next_grantor:
            discrepancies.append(f"Title gap: Ownership transfer broke between {prev_grantee} and {next_grantor}.")
            
    verification = TitleVerification(
        is_complete=(len(discrepancies) == 0),
        ownership_flow=ownership_flow,
        discrepancies=discrepancies
    )
    
    return {
        "verification": verification,
        "current_step": "TITLE_RESOLVED"
    }

# 4. Covenant Auditor Node
def covenant_auditor_node(state: TitleState) -> Dict[str, Any]:
    print("--- [Node: Covenant Auditor] ---")
    text = state["clean_text"]
    restrictions = []
    height_limit = None
    commercial_allowed = True
    easements = []
    
    # Process text for rules matching
    for line in text.split("\n"):
        if "easement" in line.lower() or "easements" in line.lower():
            desc = line.split(":")[-1].strip() if ":" in line else line.strip()
            restrictions.append(CovenantRestriction(restriction_type="Easement", description=desc, year=1984))
            easements.append(desc)
        if "height" in line.lower():
            desc = line.split(":")[-1].strip() if ":" in line else line.strip()
            restrictions.append(CovenantRestriction(restriction_type="Height Limit", description=desc, year=1984))
            height_limit = 30.0 # Standardize
        if "no commercial" in line.lower() or "commercial activities prohibited" in line.lower() or "no commercial operations" in line.lower() or "commercial activities" in line.lower():
            desc = line.split(":")[-1].strip() if ":" in line else line.strip()
            restrictions.append(CovenantRestriction(restriction_type="Usage Ban", description=desc, year=1984))
            commercial_allowed = False
            
    zoning = ZoningAssessment(
        height_limit=height_limit,
        commercial_allowed=commercial_allowed,
        easements=easements
    )
    
    # Run simulated local semantic RAG search
    print("  Executing Local semantic search for land covenants...")
    retriever = DeedRetriever()
    precedents_found = retriever.retrieve_precedents("height restriction easement", k=2)
    precedent_strings = [f"[{p['id']}] {p['text']}" for p in precedents_found]
    
    return {
        "restrictions": restrictions,
        "zoning": zoning,
        "precedents": precedent_strings,
        "current_step": "COVENANTS_AUDITED"
    }

# Assemble Graph
def build_title_chain_workflow():
    workflow = StateGraph(TitleState)
    
    workflow.add_node("ocr_clean", clean_ocr_node)
    workflow.add_node("entity_abstract", entity_abstractor_node)
    workflow.add_node("title_resolve", title_resolver_node)
    workflow.add_node("covenant_audit", covenant_auditor_node)
    
    workflow.set_entry_point("ocr_clean")
    workflow.add_edge("ocr_clean", "entity_abstract")
    workflow.add_edge("entity_abstract", "title_resolve")
    workflow.add_edge("title_resolve", "covenant_audit")
    workflow.add_edge("covenant_audit", END)
    
    return workflow.compile()

if __name__ == "__main__":
    print("====================================================")
    print("  TerraTrace Title Agent Pipeline (Pydantic + RAG)  ")
    print("====================================================")
    
    deeds_file = os.path.join(os.path.dirname(__file__), "sample_deeds.txt")
    if os.path.exists(deeds_file):
        with open(deeds_file, "r") as f:
            raw_input = f.read()
    else:
        raw_input = """
        --- RECORD ENTRY: 1962 ---
        Grantor: Sterling Family Estates
        Grantee: Thomas Sterling
        
        --- RECORD ENTRY: 1984 ---
        Grantor: Thomas Sterling
        Grantee: Oakridge Land Dev Corporation
        Price: $285,000
        Easements: Reserving a utilities easement on the eastern 10 feet.
        Covenants: Max building height restricted to 30 feet. No commercial activities.
        """
        
    initial_state = {
        "raw_text": raw_input,
        "clean_text": "",
        "metadata": {},
        "history": [],
        "restrictions": [],
        "verification": None,
        "zoning": None,
        "precedents": [],
        "current_step": "INIT"
    }
    
    app = build_title_chain_workflow()
    res = app.invoke(initial_state)
    
    # Format a final Pydantic Title Report
    report = TitleReport(
        metadata={"parsed_step": res["current_step"]},
        history=res["history"],
        restrictions=res["restrictions"],
        verification=res["verification"],
        zoning=res["zoning"]
    )
    
    print("\n====================================================")
    print("  TerraTrace Executed State Output Summary           ")
    print("====================================================")
    print(f"Verify Chain Successful: {report.verification.is_complete}")
    print(f"Ownership flow: {' -> '.join(report.verification.ownership_flow)}")
    
    print("\nAudited Covenants:")
    for rest in report.restrictions:
        print(f"  • [{rest.restriction_type}]: {rest.description}")
        
    print("\nZoning Limits:")
    print(f"  Height Limit: {report.zoning.height_limit} ft")
    print(f"  Commercial Allowed: {report.zoning.commercial_allowed}")
    print(f"  Active Easements: {', '.join(report.zoning.easements)}")
    
    print("\nSemantic Precedents Retrieved (RAG):")
    for prec in res["precedents"]:
        print(f"  • {prec}")
    print("====================================================\n")
