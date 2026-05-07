import os
import json
import sqlite3
import sys

# Add src to path to import models and repository
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from resumebuddy.infrastructure.adapters.repository import SQLiteJobRepository

def get_file_content(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            return f.read().replace('<', '&lt;').replace('>', '&gt;')
    return ""

repo = SQLiteJobRepository("jobs.db")
prospects_objs = repo.list_jobs()

# Custom weight map for sorting by grade
grade_weights = {
    "Strategic": 100,
    "A+": 95,
    "A": 90,
    "A-": 85,
    "B+": 80,
    "B": 75,
    "B-": 70,
    "C+": 65,
    "C": 60,
    "C-": 55,
    "D": 40,
    "F": 20,
    "?": 0,
    "N/A": 0
}

def get_grade_weight(score):
    return grade_weights.get(score, -1)

prospects_objs.sort(key=lambda x: get_grade_weight(x.score), reverse=True)
prospects = [p.model_dump() for p in prospects_objs]

html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Stephen's Job Dashboard</title>
    <style>
        body { font-family: -apple-system, system-ui, sans-serif; line-height: 1.5; color: #333; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f4f7f6; }
        .section-header { border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-top: 40px; color: #2c3e50; }
        .card { background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 20px; margin-bottom: 20px; transition: all 0.3s ease; display: flex; flex-direction: column; position: relative; min-height: 200px; }
        .card:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0,0,0,0.15); }
        .fit-tag { position: absolute; top: 15px; right: 15px; font-weight: bold; font-size: 1.2em; color: #27ae60; display: flex; flex-direction: column; align-items: flex-end; }
        .fit-tag span { font-size: 0.8em; margin-left: 2px; }
        .tier-tag { font-size: 0.7em; color: #7f8c8d; text-transform: uppercase; letter-spacing: 1px; }
        h1 { color: #2c3e50; text-align: center; }
        h2 { color: #3498db; margin-top: 5px; font-size: 1.1em; flex-grow: 1; padding-right: 40px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; margin-top: 20px; min-height: 50px; }
        .btn { display: inline-block; padding: 6px 10px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 0.85em; margin-top: 10px; text-align: center; cursor: pointer; border: none; }
        .btn-secondary { background: #95a5a6; }
        .details-link { font-size: 0.8em; display: block; margin-bottom: 10px; color: #7f8c8d; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .status-controls { margin-top: 15px; border-top: 1px solid #eee; padding-top: 10px; display: flex; align-items: center; gap: 8px; }
        .status-select { padding: 4px; border-radius: 4px; border: 1px solid #ccc; font-size: 0.8em; cursor: pointer; flex-grow: 1; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.7em; font-weight: bold; text-transform: uppercase; margin-bottom: 10px; width: fit-content; }
        .badge-ready { background: #e1f5fe; color: #0288d1; }
        .badge-applied { background: #e8f5e9; color: #2e7d32; }
        .badge-interview { background: #fff3e0; color: #f57c00; }
        .badge-accepted { background: #f3e5f5; color: #7b1fa2; border: 1px solid #7b1fa2; }
        .badge-rejected { background: #ffebee; color: #c62828; }
        .badge-declined { background: #eceff1; color: #455a64; border: 1px dashed #455a64; }
    </style>
</head>
<body>
    <h1>Stephen's Job Dashboard</h1>
    <h2 class="section-header">Ready to Apply</h2>
    <div id="ready-grid" class="grid"></div>
    <h2 class="section-header">In Progress</h2>
    <div id="progress-grid" class="grid"></div>
    <h2 class="section-header">Closed / Historical</h2>
    <div id="closed-grid" class="grid"></div>
    <script>
        let prospects = JSON_DATA;
        
        async function fetchJobs() {
            try {
                const res = await fetch('http://localhost:8000/jobs');
                if (res.ok) {
                    prospects = await res.json();
                    renderDashboard();
                }
            } catch (e) {
                console.log("Bridge server not available, using embedded data.");
                renderDashboard();
            }
        }

        async function setStatus(id, status) {
            try {
                const res = await fetch(`http://localhost:8000/jobs/${id}/status`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: status })
                });
                if (res.ok) {
                    await fetchJobs();
                }
            } catch (e) {
                alert("Failed to update status on server.");
            }
        }

        function getBadgeClass(status) {
            switch(status) {
                case 'Applied': return 'badge-applied';
                case 'Interview Scheduled': return 'badge-interview';
                case 'Accepted': return 'badge-accepted';
                case 'Rejected': return 'badge-rejected';
                case 'Declined': return 'badge-declined';
                default: return 'badge-ready';
            }
        }

        function renderDashboard() {
            const grids = {'ready': document.getElementById('ready-grid'), 'progress': document.getElementById('progress-grid'), 'closed': document.getElementById('closed-grid')};
            Object.values(grids).forEach(g => g.innerHTML = '');
            prospects.forEach(p => {
                const status = p.status;
                const tierName = p.priority === 1 ? 'Boss Fight' : (p.priority === 2 ? 'Strategic Pivot' : (p.priority === 3 ? 'Stability' : 'Closed'));
                
                // Process signals
                let signalsHtml = '';
                if (p.signals_json) {
                    try {
                        const signals = JSON.parse(p.signals_json);
                        signalsHtml = '<div style="display: flex; gap: 4px; margin-top: 5px; flex-wrap: wrap;">' + 
                            signals.map(s => `<span title="${s.name}: ${s.description}" style="cursor: help; opacity: ${s.is_positive ? '1' : '0.7'}; filter: ${s.is_positive ? 'none' : 'grayscale(0.5)'}">${s.icon}</span>`).join('') + 
                            '</div>';
                    } catch (e) { console.error("Error parsing signals", e); }
                }

                const card = document.createElement('div');
                card.className = 'card';
                
                let companyGradeHtml = '';
                let companySnippetHtml = '';
                if (p.company_grade && p.company_grade !== 'N/A') {
                    companyGradeHtml = `<span class="badge" style="background: #fdf9e1; color: #856404; border: 1px solid #ffeeba; margin-left: 5px;">Co Grade: ${p.company_grade}</span>`;
                }
                
                if (p.company_mission) {
                    companySnippetHtml = `<div style="font-size: 0.8em; color: #666; margin-top: 5px; font-style: italic;">${p.company_mission}</div>`;
                }

                card.innerHTML = `
                    <div class="tier-tag">${tierName}</div>
                    <div class="fit-tag">
                        ${p.score}
                        ${signalsHtml}
                    </div>
                    <div style="display: flex; align-items: center; gap: 5px;">
                        <span class="badge ${getBadgeClass(status)}">${status}</span>
                        ${companyGradeHtml}
                    </div>
                    <a href="details/${p.id}.html" style="text-decoration: none; color: inherit;"><h2>${p.name}</h2></a>
                    ${companySnippetHtml}
                    <a href="${p.url}" target="_blank" class="details-link">${p.url}</a>
                    <div style="display: flex; gap: 5px;">
                        <a href="details/${p.id}.html" class="btn" style="flex: 1;">Kits & Insights</a>
                        <a href="${p.url}" target="_blank" class="btn btn-secondary" style="flex: 1;">Portal</a>
                    </div>
                    <div class="status-controls">
                        <select class="status-select" onchange="setStatus('${p.id}', this.value)">
                            <option value="Ready to Apply" ${status === 'Ready to Apply' ? 'selected' : ''}>Ready to Apply</option>
                            <option value="Applied" ${status === 'Applied' ? 'selected' : ''}>Applied</option>
                            <option value="Interview Scheduled" ${status === 'Interview Scheduled' ? 'selected' : ''}>Interview Scheduled</option>
                            <option value="Accepted" ${status === 'Accepted' ? 'selected' : ''}>Accepted</option>
                            <option value="Rejected" ${status === 'Rejected' ? 'selected' : ''}>Rejected</option>
                            <option value="Declined" ${status === 'Declined' ? 'selected' : ''}>Declined</option>
                        </select>
                    </div>
                `;
                if (status === 'Ready to Apply') grids.ready.appendChild(card);
                else if (status === 'Applied' || status === 'Interview Scheduled') grids.progress.appendChild(card);
                else grids.closed.appendChild(card);
            });
        }
        
        fetchJobs();
    </script>
</body>
</html>
"""

company_mapping = {
    "Roblox": "roblox.md",
    "Exact Sciences": "exact_sciences.md",
    "Abbott": "exact_sciences.md",
    "nvisia": "nvisia.md",
    "Smartsheet": "smartsheet.md",
    "Wellington": "wellington_management.md",
    "Global Investment": "wellington_management.md",
    "Figma": "figma.md",
    "Webflow": "webflow.md",
    "Parspec": "parspec.md",
    "AI Search": "parspec.md",
    "Netflix": "netflix.md",
    "GitHub": "github.md",
    "Coinbase": "coinbase.md",
    "Zillow": "zillow.md",
    "Proxify": "proxify.md",
    "Cresta": "cresta.md",
    "Immuta": "immuta.md",
    "Together AI": "together_ai.md",
    "Wolters Kluwer": "wolters_kluwer.md",
    "INDUSVALLEY": "indusvalley.md",
    "Shipt": "shipt.md",
    "EngagedMD": "engagedmd.md",
    "Lemon.io": "lemon_io.md",
    "FranklinCovey": "franklincovey.md",
    "YO HR": "working_nomads.md",
    "Working Nomads": "working_nomads.md",
    "Archetype AI": "archetype_ai.md",
    "onXmaps": "onxmaps.md",
    "SpotOn": "spoton.md",
    "Mozilla": "mozilla.md",
    "AllSpice": "allspice.md",
    "Summit": "summit.md",
    "CCAP": "ccap.md",
    "Kinimatic": "kinimatic.md",
    "Walmart": "walmart.md",
    "Nxt Level": "nxt_level.md",
    "Yahoo": "yahoo.md",
    "Plaid": "plaid.md",
    "Oak Tree": "oak_tree_software.md",
    "Nuclearn": "nuclearn.md",
    "Eleventh Hour": "eleventh_hour_games.md",
    "FreeWill": "freewill.md",
    "Manifest": "manifest.md",
    "Insight Global": "insight_global.md",
    "Ladders": "ladders.md",
    "Plura": "plura.md",
    "Paramount": "paramount.md",
    "OpenAI": "openai.md",
    "Grafana Labs": "grafana_labs.md",
    "Planet DDS": "planet_dds.md"
}

def _load_intel(filename):
    path = os.path.join("knowledge-base", "companies", filename)
    if os.path.exists(path):
        with open(path, 'r') as f:
            content = f.read()
            # Extract grade
            grade = "N/A"
            for line in content.split('\n'):
                if "Maturity Grade:" in line or "Grade:" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        grade = parts[1].strip().split(' ')[0]
            return content, grade, filename
    return None, None, None

def get_company_intel(job_name):
    # Try exact match first
    for key, filename in company_mapping.items():
        if key.lower() == job_name.lower():
            return _load_intel(filename)
    
    # Try fuzzy match
    for key, filename in company_mapping.items():
        if key.lower() in job_name.lower():
            return _load_intel(filename)
    return None, None, None

# Generation logic for detail pages
for p in prospects:
    details_path = os.path.join(p['dir'], "details.md")
    resume_path = os.path.join(p['dir'], "resume.txt")
    if not os.path.exists(resume_path): resume_path = "resume.txt"
    cl_path = os.path.join(p['dir'], "cover_letter.txt")
    
    # Primary Source: Files (to allow manual editing to sync to DB)
    details = get_file_content(details_path) or p.get('details_content') or ""
    resume = get_file_content(resume_path) or p.get('resume_content') or ""
    cl = get_file_content(cl_path) or p.get('cover_letter_content') or ""

    intel_content, intel_grade, intel_file = get_company_intel(p['name'])
    p['company_grade'] = intel_grade
    
    # Extract a mission snippet for the main card
    if intel_content:
        mission_section = ""
        lines = intel_content.split('\n')
        for i, line in enumerate(lines):
            if "## 1. The Mission" in line or "## Mission" in line:
                if i + 1 < len(lines): mission_section = lines[i+1].strip()
                break
        p['company_mission'] = mission_section[:150] + "..." if len(mission_section) > 150 else mission_section

    # Sync back to DB if DB is missing content but files have it
    if details or resume or cl:
        repo.update_content(p['id'], resume=resume, cv=cl, details=details)
    
    intel_html = ""
    if intel_content:
        intel_html = f"""
        <div class="card" style="border-left: 5px solid #f1c40f; background: #fffdf0;">
            <h2>Company Intel: {intel_file} (Grade: {intel_grade})</h2>
            <div style="white-space: pre-wrap; font-family: -apple-system, system-ui, sans-serif; font-size: 0.95em;">{intel_content}</div>
        </div>
        """

    detail_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{p['name']} - Career Kit</title>
    <style>
        body {{ font-family: -apple-system, system-ui, sans-serif; line-height: 1.5; color: #333; max-width: 1000px; margin: 0 auto; padding: 20px; background: #f4f7f6; }}
        .nav {{ margin-bottom: 20px; }}
        .card {{ background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 30px; margin-bottom: 30px; position: relative; }}
        pre {{ background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; white-space: pre-wrap; font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace; font-size: 0.9em; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-top: 30px; color: #2c3e50; }}
        .btn {{ display: inline-block; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; margin-right: 10px; cursor: pointer; border: none; }}
        .copy-btn {{ position: absolute; top: 10px; right: 10px; padding: 5px 10px; background: #eee; border: 1px solid #ccc; border-radius: 4px; cursor: pointer; font-size: 0.8em; }}
        #chat-widget {{ position: fixed; bottom: 20px; right: 20px; width: 350px; height: 500px; background: white; border-radius: 10px; box-shadow: 0 5px 25px rgba(0,0,0,0.2); display: flex; flex-direction: column; overflow: hidden; }}
        #chat-header {{ background: #3498db; color: white; padding: 15px; font-weight: bold; display: flex; justify-content: space-between; }}
        #chat-history {{ flex-grow: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 10px; background: #fdfdfd; }}
        #chat-input-area {{ padding: 15px; border-top: 1px solid #eee; display: flex; gap: 10px; }}
        #chat-input {{ flex-grow: 1; padding: 8px; border: 1px solid #ddd; border-radius: 5px; }}
        .msg-user {{ align-self: flex-end; background: #3498db; color: white; padding: 8px 12px; border-radius: 15px 15px 0 15px; max-width: 80%; font-size: 0.9em; }}
        .msg-ai {{ align-self: flex-start; background: #f1f0f0; color: #333; padding: 8px 12px; border-radius: 15px 15px 15px 0; max-width: 80%; font-size: 0.9em; }}
        .action-bar {{ margin-bottom: 20px; display: flex; gap: 10px; }}
    </style>
</head>
<body>
    <div class="nav">
        <a href="../index.html" class="btn">← Back to Dashboard</a>
        <a href="{p['url']}" target="_blank" class="btn btn-secondary">External Portal ↗</a>
    </div>
    {intel_html}
    <div class="card">
        <h1>{p['name']}</h1>
        <div class="action-bar">
            <button id="council-btn" onclick="invokeCouncil()" class="btn" style="background: #8e44ad;">Invoke LLM Council</button>
            <button onclick="triggerAction('cover_letter')" class="btn" style="background: #27ae60;">Regen Cover Letter</button>
            <button onclick="triggerAction('docx_resume')" class="btn" style="background: #e67e22;">Gen DOCX Resume</button>
            <button onclick="triggerAction('docx_cv')" class="btn" style="background: #e74c3c;">Gen DOCX CV</button>
        </div>
        <div id="insight-content"></div>
        <h2>Strategic Narrative (details.md)</h2>
        <pre id="details-text">{details}</pre>
        <h2>Tailored Resume</h2>
        <div style="position: relative;"><button class="copy-btn" onclick="copyToClipboard('resume-text')">Copy</button><pre id="resume-text">{resume}</pre></div>
        <h2>Cover Letter</h2>
        <div style="position: relative;"><button class="copy-btn" onclick="copyToClipboard('cl-text')">Copy</button><pre id="cl-text">{cl}</pre></div>
    </div>
    <div id="chat-widget">
        <div id="chat-header"><span>Live Bridge: Ask Gemini</span><span style="cursor: pointer;" onclick="document.getElementById('chat-history').innerHTML=''">Clear</span></div>
        <div id="chat-history"><div class="msg-ai">Ask me anything about the {p['name']} role.</div></div>
        <div id="chat-input-area"><input type="text" id="chat-input" placeholder="Ask a question..." onkeypress="if(event.key==='Enter') sendMessage()"><button onclick="sendMessage()" class="btn">Send</button></div>
    </div>
    <script>
        function simpleMarkdown(text) {{
            return text
                .replace(/### (.*?)\\n/g, '<div style="font-weight:bold; margin-top:10px; color:#2c3e50;">$1</div>')
                .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
                .replace(/\\*(.*?)\\*/g, '<em>$1</em>')
                .replace(/^- (.*?)$/gm, '<li style="margin-left:15px;">$1</li>')
                .replace(/\\n/g, '<br>');
        }}
        async function sendMessage() {{
            const input = document.getElementById('chat-input');
            const history = document.getElementById('chat-history');
            const val = input.value; if(!val) return;
            history.innerHTML += '<div class="msg-user">' + val + '</div>';
            input.value = '';
            const context = "JOB: " + document.querySelector('h1').innerText + "\\n" +
                          "STRATEGY: " + document.getElementById('details-text').innerText + "\\n" +
                          "RESUME: " + document.getElementById('resume-text').innerText.substring(0, 1000);
            try {{
                const res = await fetch('http://localhost:8000/chat', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ prompt: val, context: context }})
                }});
                const data = await res.json();
                history.innerHTML += '<div class="msg-ai">' + simpleMarkdown(data.response) + '</div>';
                history.scrollTop = history.scrollHeight;
            }} catch(e) {{ history.innerHTML += '<div class="msg-ai" style="color: red;">Bridge server error.</div>'; }}
        }}
        async function invokeCouncil() {{
            const btn = document.getElementById('council-btn');
            const content = document.getElementById('insight-content');
            btn.innerText = 'Consulting advisors...';
            try {{
                const res = await fetch('http://localhost:8000/council', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ job_id: "{p['id']}", dir_path: "{p['dir']}" }})
                }});
                const data = await res.json();
                content.innerHTML = simpleMarkdown(data.verdict);
                btn.innerText = 'Verdict Ready';
            }} catch(e) {{ alert('Bridge error.'); }}
        }}
        async function triggerAction(action) {{
            if(!confirm('Trigger action?')) return;
            let content = null;
            if (action === 'docx_resume') content = document.getElementById('resume-text').innerText;
            if (action === 'docx_cv') content = document.getElementById('cl-text').innerText;

            try {{
                const res = await fetch('http://localhost:8000/action', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ 
                        action: action, 
                        job_id: "{p['id']}", 
                        dir_path: "{p['dir']}",
                        content: content
                    }})
                }});
                const data = await res.json();
                if (data.error) {{
                    alert('Error: ' + data.error);
                }} else {{
                    alert(data.response || 'Success');
                    if (action === 'cover_letter') location.reload();
                }}
            }} catch(e) {{ alert('Bridge error: ' + e); }}
        }}
        function copyToClipboard(id) {{
            const text = document.getElementById(id).innerText;
            navigator.clipboard.writeText(text).then(() => alert('Copied!'));
        }}
    </script>
</body>
</html>
"""
    os.makedirs("tmp/dashboard/details", exist_ok=True)
    with open(f"tmp/dashboard/details/{p['id']}.html", 'w') as f:
        f.write(detail_html)

with open("tmp/dashboard/index.html", 'w') as f:
    f.write(html_template.replace('JSON_DATA', json.dumps(prospects)))

print("Dashboard updated from SQLite.")
