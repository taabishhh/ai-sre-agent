from agent.config import SETTINGS


def ask_for_approval(diagnosis, proposal):
    if SETTINGS.auto_approve:
        print("\n[AUTO_APPROVE is on, skipping the approval step. Don't use this in production.]\n")
        return "auto_approved", "auto-approved via AUTO_APPROVE"

    print("\n" + "=" * 72)
    print("HUMAN APPROVAL REQUIRED")
    print("=" * 72)
    print(f"\nRoot cause ({diagnosis['confidence']} confidence):\n  {diagnosis['root_cause']}\n")
    print("Evidence:")
    for item in diagnosis["evidence"]:
        print(f"  - {item}")
    print(f"\nProposed action: {proposal['action']}")
    print(f"  Params:           {proposal['params']}")
    print(f"  Rationale:        {proposal['rationale']}")
    print(f"  Risk level:       {proposal['risk_level']}")
    print(f"  Expected outcome: {proposal['expected_outcome']}")
    print("-" * 72)

    if proposal["action"] == "no_action":
        print("Nothing to approve, the agent suggested no action.")
        return "denied", "no action proposed"

    while True:
        answer = input("Apply this fix? [y/N]: ").strip().lower()
        if answer in ("y", "yes"):
            return "approved", input("Optional note (enter to skip): ").strip()
        if answer in ("", "n", "no"):
            return "denied", input("Reason for denying (enter to skip): ").strip()
        print("Please answer y or n.")
