import os

def fix_file(path):
    if not os.path.exists(path):
        return
    with open(path, 'r') as f:
        content = f.read()
    
    # Fix Title
    content = content.replace("Lead Architect at Symetra", "Lead Backend Engineer / Architect at Symetra")
    content = content.replace("Lead Architect @ Symetra", "Lead Backend Engineer / Architect @ Symetra")
    content = content.replace("Lead Architect", "Lead Backend Engineer / Architect") # General sweep
    
    # Fix Misrepresentation of LangGraph/RAG at Symetra
    # If it mentions LangGraph/RAG in the context of "In my current role at Symetra"
    bad_phrasing = "In my current role as Lead Backend Engineer / Architect at Symetra, I am building the 'Deterministic Harness' for agentic orchestration. My work involves designing stateful agent workflows using LangGraph and integrating RAG patterns"
    good_phrasing = "Parallel to my architectural work, I am leading R&D into the 'Deterministic Harness' for agentic orchestration. My recent projects involve designing stateful agent workflows using LangGraph and integrating RAG patterns"
    
    content = content.replace(bad_phrasing, good_phrasing)
    
    # Specific fix for the onXmaps cover letter snippet the user mentioned
    content = content.replace("In my current role as Lead Architect at Symetra, I am building the 'Deterministic Harness' for agentic orchestration. My work involves designing stateful agent workflows using LangGraph and integrating RAG patterns that leverage Vector Databases to provide context-aware intelligence.", 
                              "Parallel to my professional architectural work, I am leading R&D into the 'Deterministic Harness' for agentic orchestration. This involves designing stateful agent workflows using LangGraph and integrating RAG patterns that leverage Vector Databases to provide context-aware intelligence.")

    with open(path, 'w') as f:
        f.write(content)

# Target directories
dirs = ['tmp/prospects', 'tmp/custom']
for d in dirs:
    for root, _, files in os.walk(d):
        for file in files:
            if file.endswith('.txt') or file.endswith('.md'):
                fix_file(os.path.join(root, file))

print("Batch correction of titles and AI phrasing complete.")
