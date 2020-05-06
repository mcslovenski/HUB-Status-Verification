HUB_status_verification.exe is an executable file that
- converts pdf files to text
- extracts listed subcontractors and the information provided about them
- searches the CMBL for listed subcontractors and extracts result information
- compares listed information with found online information
- produces a logfile for each listed subcontractor

HUB_status_versification.exe is run like any other executable program, most commonly by double-clicking it.
On running HUB_status_verification.exe, user will be prompted to select files for processing.
One or more files may be selected; to select multiple non-adjacent files, hold control while selecting.

HUB_status_verification.exe produces three subdirectories in the directory where it is run:
- agreement
- disagreement
- notFound

HUB_status_verification.exe produces plaintext logfiles for each subcontractor and places them in one of the above directories based on the result of information comparison.
Logfiles formats are outlined at the end of this readme.

Results of HUB_status_verification.exe's processing should be verified periodically and if particularly important.

In addition to not locating vendors on the CMBL, HUB_status_verification is likely to produce false positives and false negatives at a rate greater than 0 due to the nature of text search.



Logfile formats:

IF NO VENDORS WERE FOUND IN CMBL SEARCH:
"""
vendor name on subcontracting plan:
    {subcontractor['name']}
vendor ID or EIN on subcontracting plan:
    {subcontractor['VID/EIN']}
HUB status on subcontracting plan:
    {subcontractor['hub_status']}

vendor not found in CMBL search
{timestamp as YYYY-MM-DD--HH-MM-SS}
"""

IF LISTED VENDOR HUB STATUS AND CMBL HUB VENDOR STATUS DISAGREE:
"""
vendor name on subcontracting plan:
    {subcontractor['name']}
vendor name from CMBL search:
    {cmbl_vendor['name']}
vendor ID or EIN on subcontracting plan:
    {subcontractor['VID/EIN']}
vendor ID from CMBL:
    {cmbl_vendor['VID']}
HUB status on subcontracting plan:
    {subcontractor['hub_status']}
HUB status from CMBL:
    {cmbl_vendor['hub_status_code']}

HUB status DISAGREEMENT
{timestamp as YYYY-MM-DD--HH-MM-SS}
"""

IF LISTED VENDOR HUB STATUS AND CMBL VENDOR HUB STATUS AGREE:
"""
vendor name on subcontracting plan:
    {subcontractor['name']}
vendor name from CMBL search:
    {cmbl_vendor['name']}
vendor ID or EIN on subcontracting plan:
    {subcontractor['VID/EIN']}
vendor ID from CMBL:
    {cmbl_vendor['VID']}
HUB status on subcontracting plan:
    {subcontractor['hub_status']}
HUB status from CMBL:
    {cmbl_vendor['hub_status_code']}

logfile.write("HUB status AGREEMENT
{timestamp as YYYY-MM-DD--HH-MM-SS}
"""