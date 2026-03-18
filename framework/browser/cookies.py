from __future__ import annotations

from playwright.sync_api import Page


def set_onetrust_consent_cookies(page: Page, base_url: str) -> None:
    if not base_url:
        return
    try:
        hostname = base_url.split("//")[-1].split("/")[0]
        parts = hostname.split(".")
        if len(parts) >= 2:
            domain = "." + ".".join(parts[-2:])
        else:
            domain = hostname
        context = page.context
        context.add_cookies(
            [
                {
                    "name": "OptanonConsent",
                    "value": "data=boBLJIDePN7tABBJRG7LEtAAAAyAABAyAEAQAkABgAGAAYABgAGwAcwBzAG8AdwBuAGMALQA1"
                    "ADgANwA3ADkAOAAxADkAMgA0ADkAMgAzADkAMgAwADkAMgA0ADkAMgA0ADkAOAA1ADkANgA0ADkANgA1"
                    "ADkAMQA3ADkAMQA2ADkAMgA1ADkANgA2ADkANgA3ADkANgA3ADkANgA3ADkAOAA2ADkANgA3ADkANgA4"
                    "ADkANgA4ADkANgA5ADkANgA5ADkANgA5ADkAOAA2ADkANgA5ADkAOAA2ADkANgA3ADkANgA4ADkAOAA3"
                    "ADkAOAA4ADkAOAA5ADkAOAA5ADkAOAA5ADkAOAA5ADkAOAA5ADkAOAA5ADkAOAA5ADkA,groups=BO_7"
                    ",ACKN_1,AL_1,TE_1,AE_1,ME_1,CU_1,VA_1,PR_1,UA_1,MEPS_1,PV_1,GE_1,SP_1,EM_1,BF_1,WA_1"
                    ",WG_1,OUBO_1,RG_1,OO_1,GR_1,PL_1,CD_1,CO_1,CRT_1,HR_1,PR_1,VO_1,NL_1,OA_1,P_1,PI_1"
                    ",EV_1,AN_1,AO_1,CI_1,CT_1,C_1,DP_1,D_1,ET_1,F_1,IP_1,J_1,K_1,L_1,M_1,N_1,O_1,P_1"
                    ",PM_1,Q_1,R_1,S_1,SF_1,SI_1,SK_1,T_1,U_1,UR_1,VM_1,VT_1,WA_1",
                    "domain": domain,
                    "path": "/",
                },
                {
                    "name": "OptanonAlertBoxClosed",
                    "value": "2024-01-01T00:00:00.000Z",
                    "domain": domain,
                    "path": "/",
                },
            ]
        )
    except Exception:
        pass
