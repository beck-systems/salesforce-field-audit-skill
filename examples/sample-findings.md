# Contact Object Field Audit

**Org:** Demo Org (synthetic data)  
**Date:** 2026-08-07  
**Custom fields audited:** 25

## Scope

- Record filter: `none — demo dataset`
- In-scope records (all-time): **50,000**
- In-scope records created in the last 365 days: **8,000**
- Population % is computed against these two denominators; the recent figure isolates whether a field is still being written to on new records.

## Summary

**10 of 25 fields (40.0%) are deprecation candidates** (dead, near-dead, or legacy/declining).

| Category | Fields |
|---|---:|
| Dead — 0% populated | 6 |
| Core / actively used | 6 |
| Near-dead — <0.1% populated | 3 |
| Moderate use | 3 |
| Low adoption | 3 |
| Needs manual review (unqueryable type) | 3 |
| Legacy — declining, rarely set on new records | 1 |

## Managed-package culprits

Fields grouped by namespace (`Namespace__Field__c`), ranked by share flagged dead/near-dead/legacy/unqueryable. A namespace where most of its footprint is flagged usually means a decommissioned integration still leaving fields behind.

| Namespace | Fields on object | Flagged | % flagged |
|---|---:|---:|---:|
| `LegacyCRM` | 6 | 6 | 100.0% |

## Field ledger

| Field | API Name | Type | % Populated (all) | % Populated (recent) | Status |
|---|---|---|---:|---:|---|
| Pager Number<br><sub>Legacy contact field from the original 2003 import.</sub> | `Pager_Number__c` | string | 0.00% | 0.00% | Dead — 0% populated |
| Telex Number | `Telex_Number__c` | string | 0.00% | 0.00% | Dead — 0% populated |
| External Id<br><sub>Was used to link records during the 2019 migration.</sub> | `LegacyCRM__External_Id__c` | string | 0.00% | 0.00% | Dead — 0% populated |
| Sync Status | `LegacyCRM__Sync_Status__c` | picklist | 0.00% | 0.00% | Dead — 0% populated |
| Last Sync Date | `LegacyCRM__Last_Sync_Date__c` | datetime | 0.00% | 0.00% | Dead — 0% populated |
| Import Batch | `LegacyCRM__Import_Batch__c` | string | 0.00% | 0.00% | Dead — 0% populated |
| Fax Number | `Fax_Number__c` | string | 0.08% | 0.01% | Near-dead — <0.1% populated |
| Mailing List Sync Error | `Mailing_List_Sync_Error__c` | string | 0.03% | 0.00% | Near-dead — <0.1% populated |
| Legacy Score | `LegacyCRM__Legacy_Score__c` | double | 0.01% | 0.00% | Near-dead — <0.1% populated |
| Twitter Handle<br><sub>Superseded by LinkedIn_URL__c in 2023.</sub> | `Twitter_Handle__c` | string | 42.80% | 1.50% | Legacy — declining, rarely set on new records |
| Account Manager Notes<br><sub>Free-form notes, long text area.</sub> | `Account_Manager_Notes__c` | textarea | — | — | Needs manual review (unqueryable type) |
| Internal Tags | `Internal_Tags__c` | multipicklist | — | — | Needs manual review (unqueryable type) |
| Notes | `LegacyCRM__Notes__c` | textarea | — | — | Needs manual review (unqueryable type) |
| Lead Source Detail<br><sub>Free-text notes from SDR outreach.</sub> | `Lead_Source_Detail__c` | string | 2.40% | 2.25% | Low adoption |
| Referral Source | `Referral_Source__c` | string | 1.22% | 0.15% | Low adoption |
| Slack Connect Channel | `Slack_Connect_Channel__c` | string | 0.18% | 0.05% | Low adoption |
| Preferred Contact Method | `Preferred_Contact_Method__c` | picklist | 19.60% | 18.12% | Moderate use |
| Last Survey Score | `Last_Survey_Score__c` | double | 6.20% | 8.00% | Moderate use |
| Trial Extension Count | `Trial_Extension_Count__c` | double | 4.40% | 5.12% | Moderate use |
| Do Not Call | `Do_Not_Call__c` | boolean | 100.00% | 100.00% | Core / actively used |
| Newsletter Opt-In | `Newsletter_Opt_In__c` | boolean | 100.00% | 100.00% | Core / actively used |
| Onboarding Cohort<br><sub>Set automatically on contact creation.</sub> | `Onboarding_Cohort__c` | string | 100.00% | 100.00% | Core / actively used |
| Timezone | `Timezone__c` | picklist | 88.00% | 95.00% | Core / actively used |
| LinkedIn URL | `LinkedIn_URL__c` | url | 76.40% | 88.75% | Core / actively used |
| SSO Provider | `SSO_Provider__c` | picklist | 24.80% | 48.75% | Core / actively used |
