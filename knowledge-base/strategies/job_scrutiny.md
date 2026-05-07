# Job Scrutiny & Vetting Protocol

This document defines the process for ensuring job leads are fresh, legitimate, and correctly represented.

## 1. The Freshness Check
*   **LinkedIn 'Reposted' Trap:** If a job was reposted "1 week ago," always check the **Original Post Date** if visible. Reposting often happens when a search is stalling or a previous candidate failed the background check.
*   **The 3-Week Rule:** Any role older than 3 weeks (without a clear "Hiring Now" signal) is high-risk for link decay or stale pipeline.

## 2. Career Page Verification (MANDATORY)
Never rely on aggregators (LinkedIn, Indeed). Always find the **Official Career Portal**.
*   **Mozilla:** [mozilla.org/en-US/careers/](https://www.mozilla.org/en-US/careers/)
*   **Exact Sciences:** [exactsciences.com/about/careers/](https://www.exactsciences.com/about/careers/)
*   **Abbott:** [abbott.com/careers.html](https://www.abbott.com/careers.html)
*   **Webflow:** [webflow.com/careers](https://webflow.com/careers)
*   **SpotOn:** [spoton.com/about/careers/](https://www.spoton.com/about/careers/)

### Vetting Steps:
1.  **Extract the Req ID:** If possible, find the unique ID (e.g., R3080).
2.  **Search the Portal:** Enter the Req ID directly into the company portal.
3.  **Cross-Reference Titles:** If the title on LinkedIn is "Staff Backend Engineer" but the portal says "Senior Software Engineer," the LinkedIn title may be an "Internal Level" that isn't publicly facing.

## 3. Accessibility Map
*   **Workday:** (Exact Sciences, Abbott, NVIDIA) - Generally requires a manual portal account. Scraping is difficult.
*   **Greenhouse:** (Webflow, Mozilla) - Static HTML; high-fidelity scraping possible.
*   **Lever:** (Many startups) - Clean JSON API endpoints often available.
